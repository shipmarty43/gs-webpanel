# CSV Import Guide for Hosts

## Overview

The CSV import feature allows you to quickly add multiple hosts to your C2 panel using a CSV (Comma-Separated Values) file. This is especially useful when setting up a large number of hosts or migrating from another system.

## CSV Format

### Required Columns

- **hostname** - Unique identifier for the host (descriptive name)
- **gsocket_secret** - GSocket secret token for connecting to the host

### Optional Columns

- **ip_address** - IP address of the host (optional, for reference only)
- **custom_gsrn_server** - Custom GSRN relay server (e.g., "relay.example.com:443")
- **description** - Short description of the host
- **tags** - Comma or semicolon-separated tags (e.g., "prod;web" or "prod,web")

### CSV Header

The first row MUST contain column names:

```csv
hostname,ip_address,gsocket_secret,custom_gsrn_server,description,tags
```

## Example CSV Files

### Basic Example (Required fields only)

```csv
hostname,gsocket_secret
web-server-01,a1b2c3d4e5f6
db-server-01,x1y2z3a4b5c6
app-server-01,p1q2r3s4t5u6
```

### Complete Example (All fields)

```csv
hostname,ip_address,gsocket_secret,custom_gsrn_server,description,tags
web-server-01,192.168.1.10,a1b2c3d4e5f6,,Production web server,prod;web;nginx
db-server-01,192.168.1.20,x1y2z3a4b5c6,,PostgreSQL database,prod;db;postgres
app-server-01,192.168.1.30,p1q2r3s4t5u6,relay.example.com:443,Application server,prod;app;nodejs
backup-server,10.0.0.50,m1n2o3p4q5r6,,Backup storage,backup;storage
```

### Example with Empty Optional Fields

```csv
hostname,ip_address,gsocket_secret,custom_gsrn_server,description,tags
web-server-01,,a1b2c3d4e5f6,,,web
db-server-01,192.168.1.20,x1y2z3a4b5c6,,,
app-server-01,,p1q2r3s4t5u6,relay.example.com:443,App server,
```

## How to Import

### Using the Web Interface

1. Navigate to **Hosts** page
2. Click **Import CSV** button (top right)
3. Click **Browse** and select your CSV file
4. Click **Import**
5. Review import results

### Download Template

1. Click **Import CSV** button
2. Click **Download Template** button
3. Edit the template with your host data
4. Import the modified file

## Import Results

After import, you'll see a detailed results summary:

- **Total rows** - Number of data rows in CSV
- **Imported** - Successfully added hosts
- **Skipped** - Rows that couldn't be imported
- **Errors** - Detailed error messages for skipped rows

Example:
```
✓ Import completed
Total rows: 10
Imported: 8
Skipped: 2

Errors:
• Row 3 (db-server-01): Hostname already exists
• Row 7 (invalid-host): Invalid hostname format
```

## Validation Rules

### Hostname Validation

- Must be 1-255 characters
- Can contain: letters, numbers, hyphens, underscores, dots
- Cannot start or end with hyphen or dot
- Must be unique across all hosts

### IP Address Validation (Optional)

- Must be valid IPv4 or IPv6 format
- Examples: `192.168.1.10`, `10.0.0.1`, `2001:db8::1`

### GSocket Secret

- Can be any string
- Recommended: Generate using `gs-netcat -g`
- Will be encrypted before storage

### Custom GSRN Server (Optional)

- Format: `hostname:port` or just `hostname`
- Example: `relay.example.com:443`

### Tags (Optional)

- Separate multiple tags with commas or semicolons
- Examples: `web,prod,nginx` or `web;prod;nginx`

## Common Errors and Solutions

### "Hostname already exists"

**Cause**: A host with this hostname is already in the database

**Solution**:
- Use a different hostname
- Delete the existing host first
- Update the existing host instead of importing

### "Invalid hostname format"

**Cause**: Hostname contains invalid characters or format

**Solution**:
- Use only letters, numbers, hyphens, underscores, dots
- Don't start/end with hyphen or dot
- Keep length between 1-255 characters

### "CSV must contain columns: hostname, gsocket_secret"

**Cause**: CSV file is missing required column headers

**Solution**:
- Ensure first row contains: `hostname,gsocket_secret`
- Download template and use it as a base

### "File must be UTF-8"

**Cause**: CSV file uses non-UTF-8 encoding

**Solution**:
- Save CSV file with UTF-8 encoding
- In Excel: Save As → CSV UTF-8
- In LibreOffice: Use "Unicode (UTF-8)" character set

### "Missing required fields"

**Cause**: Row has empty hostname or gsocket_secret

**Solution**:
- Ensure every data row has values for hostname and gsocket_secret
- Remove empty rows from CSV

## Tips and Best Practices

### 1. Generate Secrets Securely

Use `gs-netcat -g` to generate cryptographically secure secrets:

