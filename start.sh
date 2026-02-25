#!/bin/bash
# Production startup script with database migrations
# This script ensures database migrations run before starting the application

set -e  # Exit immediately if a command exits with a non-zero status

echo "=========================================="
echo "Starting Muhasebe Pro Production Server"
echo "=========================================="

# Run database migrations
echo ""
echo "[1/2] Running database migrations..."
echo "------------------------------------------"
if flask db upgrade; then
    echo "✅ Database migrations completed successfully"
else
    echo "❌ Database migrations FAILED"
    echo "Application will not start to prevent data corruption"
    exit 1
fi

# Start the application
echo ""
echo "[2/2] Starting Gunicorn server..."
echo "------------------------------------------"
exec gunicorn --workers 1 --timeout 120 --bind 0.0.0.0:8080 "app:create_app()"
