# ⚠️ IMPORTANT: Docker Rebuild Required!

## 🚨 Critical Issue

If you're seeing this error in monitor logs:
```
FileNotFoundError: [Errno 2] No such file or directory: 'gs-netcat'
```

**Your Docker images are outdated and need to be rebuilt!**

## ⚡ Quick Fix

Run these commands to rebuild and restart:

```bash
# Stop all containers
docker-compose down

# Rebuild images (this installs gs-netcat and other dependencies)
docker-compose build --no-cache

# Start containers
docker-compose up -d
```

## 📋 Step-by-Step Instructions

### 1. Stop Running Containers

```bash
cd /path/to/gs-webpanel
docker-compose down
```

You should see:
```
Stopping c2-panel-monitor ... done
Stopping c2-panel-web     ... done
Removing c2-panel-monitor ... done
Removing c2-panel-web     ... done
```

### 2. Rebuild Docker Images

**Option A: Full Rebuild (Recommended)**
```bash
docker-compose build --no-cache
```

This will:
- ✅ Install all system dependencies
- ✅ Install gsocket tools (gs-netcat, gs-sftp, etc.)
- ✅ Install Python dependencies
- ✅ Copy application files

Expected output:
```
Building web
[+] Building 45.2s (15/15) FINISHED
 => [internal] load build definition from Dockerfile
 => => transferring dockerfile: 1.23kB
 => [internal] load .dockerignore
 => ...
 => [7/10] RUN ARCH=$(uname -m) && ...
 => ...
Successfully built abc123def456
Successfully tagged gs-webpanel_web:latest
```

Build time: ~30-60 seconds (using pre-built static binaries)

