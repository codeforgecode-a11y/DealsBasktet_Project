#!/usr/bin/env bash
# Production start script for local testing

set -e

echo "🚀 Starting DealsBasket in production mode..."

# Activate virtual environment
source .venv/bin/activate

# Set production environment
export DJANGO_SETTINGS_MODULE=server.settings.production
export DEBUG=False

# Create logs directory if it doesn't exist
mkdir -p logs

# Load environment variables from .env file
if [ -f .env ]; then
    echo "📄 Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
else
    echo "⚠️  .env file not found, using defaults"
fi

# Check if required environment variables are set
if [ -z "$SECRET_KEY" ]; then
    echo "⚠️  SECRET_KEY not set, using default (not secure for production)"
    export SECRET_KEY="django-insecure-production-test-key"
fi

if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  DATABASE_URL not set, using SQLite for local testing"
    export DATABASE_URL="sqlite:///./db.sqlite3"
fi

# Set Django settings module based on environment
if [ -z "$DJANGO_SETTINGS_MODULE" ]; then
    export DJANGO_SETTINGS_MODULE="server.settings.production"
fi

# Run migrations
echo "🗄️ Running migrations..."
python manage.py migrate

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if needed
echo "👤 Creating superuser if needed..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
from decouple import config
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    username = config('DJANGO_SUPERUSER_USERNAME', default='admin')
    email = config('DJANGO_SUPERUSER_EMAIL', default='admin@dealsbasket.com')
    password = config('DJANGO_SUPERUSER_PASSWORD', default='admin123')
    User.objects.create_superuser(username, email, password)
    print(f'Superuser created: {username}')
else:
    print('Superuser already exists')
"

# Start Gunicorn
echo "🌟 Starting Gunicorn server..."
echo "📍 Server will be available at: http://localhost:8000"
echo "📍 Admin panel: http://localhost:8000/admin/"
echo "📍 API documentation: http://localhost:8000/api/schema/swagger-ui/"
echo "📍 Health check: http://localhost:8000/health/"

gunicorn --config gunicorn.conf.py server.wsgi:application
