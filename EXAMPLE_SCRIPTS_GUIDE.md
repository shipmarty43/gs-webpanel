# Example Administration Scripts Guide

## Overview

The C2 Panel comes with 6 pre-installed example scripts for common system administration tasks. These scripts are automatically initialized when you first run the panel.

## Available Scripts

### 1. System Information
**Category:** Monitoring
**Description:** Collects comprehensive system information

**Collects:**
- Hostname and OS information
- CPU model, cores, and usage
- Memory usage (RAM)
- Disk usage
- Network interfaces and IPs
- System uptime and load average
- Top processes by memory and CPU

**Usage:**
- Run on hosts to get quick system overview
- Useful for troubleshooting performance issues
- Can be scheduled as periodic health check

**Example output:**
```
==========================================
SYSTEM INFORMATION REPORT
Generated: 2024-11-17 10:30:00
==========================================

--- Hostname ---
web-server-01

--- OS Information ---
OS: Ubuntu 22.04.3 LTS

--- CPU Information ---
CPU Model: Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz
CPU Cores: 4
CPU Usage: 15.3%
...
```

---

### 2. Security Audit
**Category:** Security
**Description:** Performs basic security checks

**Checks:**
- Failed SSH login attempts
- SSH configuration (PermitRootLogin, PasswordAuthentication)
- Users with UID 0 (root privileges)
- Empty password accounts
- Firewall status (UFW/firewalld/iptables)
- Open/listening ports
- Recently modified system files
- World-writable files in /etc
- Installed security packages

**Usage:**
- Run after system setup to verify security
- Periodic security audits
- Compliance checking

**Important:**
- Some checks require root privileges
- Review output for security issues
- Fix any detected vulnerabilities

---

### 3. Disk Cleanup
**Category:** Maintenance
**Description:** Safely cleans temporary files and caches

**Cleans:**
- APT/YUM package manager cache
- /tmp files (older than 7 days)
- /var/tmp files (older than 30 days)
- Large log files (>100MB)
- Systemd journal logs (keeps last 7 days)
- User cache directories

**Usage:**
- Run when disk space is low
- Periodic maintenance (weekly/monthly)
- Before system updates

**Safety:**
- Only removes safe temporary files
- Keeps recent files and logs
- Shows disk usage before/after

**Example:**
```bash
# Before cleanup
/dev/sda1       50G   45G  2.5G  95% /

# After cleanup
/dev/sda1       50G   38G  9.5G  80% /
Freed: 7GB
```

---

### 4. System Update
**Category:** Maintenance
**Description:** Updates system packages and installs security patches

**Features:**
- Detects package manager (APT/YUM/DNF)
- Updates package lists
- Shows available updates
- Installs security patches
- Cleans up old packages
- Checks if reboot required

**Usage:**
- Regular system updates (weekly/monthly)
- Security patching
- Keeping systems up-to-date

**Important:**
- **Requires root privileges**
- May require system reboot
- Test on dev systems first
- Review changes before applying to production

**Warning Signs:**
```
⚠ SYSTEM REBOOT REQUIRED
The following packages require a restart:
  linux-image-5.15.0-91-generic
  systemd
```

---

### 5. Service Status Check
**Category:** Monitoring
**Description:** Checks status of critical services

**Monitors:**
- System services (SSH, cron, rsyslog)
- Web servers (nginx, Apache)
- Databases (MySQL, PostgreSQL, MongoDB, Redis)
- Docker containers and images
- Failed services
- Services using most memory

**Usage:**
- Health checks before/after deployments
- Troubleshooting service issues
- Monitoring service availability

**Example output:**
```
--- Common System Services ---
✓ sshd: RUNNING
✓ cron: RUNNING
✓ rsyslog: RUNNING

--- Web Servers ---
✓ nginx: RUNNING

--- Databases ---
✓ postgresql: RUNNING
✗ redis: STOPPED

--- Failed Services ---
0 loaded units listed.
```

---

### 6. Network Diagnostic
**Category:** Diagnostics
**Description:** Performs comprehensive network diagnostics

**Tests:**
- Network interfaces and IPs
- Routing table
- DNS configuration and resolution
- Connectivity to common servers
- Active network connections
- Listening ports
- Firewall rules
- Bandwidth usage (if vnstat installed)
- Public IP address
- Traceroute to 8.8.8.8

**Usage:**
- Troubleshooting network issues
- Verifying network configuration
- Checking connectivity problems
- Firewall rule verification

**Example issues detected:**
```
google.com: ✗ FAILED        # DNS issue
8.8.8.8: ✗ Unreachable      # Network connectivity issue
Public IP: Unable to determine  # No internet access
```

---

## How to Use Example Scripts

### Via Web Interface

1. **Navigate to Scripts page**
   - Login to C2 Panel
   - Click "Scripts" in navigation

2. **Find example script**
   - Scripts are pre-loaded on first run
   - Look for scripts with categories: monitoring, security, maintenance, diagnostics

