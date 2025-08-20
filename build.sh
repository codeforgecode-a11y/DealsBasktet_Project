#!/usr/bin/env bash
# Build script for Render deployment

set -o errexit  # exit on error

echo "🚀 Starting DealsBasket build process..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Run database migrations
echo "🗄️ Running database migrations..."
python manage.py migrate

# Create superuser if it doesn't exist
echo "👤 Creating superuser if needed..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
from decouple import config

User = get_user_model()

# Check if superuser exists
if not User.objects.filter(is_superuser=True).exists():
    # Create superuser from .env file
    username = config('DJANGO_SUPERUSER_USERNAME', default='admin')
    email = config('DJANGO_SUPERUSER_EMAIL', default='admin@dealsbasket.com')
    password = config('DJANGO_SUPERUSER_PASSWORD', default='admin123')

    User.objects.create_superuser(
        username=username,
        email=email,
        password=password
    )
    print(f"Superuser '{username}' created successfully!")
else:
    print("Superuser already exists.")
EOF

# Run Django system checks
echo "🔍 Running Django system checks..."
python manage.py check --deploy

echo "✅ Build completed successfully!"
