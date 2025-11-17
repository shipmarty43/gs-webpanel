# Installing GSocket in Docker Container

## Problem
Web terminal fails with error: `[Errno 2] No such file or directory`

This happens because `gs-netcat` is not installed in the Docker container.

## Solution

The Dockerfile has been updated to automatically install gsocket tools.

### What Changed

**Dockerfile:**
- Added system dependencies: `bash`, `make`, `openssl`, `libssl-dev`
- Enabled gsocket installation: `RUN curl -fsSL https://gsocket.io/x | bash`

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

The gsocket installer (`https://gsocket.io/x`) installs:
- `gs-netcat` - Main tool for connecting to remote shells
- `gs-sftp` - Secure file transfer
- `gs-mount` - Remote file system mounting
- `blitz` - Additional tools

Installation location: `/usr/local/bin/`

## Next Steps

After rebuilding the container:
1. ✅ Web terminal will work
2. ✅ Can execute interactive commands on hosts
3. ✅ Full shell access through browser
