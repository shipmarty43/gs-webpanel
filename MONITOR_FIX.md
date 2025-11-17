# Fix for Monitor Service Module Import Error

## Problem
Monitor service was failing with error:
```
ModuleNotFoundError: No module named 'app'
```

## Solution
Fixed in commit `882a9d8` by:
1. Changed command from `python app/services/monitor_service.py` to `python -m app.services.monitor_service`
2. Added `PYTHONPATH=/app` environment variable to monitor service

## How to Apply

### Method 1: Using deploy.sh (Recommended)
```bash
./deploy.sh
```

This will:
- Pull latest changes
- Rebuild containers
- Restart all services

### Method 2: Manual restart
```bash
# Pull latest changes
git pull origin claude/gsocket-c2-panel-01CChs23hpBqkFEJi2ygWxWR

# Restart monitor service
docker-compose restart monitor

# Or restart all services
docker-compose down && docker-compose up -d
```

### Method 3: Quick update
```bash
./update.sh
```

## Verification

After applying the fix, verify monitor service is running:

```bash
# Check container status
docker-compose ps

# Check monitor logs (should not show ModuleNotFoundError)
docker-compose logs monitor

# Should see:
# c2-panel-monitor  | Starting monitor service...
# c2-panel-monitor  | Checking X hosts...
```

## Technical Details

**Why this happened:**
- Old command: `python app/services/monitor_service.py` - runs file directly
- Problem: Python doesn't recognize relative imports like `from app.database import ...`

**Why this fixes it:**
- New command: `python -m app.services.monitor_service` - runs as module
- Python properly resolves `app` package imports
- PYTHONPATH ensures `/app` is in module search path

## Related Files
- `docker-compose.yml` - Updated monitor service configuration
- `app/services/monitor_service.py` - Already had correct `if __name__ == "__main__"` block
