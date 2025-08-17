#!/bin/bash

set -x  # Enable debug output

# Source environment variables
set -a
source /media/durgesh/Development/DealsBasket_Project/.env
set +a

# Use existing credentials and configuration
KEY_PATH="/media/durgesh/Development/DealsBasket_Project/Credentials/DealsBasket.pem"
RDS_HOST="$DB_HOST"
DB_USER="$DB_USER"
DB_PASSWORD="$DB_PASSWORD"
DB_NAME="$DB_NAME"
LOCAL_PORT=5432
REMOTE_PORT=5432

echo "Setting up SSH tunnel to RDS..."
echo "Local port $LOCAL_PORT will be forwarded to $RDS_HOST:$REMOTE_PORT"

# Kill any existing tunnels and wait for them to die
pkill -f "ssh.*:$LOCAL_PORT:.*:$REMOTE_PORT" || true
sleep 2

# Test if the port is already in use
if nc -z localhost $LOCAL_PORT 2>/dev/null; then
    echo "Port $LOCAL_PORT is already in use. Checking what's using it..."
    sudo lsof -i :$LOCAL_PORT
    echo "Please free the port and try again."
    exit 1
fi

# Create .ssh directory if it doesn't exist
mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"

# Test SSH connection first
echo "Testing SSH connection to bastion host..."
ssh -i "$KEY_PATH" \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    ec2-user@$BASTION_HOST "echo 'SSH connection successful'"

if [ $? -ne 0 ]; then
    echo "Failed to connect to bastion host"
    exit 1
fi

echo "Testing RDS connection from bastion host..."
ssh -i "$KEY_PATH" \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    ec2-user@$BASTION_HOST \
    "PGPASSWORD=DUrg7080 psql -h $RDS_HOST -U durgesh -d dealsbasket -c '\conninfo'"

if [ $? -ne 0 ]; then
    echo "Failed to connect to RDS from bastion host"
    exit 1
fi

echo "Setting up tunnel..."
# Set up the tunnel with verbose output
ssh -v -i "$KEY_PATH" \
    -N \
    -L 127.0.0.1:$LOCAL_PORT:$RDS_HOST:$REMOTE_PORT \
    -o ExitOnForwardFailure=yes \
    -o ServerAliveInterval=60 \
    -o TCPKeepAlive=yes \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    ec2-user@$BASTION_HOST

tunnel_status=$?

if [ $tunnel_status -eq 0 ]; then
    echo "SSH tunnel established successfully"
    echo "Testing local connection..."
    sleep 2
    PGPASSWORD=dealsbasket_password psql -h localhost -U dealsbasket_user -d dealsbasket_db -c "\conninfo"
else
    echo "Failed to establish SSH tunnel (exit code: $tunnel_status)"
    exit 1
fi