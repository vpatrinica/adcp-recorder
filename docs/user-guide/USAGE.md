# ADCP Recorder - Usage Guide

This guide provides comprehensive instructions for using the ADCP Recorder system in daily operations.

## Table of Contents

- [Quick Start](#quick-start)
- [CLI Command Reference](#cli-command-reference)
- [Common Workflows](#common-workflows)
- [Data Access and Querying](#data-access-and-querying)
- [File Export Formats](#file-export-formats)
- [Monitoring and Health Checks](#monitoring-and-health-checks)
- [Error Handling and Recovery](#error-handling-and-recovery)
- [Best Practices](#best-practices)
- [Performance Tuning](#performance-tuning)

---

## Quick Start

### First-Time Setup

```bash
# 1. List available serial ports
adcp-recorder list-ports

# 2. Configure the recorder
adcp-recorder configure --port /dev/ttyUSB0 --baud 9600 --output ~/adcp_data

# 3. Check configuration
adcp-recorder status

# 4. Start recording
adcp-recorder start
```

Press `Ctrl+C` to stop the recorder.

### Typical Daily Usage

```bash
# Start recording (runs in foreground)
adcp-recorder start

# Or run as background service (see DEPLOYMENT.md)
sudo systemctl start adcp-recorder  # Linux
```

---

## CLI Command Reference

### `adcp-recorder --help`

Display help information and list all available commands.

```bash
adcp-recorder --help
```

**Output:**
```
Usage: adcp-recorder [OPTIONS] COMMAND [ARGS]...

  ADCP Recorder Control Plane

Options:
  --help  Show this message and exit.

Commands:
  configure        Update configuration settings.
  generate-service Generate OS service configuration templates.
  list-ports       List available serial ports.
  start            Start the recorder with current configuration.
  status           Show current configuration and status.
```

---

### `list-ports`

List all available serial ports on the system.

**Syntax:**
```bash
adcp-recorder list-ports
```

**Example Output:**
```
Found 2 ports:
  /dev/ttyUSB0: USB Serial Port (USB VID:PID=0403:6001)
  /dev/ttyACM0: Arduino Uno (USB VID:PID=2341:0043)
```

**Use Cases:**
- Identify the correct serial port for your ADCP
- Verify USB-to-serial adapter is recognized
- Troubleshoot connection issues

---

### `configure`

Update configuration settings.

**Syntax:**
```bash
adcp-recorder configure [OPTIONS]
```

**Options:**
- `--port TEXT` - Serial port device (e.g., `/dev/ttyUSB0`, `COM3`)
- `--baud INTEGER` - Baud rate (e.g., `9600`, `115200`)
- `--output TEXT` - Output directory path
- `--debug` / `--no-debug` - Enable/disable debug logging

**Examples:**

```bash
# Set serial port
adcp-recorder configure --port /dev/ttyUSB0

# Set baud rate
adcp-recorder configure --baud 115200

# Set output directory
adcp-recorder configure --output /data/adcp

# Enable debug logging
adcp-recorder configure --debug

# Configure multiple settings at once
adcp-recorder configure --port /dev/ttyUSB0 --baud 9600 --output ~/adcp_data

# View current configuration (no options)
adcp-recorder configure
```

**Output:**
```
Configuration updated in /home/user/.adcp-recorder/config.json
  Port: /dev/ttyUSB0
  Baud: 9600
  Output: /home/user/adcp_data
  Level: INFO
```

---

### `status`

Show current configuration and perform system checks.

**Syntax:**
```bash
adcp-recorder status
```

**Example Output:**
```
ADCP Recorder Status
====================
Configuration File: /home/user/.adcp-recorder/config.json
Serial Port:       /dev/ttyUSB0
Baud Rate:         9600
Output Directory:  /home/user/adcp_data
Log Level:         INFO

System Checks:
  [OK] Output directory exists
  [OK] Serial port /dev/ttyUSB0 found
```

**Use Cases:**
- Verify configuration before starting
- Troubleshoot setup issues
- Check system readiness

---

### `start`

Start the recorder with the current configuration.

**Syntax:**
```bash
adcp-recorder start
```

**Example Output:**
```
Starting recorder on /dev/ttyUSB0 at 9600 baud...
Data will be saved to /home/user/adcp_data
Press Ctrl+C to stop.

2026-01-12 22:30:15,123 - adcp_recorder.serial.producer - INFO - Connected to /dev/ttyUSB0
2026-01-12 22:30:15,456 - adcp_recorder.serial.consumer - INFO - Consumer started
2026-01-12 22:30:16,789 - adcp_recorder.parsers.pnors - INFO - Parsed PNORS message
```

**Stopping:**
Press `Ctrl+C` to gracefully stop the recorder.

**Behavior:**
- Opens serial port connection
- Initializes database
- Starts producer/consumer threads
- Continuously reads and processes NMEA data
- Writes to database and daily CSV files
- Runs until interrupted

---

### `generate-service`

Generate OS-specific service configuration templates.

**Syntax:**
```bash
adcp-recorder generate-service --platform {linux|windows} [--out DIRECTORY]
```

**Options:**
- `--platform` - Target platform (`linux` or `windows`) **[Required]**
- `--out` - Output directory (default: current directory)

**Examples:**

```bash
# Generate Linux systemd service file
adcp-recorder generate-service --platform linux

# Generate Windows service installer
adcp-recorder generate-service --platform windows

# Output to specific directory
adcp-recorder generate-service --platform linux --out /tmp
```

**Output:**
- **Linux**: `adcp-recorder.service` (systemd unit file)
- **Windows**: `install_service.bat` (service installation script)

See [DEPLOYMENT.md](../deployment/DEPLOYMENT.md) for service installation instructions.

---

## Common Workflows

### Workflow 1: Initial Setup and Testing

```bash
# Step 1: Find your serial port
adcp-recorder list-ports

# Step 2: Configure the recorder
adcp-recorder configure --port /dev/ttyUSB0 --baud 9600 --output ~/adcp_test

# Step 3: Enable debug logging for testing
adcp-recorder configure --debug

# Step 4: Verify configuration
adcp-recorder status

# Step 5: Start recorder for a test run
adcp-recorder start
# Let it run for 1-2 minutes, then press Ctrl+C

# Step 6: Verify data was collected
ls -lh ~/adcp_test/
duckdb ~/adcp_test/adcp.duckdb "SELECT COUNT(*) FROM raw_lines;"

# Step 7: Disable debug logging for production
adcp-recorder configure --no-debug
```

---

### Workflow 2: Production Deployment

```bash
# Step 1: Configure for production
adcp-recorder configure \
    --port /dev/ttyUSB0 \
    --baud 9600 \
    --output /var/lib/adcp-recorder/data \
    --no-debug

# Step 2: Generate service file
adcp-recorder generate-service --platform linux --out /tmp

# Step 3: Install as system service
sudo cp /tmp/adcp-recorder.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable adcp-recorder
sudo systemctl start adcp-recorder

# Step 4: Monitor service
sudo systemctl status adcp-recorder
sudo journalctl -u adcp-recorder -f
```

See [DEPLOYMENT.md](../deployment/DEPLOYMENT.md) for complete deployment instructions.

---

### Workflow 3: Data Collection and Export

```bash
# Start recording
adcp-recorder start

# Data is automatically saved to:
# - Database: ~/adcp_data/adcp.duckdb
# - Daily CSV files: ~/adcp_data/{MESSAGE_TYPE}/{YYYY-MM-DD}.csv

# After collection, query the database
duckdb ~/adcp_data/adcp.duckdb

# Or access daily CSV files
cat ~/adcp_data/PNORS/2026-01-12.csv
```

---

### Workflow 4: Troubleshooting Connection Issues

```bash
# Step 1: Verify serial port exists
adcp-recorder list-ports

# Step 2: Check permissions (Linux)
ls -l /dev/ttyUSB0
groups | grep dialout

# Step 3: Enable debug logging
adcp-recorder configure --debug

# Step 4: Start and observe logs
adcp-recorder start

# Step 5: Check for errors
# Look for connection errors, timeout messages, or parse failures

# Step 6: Try different baud rate if needed
adcp-recorder configure --baud 115200
adcp-recorder start
```

---

### Workflow 5: Changing Configuration

```bash
# Stop the recorder if running (Ctrl+C or stop service)

# Update configuration
adcp-recorder configure --port /dev/ttyUSB1 --baud 115200

# Verify changes
adcp-recorder status

# Restart recorder
adcp-recorder start
```

---

## Data Access and Querying

### Database Access

The recorder stores all data in a DuckDB database located at `{output_dir}/adcp.duckdb`.

**Connect to Database:**
```bash
# Using DuckDB CLI
duckdb ~/adcp_data/adcp.duckdb

# Using Python
python3 -c "import duckdb; conn = duckdb.connect('~/adcp_data/adcp.duckdb'); print(conn.execute('SHOW TABLES').fetchall())"
```

### Common Queries

**Count total messages:**
```sql
SELECT COUNT(*) FROM raw_lines;
```

**View recent messages:**
```sql
SELECT * FROM raw_lines ORDER BY timestamp DESC LIMIT 10;
```

**Count by message type:**
```sql
SELECT 
    SUBSTRING(line, 2, POSITION(',' IN line) - 2) AS message_type,
    COUNT(*) AS count
FROM raw_lines
WHERE valid = true
GROUP BY message_type
ORDER BY count DESC;
```

**Query specific message type (e.g., PNORS):**
```sql
SELECT * FROM pnors ORDER BY timestamp DESC LIMIT 10;
```

**Find errors:**
```sql
SELECT * FROM errors ORDER BY timestamp DESC LIMIT 10;
```

**Time-based queries:**
```sql
-- Messages from last hour
SELECT * FROM raw_lines 
WHERE timestamp > NOW() - INTERVAL 1 HOUR;

-- Messages from specific date
SELECT * FROM pnors 
WHERE DATE(timestamp) = '2026-01-12';
```

**Aggregate statistics:**
```sql
-- Average heading from PNORS messages
SELECT AVG(heading) AS avg_heading FROM pnors;

-- Temperature statistics
SELECT 
    MIN(temperature) AS min_temp,
    MAX(temperature) AS max_temp,
    AVG(temperature) AS avg_temp
FROM pnors
WHERE temperature IS NOT NULL;
```

See [Query Examples](../examples/query-examples.md) for more advanced queries.

---

## File Export Formats

### Daily CSV Files

The recorder automatically exports data to daily CSV files organized by message type.

**Directory Structure:**
```
output_dir/
├── PNORI/
│   ├── 2026-01-12.csv
│   └── 2026-01-13.csv
├── PNORS/
│   ├── 2026-01-12.csv
│   └── 2026-01-13.csv
├── PNORC/
│   └── 2026-01-12.csv
└── errors/
    └── 2026-01-12.bin
```

**CSV Format:**

Each CSV file contains parsed message data with headers:

```csv
timestamp,heading,pitch,roll,temperature,pressure,status
2026-01-12 10:30:15.123,45.2,1.5,-0.8,15.3,1013.2,A
2026-01-12 10:30:16.456,45.3,1.6,-0.7,15.3,1013.2,A
```

**Accessing CSV Files:**

```bash
# View today's PNORS data
cat ~/adcp_data/PNORS/$(date +%Y-%m-%d).csv

# Import into spreadsheet
libreoffice ~/adcp_data/PNORS/2026-01-12.csv

# Process with Python
python3 -c "import pandas as pd; df = pd.read_csv('~/adcp_data/PNORS/2026-01-12.csv'); print(df.head())"
```

### Error Files

Binary data and parse errors are saved to `errors/{date}.bin` for later analysis.

---

## Monitoring and Health Checks

### Real-Time Monitoring

**Monitor logs (foreground mode):**
```bash
adcp-recorder start
# Logs appear in console
```

**Monitor service logs (Linux):**
```bash
# Follow logs in real-time
sudo journalctl -u adcp-recorder -f

# View recent logs
sudo journalctl -u adcp-recorder -n 100

# View logs since specific time
sudo journalctl -u adcp-recorder --since "1 hour ago"
```

**Monitor service logs (Windows):**
```powershell
# Open Event Viewer
eventvwr.msc

# Navigate to: Windows Logs → Application
# Filter by source: adcp-recorder
```

### Health Indicators

**Good Health:**
```
INFO - Connected to /dev/ttyUSB0
INFO - Consumer started
INFO - Parsed PNORS message
INFO - Parsed PNORC message
```

**Warning Signs:**
```
WARNING - Producer thread is dead!
WARNING - No data received in 60 seconds
WARNING - Parse error: Invalid checksum
```

**Critical Issues:**
```
ERROR - Failed to open serial port
ERROR - Database locked
ERROR - Recorder stopped unexpectedly
```

### Automated Monitoring

**Check if service is running:**
```bash
# Linux
systemctl is-active adcp-recorder

# Windows
sc query adcp-recorder
```

**Monitor data collection rate:**
```bash
# Count messages in last minute
duckdb ~/adcp_data/adcp.duckdb "
SELECT COUNT(*) 
FROM raw_lines 
WHERE timestamp > NOW() - INTERVAL 1 MINUTE;"
```

**Check disk space:**
```bash
# Linux
df -h ~/adcp_data

# Windows
dir C:\adcp_data
```

---

## Error Handling and Recovery

### Common Errors and Solutions

#### Serial Port Disconnected

**Symptoms:**
```
ERROR - Failed to read from serial port
WARNING - Connection lost, attempting reconnect...
```

**Recovery:**
The recorder automatically attempts to reconnect. If manual intervention is needed:

```bash
# Stop recorder
sudo systemctl stop adcp-recorder  # or Ctrl+C

# Check physical connection
# Replug USB cable if needed

# Verify port
adcp-recorder list-ports

# Restart recorder
sudo systemctl start adcp-recorder
```

#### Database Locked

**Symptoms:**
```
ERROR - Database is locked
```

**Recovery:**
```bash
# Stop all recorder instances
sudo systemctl stop adcp-recorder
pkill -f adcp-recorder

# Remove lock files
rm ~/adcp_data/*.lock

# Restart
sudo systemctl start adcp-recorder
```

#### Disk Full

**Symptoms:**
```
ERROR - No space left on device
```

**Recovery:**
```bash
# Check disk usage
df -h ~/adcp_data

# Archive old data
tar -czf adcp_archive_$(date +%Y%m%d).tar.gz ~/adcp_data/PNORS/2025-*.csv
rm ~/adcp_data/PNORS/2025-*.csv

# Or move to external storage
mv ~/adcp_data/PNORS/2025-*.csv /mnt/archive/
```

#### Parse Errors

**Symptoms:**
```
WARNING - Parse error: Invalid checksum
WARNING - Binary data detected
```

**Investigation:**
```bash
# Check error log
duckdb ~/adcp_data/adcp.duckdb "SELECT * FROM errors ORDER BY timestamp DESC LIMIT 10;"

# View binary error file
hexdump -C ~/adcp_data/errors/$(date +%Y-%m-%d).bin | head -20
```

**Resolution:**
- Parse errors are logged but don't stop the recorder
- Binary data is saved for later analysis
- If errors are frequent, check ADCP configuration or cable quality

---

## Best Practices

### 1. Use a Dedicated Output Directory

```bash
# Good: Dedicated directory
adcp-recorder configure --output /var/lib/adcp-recorder/data

# Avoid: Shared or temporary directories
# adcp-recorder configure --output /tmp
```

### 2. Run as a System Service

For production deployments, always run as a system service for automatic startup and recovery.

See [DEPLOYMENT.md](../deployment/DEPLOYMENT.md).

### 3. Monitor Disk Space

```bash
# Set up automated monitoring
# Add to cron (Linux):
0 * * * * df -h /var/lib/adcp-recorder | mail -s "ADCP Disk Usage" admin@example.com
```

### 4. Regular Backups

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d)
tar -czf /backup/adcp_$DATE.tar.gz ~/adcp_data/
find /backup -name "adcp_*.tar.gz" -mtime +30 -delete
```

### 5. Use Appropriate Log Level

- **Production**: `INFO` (default)
- **Troubleshooting**: `DEBUG`
- **Critical systems**: `WARNING` or `ERROR`

### 6. Validate Configuration Before Deployment

```bash
# Always test configuration
adcp-recorder status
adcp-recorder start  # Test for 1-2 minutes
# Ctrl+C
```

### 7. Document Your Setup

Keep a record of:
- Serial port configuration
- ADCP model and settings
- Deployment location
- Contact information

---

## Performance Tuning

### High-Throughput Scenarios

For ADCPs generating high data rates:

**1. Use SSD Storage:**
```bash
adcp-recorder configure --output /mnt/ssd/adcp_data
```

**2. Increase Queue Size (Advanced):**

Modify `adcp_recorder/core/recorder.py`:
```python
self.queue = Queue(maxsize=5000)  # Default: 1000
```

**3. Monitor System Resources:**
```bash
# CPU and memory usage
top -p $(pgrep -f adcp-recorder)

# I/O statistics
iostat -x 5
```

### Low-Resource Systems

For embedded systems or low-power devices:

**1. Disable Debug Logging:**
```bash
adcp-recorder configure --no-debug
```

**2. Reduce Database Writes:**

Consider archiving old data more frequently to keep database size manageable.

**3. Use External Storage:**
```bash
# Mount external drive
sudo mount /dev/sda1 /mnt/external

# Configure output
adcp-recorder configure --output /mnt/external/adcp_data
```

---

## Next Steps

- **Explore examples**: See [EXAMPLES.md](EXAMPLES.md)
- **Deploy as service**: See [DEPLOYMENT.md](../deployment/DEPLOYMENT.md)
- **Query your data**: See [Query Examples](../examples/query-examples.md)
- **Advanced configuration**: See [CONFIGURATION.md](CONFIGURATION.md)

---

**Happy recording!** Your ADCP data is being captured reliably.
