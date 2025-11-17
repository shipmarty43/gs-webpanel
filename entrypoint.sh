#!/bin/bash

###############################################################################
# Docker Entrypoint Script
#
# This script:
# 1. Initializes database if it doesn't exist
# 2. Creates admin user if no users exist
# 3. Starts the application
###############################################################################

set -e

echo "=========================================="
echo "GSocket C2 Panel - Starting..."
echo "=========================================="
echo ""

# Database path
DB_PATH="/app/data/c2panel.db"

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "→ Database not found, initializing..."
    python3 scripts/init_db.py
    echo "✓ Database initialized"
    echo ""

    echo "→ Creating default admin user..."
    python3 scripts/create_test_admin.py
    echo "✓ Admin user created"
    echo ""
else
    echo "✓ Database exists"

    # Run migrations for existing database
    echo "→ Checking for database migrations..."
    python3 scripts/migrate_db.py
    echo ""

    # Check if there are any users
    USER_COUNT=$(python3 -c "
from app.database import SessionLocal
from app.models.user import User
db = SessionLocal()
count = db.query(User).count()
db.close()
print(count)
" 2>/dev/null || echo "0")

    echo "  Users in database: $USER_COUNT"

    if [ "$USER_COUNT" = "0" ]; then
        echo "→ No users found, creating admin user..."
        python3 scripts/create_test_admin.py
        echo "✓ Admin user created"
    fi
    echo ""
fi

echo "=========================================="
echo "Starting application..."
echo "=========================================="
echo ""
echo "Login credentials:"
echo "  URL: http://localhost:8000/login"
echo "  Username: admin"
echo "  Password: Admin123456!"
echo ""
echo "=========================================="
echo ""

# Execute the main command
exec "$@"
