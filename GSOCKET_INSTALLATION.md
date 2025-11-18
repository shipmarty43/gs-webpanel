# Installing GSocket in Docker Container

## 🚨 Problem
Web terminal fails with error: `[Errno 2] No such file or directory: 'gs-netcat'`

Monitor service logs show: `FileNotFoundError: [Errno 2] No such file or directory: 'gs-netcat'`

This happens because `gs-netcat` is not installed in the Docker container.

## ⚠️ CRITICAL: Images Must Be Rebuilt!

**The Dockerfile includes gsocket installation, but you MUST rebuild Docker images for it to take effect!**

📖 **See [REBUILD_REQUIRED.md](REBUILD_REQUIRED.md) for detailed step-by-step instructions.**

### Quick Fix

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Solution

The Dockerfile has been updated to automatically install gsocket tools.

### What Changed

**Dockerfile:**
- Downloads pre-built static binaries from GitHub releases
- Supports x86_64 and aarch64 architectures
- Fast installation (~30 seconds vs building from source)
- More reliable than curl installer

### How to Apply

**IMPORTANT**: You must rebuild the Docker image for changes to take effect.

```bash
# Stop containers
docker-compose down

# Rebuild images (this will install gsocket)
docker-compose build

# Start containers
docker-compose up -d
```

Or use the deployment script:
```bash
./deploy.sh
```

### Verify Installation

After rebuild, verify gs-netcat is installed:

```bash
# Check if gs-netcat is available
docker exec -it c2-panel-web which gs-netcat

# Should output: /usr/local/bin/gs-netcat or similar
```

### Testing Web Terminal

1. Navigate to Hosts page
2. Click "Terminal" button for any host
3. Should see: "Waiting for host connection..."
4. Once host connects, you'll have interactive shell access

### Troubleshooting

**Error: "gs-netcat: command not found"**
- Docker image wasn't rebuilt
- Solution: `docker-compose build --no-cache`

**Error: "Connection timeout"**
- Host is not connected via gsocket
- Check host is running: `gs-netcat -s <secret> -l -i`
- Verify secret matches

**Error: "Permission denied"**
- Secret file permissions issue
- This should be handled automatically (chmod 0600)

## GSocket Installation Details

The static binary release includes:
- `gs-netcat` - Main tool for connecting to remote shells
- `gs-sftp` - Secure file transfer
- `gs-mount` - Remote file system mounting
- `blitz` - Additional tools

**Installation method:**
- Downloads pre-built static binaries from GitHub releases
- Detects architecture automatically (x86_64/aarch64)
- Extracts to `/usr/local/bin/`
- No compilation required - fast and reliable

## Next Steps

After rebuilding the container:
1. ✅ Web terminal will work
2. ✅ Can execute interactive commands on hosts
3. ✅ Full shell access through browser
