# Troubleshooting: Login Issues

## Problem: "Incorrect username or password"

### Quick Fix

The admin user has been reset with correct credentials:

```
Username: admin
Password: Admin123456!
URL: http://localhost:8000/login
```

### Step-by-Step Verification

#### 1. Verify Database & User

Run the verification script:

```bash
python3 scripts/test_login.py
```

Expected output:
```
✓ ALL TESTS PASSED!
Login should work with:
  Username: admin
  Password: Admin123456!
```

If this fails, reset the admin user:

```bash
python3 scripts/reset_admin.py
```

#### 2. Verify Server is Running

Check if containers are running:

```bash
docker-compose ps
```

Expected output:
```
NAME                STATUS
c2-panel-web        Up X minutes
c2-panel-monitor    Up X minutes
```

If not running, start them:

```bash
docker-compose up -d
```

#### 3. Check Web Server Logs

View logs for errors:

```bash
docker-compose logs web --tail=100
```

Look for:
- ✓ "Application startup complete"
- ✗ Any error messages
- ✗ "ModuleNotFoundError"

#### 4. Test API Directly

Test the login API endpoint:

```bash
# From host machine
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin123456!"}'
```

Expected response (200 OK):
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

Error response (401 Unauthorized):
```json
{
  "detail": "Incorrect username or password"
}
```

#### 5. Test Frontend Access

Open browser and navigate to:
```
http://localhost:8000/login
```

Check browser console (F12 → Console) for errors.

Check Network tab (F12 → Network):
- Look for POST request to `/api/auth/login`
- Check request payload
- Check response status and body

### Common Issues & Solutions

#### Issue 1: Server Not Running

**Symptoms:**
- Browser shows "Unable to connect"
- curl: "Connection refused"

**Solution:**
```bash
# Start containers
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

#### Issue 2: Wrong Port

**Symptoms:**
- Server running but not accessible on port 8000

**Solution:**

Check what port the server is actually using:

```bash
docker-compose ps
# Look for port mapping like "0.0.0.0:8000->8000/tcp"

# Check if port is in use
netstat -tlnp | grep 8000
# or
lsof -i :8000
```

If port is already in use, modify `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # Use different external port
```

Then access: `http://localhost:8001/login`

#### Issue 3: Database Locked

**Symptoms:**
- Error: "database is locked"
- Login hangs

**Solution:**

```bash
# Stop all containers
docker-compose down

# Check for stale locks
rm -f data/c2panel.db-journal

# Restart
docker-compose up -d
```

#### Issue 4: CORS / Browser Issues

**Symptoms:**
- Console error: "CORS policy blocked"
- Network tab shows preflight OPTIONS request failed

**Solution:**

Check `app/main.py` for CORS configuration:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Should allow all in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Clear browser cache:
- Chrome: Ctrl+Shift+Del → Clear browsing data
- Try incognito mode

#### Issue 5: JavaScript Not Loading

**Symptoms:**
- Login button doesn't work
- No network requests in browser

**Check:**

1. View page source (Ctrl+U)
2. Look for `<script>` tags in login.html
3. Check browser console for JavaScript errors

**Solution:**

```bash
# Ensure static files are mounted
docker-compose down
docker-compose up -d

# Check volume mounts in docker-compose.yml
volumes:
  - ./static:/app/static
  - ./app/templates:/app/templates
```

#### Issue 6: bcrypt Version Warning

**Symptoms:**
- Login works but logs show bcrypt warnings

**Note:** This is a harmless warning. The bcrypt module works correctly despite the warning about `__about__` attribute.

To suppress (optional):
```bash
pip uninstall -y bcrypt
pip install bcrypt==4.1.2
```

### Testing Commands Summary

```bash
# 1. Check database & verify password
python3 scripts/test_login.py

# 2. Reset admin user (if needed)
python3 scripts/reset_admin.py

# 3. Test API login
bash scripts/test_api_login.sh

# 4. Check containers
docker-compose ps

# 5. View logs
docker-compose logs web --tail=50

# 6. Restart everything
docker-compose down && docker-compose up -d

# 7. Check web server is responding
curl http://localhost:8000/
```

### Manual Login Test (No Docker)

If running locally without Docker:

```bash
# 1. Activate venv
source venv/bin/activate

# 2. Start server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 3. In another terminal, test
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin123456!"}'
```

### Still Not Working?

1. **Check environment variables:**
   ```bash
   docker-compose exec web env | grep -E "SECRET_KEY|DATABASE"
   ```

2. **Connect to container and test directly:**
   ```bash
   docker-compose exec web python3 scripts/test_login.py
   ```

3. **Inspect database file:**
   ```bash
   docker-compose exec web python3 -c "
   from app.database import SessionLocal
   from app.models.user import User
   db = SessionLocal()
   users = db.query(User).all()
   for u in users:
       print(f'User: {u.username}, Hash: {u.password_hash[:50]}...')
   "
   ```

4. **Full clean restart:**
   ```bash
   # WARNING: This will delete all data
   docker-compose down -v
   rm -rf data/c2panel.db
   docker-compose up -d

   # Recreate admin
   docker-compose exec web python3 scripts/reset_admin.py
   ```

### Security Note

The default password `Admin123456!` is for initial setup only. After successful login, create a new admin user with a strong password and delete the default admin account.

### Contact

If issues persist, check:
1. GitHub issues: Look for similar problems
2. Docker logs: `docker-compose logs --tail=200`
3. System logs: Check for port conflicts or resource issues
