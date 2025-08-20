#!/bin/bash

# Start the simple health server in the background
echo "Starting simple health server on port 8001..."
python3 simple_health_server.py &

# Wait a moment for the health server to start
sleep 2

# Start the Django application with gunicorn
echo "Starting Django application on port 8000..."
exec gunicorn server.wsgi:application --bind 0.0.0.0:8000 --workers 3
