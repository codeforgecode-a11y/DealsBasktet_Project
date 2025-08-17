#!/bin/bash

# AWS RDS Instance Identifier
DB_INSTANCE="dealsbasket-db"
DATE=$(date +%Y%m%d-%H%M%S)
SNAPSHOT_IDENTIFIER="dealsbasket-backup-$DATE"

# Function to check if instance is available
check_instance_status() {
    STATUS=$(aws rds describe-db-instances \
        --db-instance-identifier $DB_INSTANCE \
        --query 'DBInstances[0].DBInstanceStatus' \
        --output text)
    echo $STATUS
}

# Wait for instance to be available
echo "Checking instance status..."
while true; do
    STATUS=$(check_instance_status)
    if [ "$STATUS" = "available" ]; then
        break
    fi
    echo "Instance status is $STATUS, waiting 30 seconds..."
    sleep 30
done

# Take RDS snapshot
echo "Starting RDS snapshot creation..."
SNAPSHOT_RESULT=$(aws rds create-db-snapshot \
    --db-instance-identifier $DB_INSTANCE \
    --db-snapshot-identifier $SNAPSHOT_IDENTIFIER \
    --output json | cat)

# Check if snapshot creation was initiated successfully
if [ $? -eq 0 ]; then
    echo "Snapshot creation initiated successfully: $SNAPSHOT_IDENTIFIER"
    
    # Wait for the snapshot to complete
    echo "Waiting for snapshot to complete..."
    aws rds wait db-snapshot-available \
        --db-snapshot-identifier $SNAPSHOT_IDENTIFIER
    
    if [ $? -eq 0 ]; then
        echo "Snapshot completed successfully!"
        
        # Clean up old snapshots (keep last 7)
        echo "Cleaning up old snapshots..."
        OLD_SNAPSHOTS=$(aws rds describe-db-snapshots \
            --db-instance-identifier $DB_INSTANCE \
            --query 'reverse(sort_by(DBSnapshots[?starts_with(DBSnapshotIdentifier, `dealsbasket-backup-`)][], &SnapshotCreateTime))[7:].DBSnapshotIdentifier' \
            --output text)
        
        for snapshot in $OLD_SNAPSHOTS; do
            if [ ! -z "$snapshot" ]; then
                echo "Deleting old snapshot: $snapshot"
                aws rds delete-db-snapshot --db-snapshot-identifier "$snapshot" --output json | cat
            fi
        done
    else
        echo "Error waiting for snapshot to complete"
        exit 1
    fi
else
    echo "Failed to initiate snapshot creation!"
    exit 1
fi