3. **Execute on hosts**
   - Go to Tasks page
   - Click "Create Task"
   - Select script and target hosts
   - Click "Execute"

4. **View results**
   - Monitor task execution
   - View output in task results

### Via Command Line (on host)

If you want to run scripts directly on a host:

```bash
# Copy script to host
scp scripts/example_scripts/system_info.sh user@host:/tmp/

# Make executable
ssh user@host "chmod +x /tmp/system_info.sh"

# Execute
ssh user@host "/tmp/system_info.sh"
```

---

## Customization

### Modifying Example Scripts

You can modify example scripts to fit your needs:

1. Go to Scripts page
2. Find the script
3. Click "Edit"
4. Modify script content
5. Save changes

### Creating New Scripts Based on Examples

1. Copy an example script as starting point
2. Modify for your specific needs
3. Save as new script with descriptive name

---

## Best Practices

### 1. Test Before Production
- Test scripts on dev/staging systems first
- Verify output is as expected
- Check for errors or warnings

### 2. Schedule Regular Execution
- **System Info**: Daily (monitoring)
- **Security Audit**: Weekly (compliance)
- **Disk Cleanup**: Weekly (maintenance)
- **System Update**: Weekly/Monthly (security)
- **Service Check**: Hourly/Daily (monitoring)
- **Network Diagnostic**: As needed (troubleshooting)

### 3. Review Output
- Check for error messages
- Look for security issues
- Monitor resource usage
- Track changes over time

### 4. Root Privileges
Scripts that require root:
- System Update (package installation)
- Disk Cleanup (system file modification)
- Security Audit (access to /etc/shadow, logs)

Run these with sudo or as root user.

### 5. Combine Scripts
Create task groups to run multiple scripts:
```
Daily Health Check:
  - System Information
  - Service Status Check
  - Disk Usage (from Disk Cleanup, view-only)

Weekly Maintenance:
  - Security Audit
  - Disk Cleanup
  - System Update

Troubleshooting:
  - System Information
  - Service Status Check
  - Network Diagnostic
```

---

## Troubleshooting

### Script Fails to Execute

**Check:**
1. Host is online and reachable
2. GSocket connection is working
3. Script has proper permissions
4. Required commands are installed

**Common issues:**
```bash
# Command not found
apt-get install <missing-command>

# Permission denied
# Run with sudo or as root

# Timeout
# Increase task timeout in settings
```

### Incomplete Output

**Causes:**
- Timeout too short
- Command requires user input
- Missing dependencies

**Solutions:**
- Increase timeout in Settings
- Modify script to use non-interactive mode
- Install required packages

### Script Not Showing in List

**Causes:**
- Database not initialized
- Migration not run
- Script initialization failed

**Solutions:**
```bash
# Re-run initialization
docker exec -it c2-panel-web python3 scripts/init_example_scripts.py

# Or restart containers
docker-compose restart web
```

---

## Security Considerations

### Sensitive Data

Scripts may output sensitive information:
- IP addresses
- Usernames
- System paths
- Service versions

**Recommendations:**
- Limit access to task results
- Clean up old logs regularly
- Use encryption for data at rest

### Script Modification

- Review all script changes before execution
- Don't add sensitive data (passwords, API keys) to scripts
- Use environment variables for credentials
- Test in isolated environment

### Execution Permissions

- Scripts run with permissions of gs-netcat listener
- Avoid running unnecessary commands as root
- Use principle of least privilege
- Audit script execution logs

---

## Advanced Usage

### Creating Script Templates

Save commonly used parameters:
```bash
# System info with extra details
./system_info.sh > /tmp/sysinfo-$(hostname)-$(date +%Y%m%d).txt

# Security audit with email
./security_audit.sh | mail -s "Security Audit: $(hostname)" admin@example.com
```

### Combining with Other Tools

```bash
# Export to monitoring system
./system_info.sh | curl -X POST https://monitoring.example.com/api/metrics -d @-

# Log to centralized logging
./service_check.sh | logger -t c2-panel-check
```

### Scheduling with Cron

On the host (not via C2 panel):
```bash
# Daily system info at 2 AM
0 2 * * * /usr/local/bin/system_info.sh > /var/log/daily-sysinfo.log

# Weekly security audit on Sundays at 3 AM
0 3 * * 0 /usr/local/bin/security_audit.sh | mail -s "Weekly Security Audit" admin@example.com
```

---

## Support and Contribution

### Adding Your Own Scripts

See [Script Development Guide](SCRIPT_DEVELOPMENT_GUIDE.md) for creating custom scripts.

### Reporting Issues

If you find bugs or have suggestions:
1. Check existing issues
2. Provide detailed description
3. Include script output
4. Specify OS and version

### Contributing

To contribute new example scripts:
1. Follow existing script format
2. Include comprehensive comments
3. Test on multiple OS versions
4. Document usage and requirements
