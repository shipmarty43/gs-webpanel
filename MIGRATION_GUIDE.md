# Database Migration Guide

## Overview

This project uses automatic database migrations to keep your database schema up-to-date with the latest code changes.

## How It Works

When you start the Docker containers, the entrypoint script (`entrypoint.sh`) automatically:

1. **Checks if database exists**
   - If not: Creates new database with all tables
   - If yes: Runs migration script to update schema

2. **Applies migrations** (`scripts/migrate_db.py`)
   - Checks for missing columns
   - Adds new columns without losing data
   - Skips already applied migrations

3. **Creates admin user** (if no users exist)
   - Username: `admin`
   - Password: `Admin123456!`

## Automatic Migration

Migrations run automatically on container restart:

```bash
docker-compose restart web
# or
docker compose restart web
```

You'll see output like:
```
→ Checking for database migrations...
========================================
Database Migration
========================================
Database: data/c2panel.db

✓ Column 'custom_gsrn_server' already exists

========================================
✓ Database is up to date
========================================
```

## Manual Migration

If you need to run migrations manually (without restarting containers):

```bash
# Inside the container
docker exec -it c2-panel-web python3 scripts/migrate_db.py

# Or if you're already inside the container or development environment
python3 scripts/migrate_db.py
```

## Migration History

### Migration 1: Custom GSRN Server Support
**Date**: 2024-11-17
**Description**: Added `custom_gsrn_server` column to `hosts` table

- **Column**: `custom_gsrn_server VARCHAR(255)`
- **Purpose**: Allow each host to use a custom Global Socket Relay Network server
- **Nullable**: Yes (defaults to NULL, uses global setting if not specified)

## How to Add New Migrations

When you add new fields to models, update `scripts/migrate_db.py`:

```python
# Check if column exists
if not column_exists(cursor, 'table_name', 'new_column_name'):
    print("→ Adding 'new_column_name' to table_name...")
    cursor.execute("""
        ALTER TABLE table_name
        ADD COLUMN new_column_name TYPE
    """)
    conn.commit()
    print("✓ Column 'new_column_name' added")
    migrations_applied += 1
else:
    print("✓ Column 'new_column_name' already exists")
```

## Troubleshooting

### Error: "no such column: hosts.custom_gsrn_server"

**Solution**: Migration wasn't applied. Run manual migration:

```bash
docker exec -it c2-panel-web python3 scripts/migrate_db.py
docker-compose restart web
```

### Error: "Database file not found"

**Solution**: Let the container create the database first:

```bash
docker-compose up -d
# Wait for database to be created
docker-compose restart web
```

### Checking Migration Status

To see which migrations have been applied:

```bash
docker exec -it c2-panel-web python3 scripts/migrate_db.py
```

The script will show:
- ✓ Columns that already exist
- → Columns being added
- ✓ Number of migrations applied

## Safety

- **Idempotent**: Safe to run multiple times - won't duplicate changes
- **Non-destructive**: Only adds columns, never removes data
- **Automatic backup**: Use `./deploy.sh` for automatic backups before updates

## Best Practices

1. **Always backup before major updates**:
   ```bash
   ./deploy.sh  # Includes automatic backup
   ```

2. **Test migrations in development first**:
   ```bash
   # Stop containers
   docker-compose down

   # Backup database
   cp data/c2panel.db data/c2panel.db.backup

   # Test migration
   docker-compose up -d
   ```

3. **Monitor migration output** during container startup to ensure migrations complete successfully

## Rollback

If a migration fails:

1. Stop containers:
   ```bash
   docker-compose down
   ```

2. Restore from backup:
   ```bash
   cp data/c2panel.db.backup data/c2panel.db
   ```

3. Restart containers:
   ```bash
   docker-compose up -d
   ```
