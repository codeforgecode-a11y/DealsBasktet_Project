#!/bin/bash

# Exit on error
set -e

# Load environment variables
source .env.production

# Set backup directory
BACKUP_DIR="backups/$(date +%Y%m%d)"
S3_BACKUP_BUCKET="dealsbasket-backups"

echo "🔄 Starting backup process..."
echo "============================"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
echo "📌 Backing up database..."
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > $BACKUP_DIR/database.sql

# Backup media files
echo "📌 Backing up media files..."
aws s3 sync s3://$AWS_STORAGE_BUCKET_NAME/media $BACKUP_DIR/media

# Create backup archive
echo "📌 Creating backup archive..."
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR

# Upload to S3
echo "📌 Uploading backup to S3..."
aws s3 cp $BACKUP_DIR.tar.gz s3://$S3_BACKUP_BUCKET/

# Cleanup old backups (keep last 7 days)
echo "📌 Cleaning up old backups..."
find backups/* -mtime +7 -exec rm {} \;

# Clean up local backup files
rm -rf $BACKUP_DIR
rm -f $BACKUP_DIR.tar.gz

echo "============================"
echo "✅ Backup completed successfully!"
echo "📦 Backup stored in s3://$S3_BACKUP_BUCKET/$BACKUP_DIR.tar.gz"