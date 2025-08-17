#!/bin/bash

# Exit on error
set -e

echo "🔍 Running Pre-deployment Checks..."
echo "===================================="

# Check Python version
echo "📌 Checking Python version..."
python_version=$(python3 --version)
if [[ $python_version == *"3.12"* ]]; then
    echo "✅ Python version is correct: $python_version"
else
    echo "❌ Wrong Python version. Expected 3.12.x, got: $python_version"
    exit 1
fi

# Check if all required files exist
echo "📌 Checking required files..."
required_files=(
    "manage.py"
    "requirements.txt"
    "Dockerfile"
    "docker-compose.yml"
    "nginx.conf"
    ".env.production"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ Found $file"
    else
        echo "❌ Missing required file: $file"
        exit 1
    fi
done

# Check if virtual environment is active
echo "📌 Checking virtual environment..."
if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ Virtual environment is not active"
    exit 1
else
    echo "✅ Virtual environment is active: $VIRTUAL_ENV"
fi

# Install dependencies
echo "📌 Installing/Updating dependencies..."
pip install -r requirements.txt

# Run migrations check
echo "📌 Checking for pending migrations..."
python manage.py makemigrations --check --dry-run
if [ $? -eq 0 ]; then
    echo "✅ No pending migrations"
else
    echo "❌ You have pending migrations. Please run migrations first"
    exit 1
fi

# Run tests
echo "📌 Running tests..."
python manage.py test
if [ $? -eq 0 ]; then
    echo "✅ All tests passed"
else
    echo "❌ Tests failed"
    exit 1
fi

# Collect static files
echo "📌 Collecting static files..."
python manage.py collectstatic --noinput

# Check database connection
echo "📌 Checking database connection..."
python manage.py check --database default

# Check for security issues
echo "📌 Running security checks..."
python manage.py check --deploy

# Check if AWS credentials are valid
echo "📌 Checking AWS credentials..."
aws sts get-caller-identity > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ AWS credentials are valid"
else
    echo "❌ AWS credentials are invalid"
    exit 1
fi

# Build Docker image
echo "📌 Building Docker image..."
docker build -t dealsbasket:latest .

echo "===================================="
echo "✅ All pre-deployment checks passed!"
echo "You can now proceed with deployment"