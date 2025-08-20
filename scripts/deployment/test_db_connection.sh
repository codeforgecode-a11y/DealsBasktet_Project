#!/bin/bash

# Load environment variables
set -a
# Load environment variables from .env file
if [ -f .env ]; then
    source .env
else
    echo "❌ .env file not found. Please create .env file with required variables."
    exit 1
fi
set +a

echo "Testing connection to PostgreSQL database..."
echo "Host: $DB_HOST"
echo "Database: $DB_NAME"
echo "User: $DB_USER"

# Test database connection using psql
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "\conninfo" || {
    echo "Failed to connect to database"
    exit 1
}