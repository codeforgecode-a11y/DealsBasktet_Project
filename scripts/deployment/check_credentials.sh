#!/bin/bash

# Exit on error
set -e

# Function to check AWS credentials
check_aws_credentials() {
    echo "Checking AWS credentials..."
    if aws sts get-caller-identity &>/dev/null; then
        echo "✅ AWS credentials are valid"
        return 0
    else
        echo "❌ AWS credentials are invalid"
        return 1
    fi
}

# Function to check Cloudinary credentials
check_cloudinary_credentials() {
    echo "Checking Cloudinary credentials..."
    python3 - <<EOF
import cloudinary
import cloudinary.uploader
import os

cloudinary.config(
    cloud_name="${CLOUDINARY_CLOUD_NAME}",
    api_key="${CLOUDINARY_API_KEY}",
    api_secret="${CLOUDINARY_API_SECRET}"
)

try:
    # Try to upload a test image
    response = cloudinary.uploader.upload("test.jpg")
    print("✅ Cloudinary credentials are valid")
except Exception as e:
    print("❌ Cloudinary credentials are invalid:", str(e))
    exit(1)
EOF
}

# Function to check database connection
check_database_connection() {
    echo "Checking database connection..."
    python3 - <<EOF
import psycopg2
import os

try:
    conn = psycopg2.connect(
        dbname="${DB_NAME}",
        user="${DB_USER}",
        password="${DB_PASSWORD}",
        host="${DB_HOST}",
        port="${DB_PORT}"
    )
    print("✅ Database connection successful")
    conn.close()
except Exception as e:
    print("❌ Database connection failed:", str(e))
    exit(1)
EOF
}

# Function to check Redis connection
check_redis_connection() {
    echo "Checking Redis connection..."
    python3 - <<EOF
import redis
import os

try:
    r = redis.from_url("${REDIS_URL}")
    r.ping()
    print("✅ Redis connection successful")
except Exception as e:
    print("❌ Redis connection failed:", str(e))
    exit(1)
EOF
}

# Function to check email configuration
check_email_configuration() {
    echo "Checking email configuration..."
    python3 - <<EOF
import smtplib
import os

try:
    server = smtplib.SMTP("${EMAIL_HOST}", ${EMAIL_PORT})
    server.starttls()
    server.login("${EMAIL_HOST_USER}", "${EMAIL_HOST_PASSWORD}")
    print("✅ Email configuration is valid")
    server.quit()
except Exception as e:
    print("❌ Email configuration is invalid:", str(e))
    exit(1)
EOF
}

# Load environment variables
if [ -f .env.production ]; then
    export $(cat .env.production | grep -v '^#' | xargs)
else
    echo "❌ .env.production file not found"
    exit 1
fi

# Run all checks
echo "Starting credential and connection checks..."
echo "----------------------------------------"

check_aws_credentials
check_cloudinary_credentials
check_database_connection
check_redis_connection
check_email_configuration

echo "----------------------------------------"
echo "✅ All checks completed successfully!"