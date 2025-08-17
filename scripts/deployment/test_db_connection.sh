#!/bin/bash

# Load environment variables
set -a
source config/database/.env.production
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