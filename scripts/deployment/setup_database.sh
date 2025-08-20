#!/bin/bash

# Database Setup Script for DealsBasket
# This script sets up the PostgreSQL database with proper configuration

set -e

echo "🗄️  Setting up DealsBasket database..."

# Load environment variables
# Load environment variables from .env file
if [ -f .env ]; then
    source .env
else
    echo "❌ .env file not found. Please create .env file with required variables."
    exit 1
fi

# Check if required variables are set
required_vars=("DB_HOST" "DB_NAME" "DB_USER" "DB_PASSWORD")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Required environment variable $var is not set!"
        exit 1
    fi
done

echo "📍 Database Host: $DB_HOST"
echo "📍 Database Name: $DB_NAME"
echo "📍 Database User: $DB_USER"

# Function to run SQL commands
run_sql() {
    local sql="$1"
    echo "🔧 Executing: $sql"
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "$sql"
}

# Function to check database connection
check_connection() {
    echo "🔍 Testing database connection..."
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "SELECT version();" > /dev/null 2>&1; then
        echo "✅ Database connection successful"
        return 0
    else
        echo "❌ Database connection failed"
        return 1
    fi
}

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if check_connection; then
        break
    fi
    
    echo "⏳ Attempt $attempt/$max_attempts failed. Waiting 10 seconds..."
    sleep 10
    attempt=$((attempt + 1))
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ Database connection failed after $max_attempts attempts"
    exit 1
fi

# Create extensions
echo "🔧 Creating database extensions..."
run_sql "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;"
run_sql "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
run_sql "CREATE EXTENSION IF NOT EXISTS btree_gin;"
run_sql "CREATE EXTENSION IF NOT EXISTS uuid-ossp;"

# Set up database configuration
echo "🔧 Configuring database settings..."
run_sql "ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';"
run_sql "ALTER SYSTEM SET log_min_duration_statement = 1000;"
run_sql "ALTER SYSTEM SET log_connections = on;"
run_sql "ALTER SYSTEM SET log_disconnections = on;"
run_sql "ALTER SYSTEM SET log_lock_waits = on;"
run_sql "ALTER SYSTEM SET checkpoint_completion_target = 0.9;"

# Create read-only user for monitoring
echo "🔧 Creating monitoring user..."
MONITORING_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
run_sql "CREATE USER dealsbasket_monitor WITH PASSWORD '$MONITORING_PASSWORD';"
run_sql "GRANT CONNECT ON DATABASE $DB_NAME TO dealsbasket_monitor;"
run_sql "GRANT USAGE ON SCHEMA public TO dealsbasket_monitor;"
run_sql "GRANT SELECT ON ALL TABLES IN SCHEMA public TO dealsbasket_monitor;"
run_sql "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO dealsbasket_monitor;"

# Store monitoring password in Parameter Store
if command -v aws &> /dev/null; then
    echo "🔐 Storing monitoring password in Parameter Store..."
    aws ssm put-parameter \
        --name "/dealsbasket/db_monitor_password" \
        --value "$MONITORING_PASSWORD" \
        --type "SecureString" \
        --description "Database monitoring user password" \
        --overwrite \
        --region "${AWS_DEFAULT_REGION:-ap-south-1}"
fi

# Run Django migrations
echo "🔄 Running Django migrations..."
export DJANGO_SETTINGS_MODULE=server.settings.production

# Check if Django is available
if command -v python3 &> /dev/null && python3 -c "import django" &> /dev/null; then
    echo "🔄 Running makemigrations..."
    python3 manage.py makemigrations --noinput
    
    echo "🔄 Running migrate..."
    python3 manage.py migrate --noinput
    
    echo "🔄 Collecting static files..."
    python3 manage.py collectstatic --noinput
    
    # Create superuser if it doesn't exist
    echo "👤 Creating superuser..."
    python3 manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@dealsbasket.com', 'admin123')
    print('Superuser created successfully')
else:
    print('Superuser already exists')
"
else
    echo "⚠️  Django not available. Skipping migrations."
fi

# Database performance tuning
echo "🚀 Applying performance optimizations..."
run_sql "ANALYZE;"
run_sql "VACUUM ANALYZE;"

# Create indexes for better performance
echo "📊 Creating performance indexes..."
run_sql "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users_user(email);"
run_sql "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_category ON products_product(category);"
run_sql "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_status ON orders_order(status);"
run_sql "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_created_at ON orders_order(created_at);"

echo "✅ Database setup completed successfully!"
echo ""
echo "📋 Summary:"
echo "  - Database extensions created"
echo "  - Performance settings configured"
echo "  - Monitoring user created"
echo "  - Django migrations applied"
echo "  - Performance indexes created"
echo ""
echo "🔗 Next steps:"
echo "  1. Monitor database performance using CloudWatch"
echo "  2. Set up automated backups"
echo "  3. Configure connection pooling in application"
echo ""
echo "📊 Database info:"
echo "  - Host: $DB_HOST"
echo "  - Database: $DB_NAME"
echo "  - Main user: $DB_USER"
echo "  - Monitor user: dealsbasket_monitor"
