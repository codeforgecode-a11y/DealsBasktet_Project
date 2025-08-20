#!/usr/bin/env bash
# Database migration script for Render deployment

set -o errexit  # exit on error

echo "🗄️ Starting database migration process..."

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
python << EOF
import os
import time
import psycopg2
from urllib.parse import urlparse

def wait_for_db():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("DATABASE_URL not found, skipping database wait")
        return
    
    parsed = urlparse(database_url)
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path[1:]  # Remove leading slash
            )
            conn.close()
            print("✅ Database is ready!")
            return
        except psycopg2.OperationalError:
            retry_count += 1
            print(f"Database not ready, retrying... ({retry_count}/{max_retries})")
            time.sleep(2)
    
    raise Exception("Database did not become ready in time")

wait_for_db()
EOF

# Run database migrations
echo "🔄 Running database migrations..."
python manage.py migrate --noinput

# Create initial data if needed
echo "📊 Creating initial data..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
from apps.products.models import Category
from apps.shop.models import Shop
import os

User = get_user_model()

# Create default categories if they don't exist
default_categories = [
    'Electronics',
    'Clothing',
    'Home & Garden',
    'Sports & Outdoors',
    'Books',
    'Health & Beauty',
    'Food & Beverages',
    'Toys & Games'
]

for category_name in default_categories:
    category, created = Category.objects.get_or_create(
        name=category_name,
        defaults={'description': f'{category_name} products'}
    )
    if created:
        print(f"Created category: {category_name}")

print("✅ Initial data setup completed!")
EOF

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

echo "✅ Migration process completed successfully!"
