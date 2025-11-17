# Automatic Database Initialization

## Overview

The GSocket C2 Panel automatically initializes the database and creates a default admin user when Docker containers start for the first time.

## How It Works

### Docker Entrypoint (`entrypoint.sh`)

When containers start, the entrypoint script:

1. **Checks if database exists** (`/app/data/c2panel.db`)
   - If NOT exists → Runs `scripts/init_db.py` to create tables
   - If exists → Skips database creation

2. **Checks for users in database**
   - If NO users found → Runs `scripts/create_test_admin.py`
   - If users exist → Skips user creation

3. **Starts the application**

### Initialization Scripts

#### `scripts/init_db.py`
Creates all database tables:
- users
- hosts
- scripts
- tasks
- task_executions
- logs
- ping_history

#### `scripts/create_test_admin.py`
Creates default admin user:
- **Username**: `admin`
- **Password**: `Admin123456!`
- Password is hashed with bcrypt

## First-Time Setup

### With Docker (Automatic)

```bash
# Just start the containers
docker-compose up -d

# Database and admin user are created automatically
# Wait 10 seconds, then access:
# http://localhost:8000/login
# Username: admin
# Password: Admin123456!
```

### Without Docker (Manual)

```bash
# 1. Initialize database
python3 scripts/init_db.py

# 2. Create admin user
python3 scripts/create_test_admin.py

# 3. Start application
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Re-initialization

### Reset Database (Clean Start)

**WARNING**: This deletes all data!

```bash
# Stop containers
docker-compose down

# Delete database
rm data/c2panel.db

# Restart (will auto-initialize)
docker-compose up -d
```

### Reset Admin Password Only

Keep data, just reset admin password:

```bash
# Option 1: Using script
docker-compose exec web python3 scripts/reset_admin.py

# Option 2: Direct execution
python3 scripts/reset_admin.py
```

## Verification

### Check Database Initialization

```bash
# Check if database file exists
ls -lh data/c2panel.db

# Should show file with size > 100KB
```

### Check Admin User

```bash
# Test credentials
python3 scripts/test_login.py

# Should show:
# ✓ ALL TESTS PASSED!
# Login should work with:
#   Username: admin
#   Password: Admin123456!
```

### Check Container Logs

```bash
# View initialization logs
docker-compose logs web | head -30

# Should show:
# → Database not found, initializing...
# ✓ Database initialized
# → Creating default admin user...
# ✓ Admin user created
# Starting application...
```

## Troubleshooting

### Database Already Exists

If database exists but is corrupted:

```bash
# Backup first (if you want to save data)
cp data/c2panel.db data/c2panel.db.backup

# Remove and recreate
rm data/c2panel.db
docker-compose restart web
```

### No Admin User Created

If database exists but no users:

```bash
# Create admin manually
docker-compose exec web python3 scripts/create_test_admin.py

# Or without Docker
python3 scripts/create_test_admin.py
```

### Permission Denied

If initialization fails with permission errors:

```bash
# Fix data directory permissions
sudo chown -R $USER:$USER data/
chmod 755 data/
```

### Database Locked

If you see "database is locked" errors:

```bash
# Stop all containers
docker-compose down

# Remove lock files
rm -f data/c2panel.db-journal
rm -f data/c2panel.db-wal

# Restart
docker-compose up -d
```

## Environment Variables

The initialization process respects these environment variables (`.env`):

```bash
# Database location
DATABASE_URL=sqlite:///./data/c2panel.db

# Encryption keys (used for gsocket secrets)
SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-encryption-key
```

## Migration from Older Versions

If upgrading from a version without auto-initialization:

```bash
# 1. Backup existing database
cp data/c2panel.db data/c2panel.db.backup

# 2. Pull new code
git pull

# 3. Rebuild containers
docker-compose down
docker-compose build
docker-compose up -d

# 4. Database will be detected and preserved
# 5. Admin user will NOT be recreated (existing users preserved)
```

## Custom Initialization

### Add Custom User on Startup

Edit `scripts/create_test_admin.py` to add more users:

```python
# After creating admin user, add:
custom_user = User(
    username="operator",
    password_hash=pwd_context.hash("YourPassword123!")
)
db.add(custom_user)
db.commit()
```

### Skip Admin Creation

If you don't want automatic admin creation:

```bash
# Edit entrypoint.sh, comment out:
# python3 scripts/create_test_admin.py
```

### Add Sample Data

Create `scripts/add_sample_data.py` and call it from `entrypoint.sh`:

```bash
# In entrypoint.sh, after admin creation:
python3 scripts/add_sample_data.py
```

## Security Notes

### Default Password

⚠️ **CRITICAL**: The default password `Admin123456!` is for initial setup only.

**After first login:**
1. Create a new admin user with strong password
2. Delete or disable the default `admin` account
3. Implement password rotation policy

### Production Deployment

For production:

1. **Change default credentials immediately**
2. **Set strong SECRET_KEY and ENCRYPTION_KEY** in `.env`
3. **Disable automatic admin creation** after initial setup
4. **Implement proper user management**
5. **Enable audit logging**

### Database Backup

Always backup before re-initialization:

```bash
# Automated backup script
cp data/c2panel.db "data/backup_$(date +%Y%m%d_%H%M%S).db"
```

## Technical Details

### Database Schema Version

The initialization creates the latest schema. No migrations are run automatically.

For schema updates, use migration scripts:

```bash
# Example: Add custom_gsrn_server field
python3 scripts/migrate_add_custom_gsrn.py
```

### Idempotency

The entrypoint script is idempotent:
- Safe to run multiple times
- Won't duplicate data
- Won't overwrite existing database
- Won't recreate existing users

### Startup Time

First startup (with initialization): ~5-10 seconds
Normal startup (existing database): ~2-3 seconds

## Monitoring

### Check Initialization Status

```bash
# Real-time logs
docker-compose logs -f web

# Check for successful initialization
docker-compose logs web | grep -E "initialized|created"
```

### Health Check

```bash
# Check if API responds
curl http://localhost:8000/

# Test login endpoint
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin123456!"}'
```

## Support

If initialization fails:

1. Check logs: `docker-compose logs web`
2. Check permissions: `ls -la data/`
3. Try manual initialization: `python3 scripts/init_db.py`
4. See: `TROUBLESHOOTING_LOGIN.md`