**Option B: Quick Rebuild (if you're sure cache is clean)**
```bash
docker-compose build
```

### 3. Start Containers

```bash
docker-compose up -d
```

You should see:
```
Creating c2-panel-web     ... done
Creating c2-panel-monitor ... done
```

### 4. Verify Installation

Check that gs-netcat is installed:

```bash
# Check web container
docker exec c2-panel-web which gs-netcat

# Check monitor container
docker exec c2-panel-monitor which gs-netcat
```

Both should output:
```
/usr/local/bin/gs-netcat
```

### 5. Check Logs

Monitor logs should now be clean:

```bash
docker-compose logs -f monitor
```

Expected output (no errors):
```
[2025-11-18 01:00:00] [INFO] Starting monitor service...
[2025-11-18 01:00:00] [INFO] Checking 1 hosts...
[2025-11-18 01:00:00] [INFO] Host check completed
```

## 🔍 Why This Happens

### What Changed

Recent updates to the project added:
1. **gsocket installation** to Dockerfile (line 18)
2. **System dependencies** required by gsocket (bash, make, openssl, etc.)

### The Problem

Docker uses **image caching**. If you:
- Pulled latest code with `git pull`
- But didn't rebuild images with `docker-compose build`

Then:
- ❌ Old images (without gs-netcat) are still running
- ❌ New code expects gs-netcat to be available
- ❌ Result: FileNotFoundError

### The Solution

**Always rebuild after pulling updates:**
```bash
git pull
docker-compose build
docker-compose up -d
```

## 🛠️ Alternative: Use Deploy Script

For convenience, use the automated deploy script:

```bash
./deploy.sh
```

This script automatically:
1. ✅ Backs up database
2. ✅ Pulls latest code
3. ✅ Rebuilds images
4. ✅ Restarts containers
5. ✅ Checks status

## 📊 Verify Everything Works

### 1. Check Container Status

```bash
docker-compose ps
```

Expected:
```
Name                   State    Ports
--------------------------------------------
c2-panel-web       Up      0.0.0.0:3000->8000/tcp
c2-panel-monitor   Up
```

### 2. Test Web Interface

Open browser:
- URL: http://localhost:3000/login
- Login: admin / Admin123456!

### 3. Test Terminal Feature

1. Go to Hosts page
2. Click "Terminal" button
3. Should connect without errors

### 4. Test Monitor Service

Check logs for host monitoring:
```bash
docker-compose logs monitor | tail -20
```

Should see regular host checks without errors.

## ❗ Common Mistakes

### Mistake 1: Only Restarting Containers

```bash
# ❌ WRONG - doesn't rebuild images
docker-compose restart
```

```bash
# ✅ CORRECT - rebuilds images first
docker-compose down
docker-compose build
docker-compose up -d
```

### Mistake 2: Rebuilding Only One Container

```bash
# ❌ WRONG - monitor still uses old image
docker-compose up -d --build web
```

```bash
# ✅ CORRECT - rebuilds all services
docker-compose build
docker-compose up -d
```

### Mistake 3: Not Using --no-cache

If rebuild seems too fast (< 30 seconds), cache might be stale:

```bash
# ✅ Force clean rebuild
docker-compose build --no-cache
```

## 🔄 When to Rebuild

Rebuild is required when:

- ✅ After `git pull` with Dockerfile changes
- ✅ After updating system dependencies
- ✅ After changing requirements.txt
- ✅ When seeing "command not found" errors
- ✅ When features that worked before stop working

Rebuild is **NOT** required for:

- ❌ Python code changes (app/ folder) - volume mounted
- ❌ Template changes (templates/) - volume mounted
- ❌ Static file changes (static/) - volume mounted
- ❌ Script changes (scripts/) - volume mounted
- ❌ Configuration changes (.env)

## 📝 Dockerfile Changes Log

Recent changes that require rebuild:

### Commit 7b476b8 (2025-11-18)
- **LATEST:** Uses static binary releases from GitHub
- Supports x86_64 and aarch64 architectures
- Much faster build time (~30-60 seconds)
- More reliable installation method
- **REBUILD REQUIRED** for web terminal to work

### Commit 1519325 (2025-11-18)
- Changed to building from source
- Added build dependencies: g++, autoconf, automake, libtool
- **SUPERSEDED** by static binary approach

### Commit 077db47 (2024-11-17)
- Initial gsocket installation attempt: `RUN curl -fsSL https://gsocket.io/x | bash`
- Added dependencies: bash, make, openssl, libssl-dev
- **SUPERSEDED** - curl installer didn't work reliably in Docker

### How to Check if Rebuild is Needed

```bash
# Check if gs-netcat is in your running containers
docker exec c2-panel-web which gs-netcat 2>/dev/null

# If output is empty or error - REBUILD REQUIRED
# If output is /usr/local/bin/gs-netcat - OK
```

## 🆘 Still Having Issues?

### Issue: Rebuild takes too long

**Normal build time:** 30-60 seconds (using static binary releases)
**If taking longer:** Check network connection or Docker cache
**Solution:** Be patient, downloading binaries from GitHub

### Issue: Build fails with network errors

```
ERROR: failed to solve: failed to fetch ...
```

**Solution:**
```bash
# Wait a moment and retry
docker-compose build --no-cache

# Or use different DNS
echo '{"dns": ["8.8.8.8", "1.1.1.1"]}' | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker
```

### Issue: "No space left on device"

```bash
# Clean up old images
docker system prune -a

# Then rebuild
docker-compose build --no-cache
```

### Issue: Containers immediately exit after rebuild

```bash
# Check logs for errors
docker-compose logs web
docker-compose logs monitor

# Common causes:
# - Database migration failed
# - Permission issues with /app/data
# - Invalid .env configuration
```

## 📞 Getting Help

If you still have issues after rebuilding:

1. Check logs:
   ```bash
   docker-compose logs web
   docker-compose logs monitor
   ```

2. Verify gs-netcat installation:
   ```bash
   docker exec c2-panel-web gs-netcat -h
   ```

3. Check issue tracker on GitHub

## ✅ Summary

**To fix "gs-netcat not found" error:**

```bash
cd /path/to/gs-webpanel
docker-compose down
docker-compose build --no-cache
docker-compose up -d
docker-compose logs -f
```

**Time required:** 30-60 seconds (using static binary releases)

**After rebuild:**
- ✅ Web terminal works
- ✅ Monitor service runs without errors
- ✅ All gsocket features available
- ✅ No more FileNotFoundError

---

**Remember:** After every `git pull`, always run `docker-compose build` before starting containers!