```bash
gs-netcat -g
```

Or use the web interface "Generate Secret" button for each host.

### 2. Test with Small Files First

Before importing hundreds of hosts:
- Test with 2-3 hosts first
- Verify import works correctly
- Then import the full list

### 3. Backup Before Import

Import doesn't overwrite existing hosts, but it's good practice to backup:

```bash
cp data/c2panel.db data/c2panel.db.backup
```

### 4. Use Consistent Tag Format

Choose one tag separator and stick with it:
- Recommended: semicolons `prod;web;nginx`
- Also works: commas `prod,web,nginx`

### 5. Validate CSV Format

Before importing:
- Open in a text editor to verify format
- Check for extra commas or quotes
- Ensure UTF-8 encoding

### 6. Handle Special Characters

If your data contains commas in descriptions:

```csv
hostname,ip_address,gsocket_secret,custom_gsrn_server,description,tags
web-01,192.168.1.10,secret123,,"Production server, primary",prod;web
```

Use quotes around fields with commas.

## Bulk Operations

### Importing Large Numbers of Hosts

For hundreds/thousands of hosts:

1. **Split into batches**
   - Import 100-200 hosts at a time
   - Easier to troubleshoot errors

2. **Use consistent naming**
   - `web-01`, `web-02`, etc.
   - `db-prod-01`, `db-dev-01`, etc.

3. **Group by tags**
   - All production servers: `prod`
   - All web servers: `web`
   - Makes filtering easier

### Generating CSV from Other Systems

If migrating from another C2 system:

```bash
# Example: Export from database
sqlite3 old_db.db "SELECT hostname, ip, secret FROM hosts" -csv -header > hosts.csv

# Example: Generate from script
echo "hostname,ip_address,gsocket_secret,custom_gsrn_server,description,tags" > hosts.csv
for i in {1..10}; do
    echo "server-$i,192.168.1.$i,$(gs-netcat -g),,Server $i,prod" >> hosts.csv
done
```

## API Documentation

### Endpoint

```
POST /api/hosts/import/csv
```

### Headers

```
Authorization: Bearer {token}
Content-Type: multipart/form-data
```

### Request Body

- **file** - CSV file (multipart form data)

### Response

```json
{
    "success": true,
    "message": "Import completed: 8 imported, 2 skipped",
    "results": {
        "total": 10,
        "imported": 8,
        "skipped": 2,
        "errors": [
            "Row 3 (db-server-01): Hostname already exists",
            "Row 7 (invalid-host): Invalid hostname format"
        ]
    }
}
```

### Error Responses

**400 Bad Request** - Invalid CSV format or validation errors

**401 Unauthorized** - Missing or invalid authentication token

**500 Internal Server Error** - Server error during import

## Example: Complete Workflow

### 1. Prepare CSV File

Create `hosts.csv`:

```csv
hostname,ip_address,gsocket_secret,custom_gsrn_server,description,tags
web-prod-01,192.168.1.10,$(gs-netcat -g),,Production web server,prod;web
web-prod-02,192.168.1.11,$(gs-netcat -g),,Production web server,prod;web
db-prod-01,192.168.1.20,$(gs-netcat -g),,Production database,prod;db
```

### 2. Generate Secrets

```bash
# Replace $(gs-netcat -g) with actual secrets
for i in {1..3}; do
    SECRET=$(gs-netcat -g)
    echo "Generated secret $i: $SECRET"
done
```

### 3. Import via Web Interface

1. Open C2 Panel → Hosts
2. Click "Import CSV"
3. Select `hosts.csv`
4. Click "Import"
5. Review results

### 4. Verify Import

- Check Hosts list
- Verify all hosts appear
- Test connection to a few hosts

## Troubleshooting

### Import Hangs or Times Out

**Cause**: Very large CSV file (thousands of rows)

**Solution**:
- Split into smaller files (100-200 rows each)
- Import sequentially

### All Rows Skipped

**Cause**: Incorrect CSV format or encoding

**Solution**:
1. Download template
2. Copy your data to template
3. Save as CSV UTF-8
4. Try again

### Some Rows Import, Others Don't

**Cause**: Validation errors on specific rows

**Solution**:
- Check error messages in import results
- Fix problematic rows
- Re-import only failed rows

## Security Notes

1. **Secrets are encrypted** - All gsocket secrets are encrypted before storage
2. **Authentication required** - Must be logged in to import
3. **Validation enforced** - All inputs are validated before import
4. **Logs maintained** - Import operations are logged for audit

## Related Documentation

- [Host Setup Guide](HOST_SETUP_GUIDE.md) - How to configure individual hosts
- [GSocket Architecture](GSOCKET_ARCHITECTURE.md) - Understanding GSocket connections
- [Migration Guide](MIGRATION_GUIDE.md) - Database migrations and updates
