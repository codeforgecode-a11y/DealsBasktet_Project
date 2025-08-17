#!/bin/bash

# Database configuration
DB_HOST="dealsbasket.chi4u4q4kiid.ap-south-1.rds.amazonaws.com"
DB_PORT="5432"
DB_NAME="dealsbasket"
DB_USER="backup_user"
DB_PASSWORD="DealsBackup@123"

# Backup directory
BACKUP_DIR="/media/durgesh/Development/DealsBasket_Project/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/dealsbasket_backup_$DATE.sql"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Perform backup
echo "Starting database backup..."
export PGPASSWORD=$DB_PASSWORD
pg_dump -v \
    --clean \
    --if-exists \
    --no-owner \
    --no-acl \
    -h $DB_HOST \
    -p $DB_PORT \
    -U $DB_USER \
    -d $DB_NAME \
    -Fp \
    -f "$BACKUP_FILE"

# Check if backup was successful
if [ $? -eq 0 ]; then
    echo "Backup completed successfully: $BACKUP_FILE"
    
    # Compress backup
    gzip "$BACKUP_FILE"
    echo "Backup compressed: $BACKUP_FILE.gz"
    
    # Clean up old backups (keep last 7 days)
    find "$BACKUP_DIR" -name "*.gz" -mtime +7 -delete
else
    echo "Backup failed!"
    exit 1
fi