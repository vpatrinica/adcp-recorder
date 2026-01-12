# ADCP Recorder - Configuration Guide

This guide provides detailed information about configuring the ADCP Recorder system for optimal performance and reliability.

## Table of Contents

- [Configuration Overview](#configuration-overview)
- [Configuration File](#configuration-file)
- [Configuration Parameters](#configuration-parameters)
- [Environment Variables](#environment-variables)
- [Serial Port Configuration](#serial-port-configuration)
- [Database Configuration](#database-configuration)
- [Logging Configuration](#logging-configuration)
- [Platform-Specific Settings](#platform-specific-settings)
- [Configuration Examples](#configuration-examples)
- [Validation and Testing](#validation-and-testing)

---

## Configuration Overview

The ADCP Recorder uses a hierarchical configuration system:

1. **Default values** - Built-in defaults
2. **Configuration file** - Persistent settings in `~/.adcp-recorder/config.json`
3. **Environment variables** - Runtime overrides with `ADCP_RECORDER_` prefix
4. **Command-line options** - Immediate updates via CLI

Configuration precedence (highest to lowest):
```
Command-line > Environment Variables > Configuration File > Defaults
```

---

## Configuration File

### Location

The configuration file is stored at:

- **Linux/macOS**: `~/.adcp-recorder/config.json`
- **Windows**: `C:\Users\<username>\.adcp-recorder\config.json`

### File Format

The configuration file uses JSON format:

```json
{
    "serial_port": "/dev/ttyUSB0",
    "baudrate": 9600,
    "timeout": 1.0,
    "output_dir": "/home/user/adcp_data",
    "log_level": "INFO",
    "db_path": null
}
```

### Creating Configuration

The configuration file is automatically created when you first use the `configure` command:

```bash
adcp-recorder configure --port /dev/ttyUSB0 --baud 9600 --output ~/adcp_data
```

### Manual Editing

You can manually edit the configuration file:

```bash
# Linux/macOS
nano ~/.adcp-recorder/config.json

# Windows
notepad %USERPROFILE%\.adcp-recorder\config.json
```

> [!WARNING]
> Ensure the JSON syntax is valid after manual edits. Invalid JSON will cause the recorder to fall back to default values.

---

## Configuration Parameters

### Core Parameters

#### `serial_port`

- **Type**: String
- **Default**: `/dev/ttyUSB0` (Linux), `COM1` (Windows)
- **Description**: Serial port device path
- **Examples**:
  - Linux: `/dev/ttyUSB0`, `/dev/ttyACM0`, `/dev/ttyS0`
  - Windows: `COM1`, `COM3`, `COM10`

```bash
adcp-recorder configure --port /dev/ttyUSB0
```

#### `baudrate`

- **Type**: Integer
- **Default**: `9600`
- **Description**: Serial communication baud rate
- **Valid Values**: `300`, `1200`, `2400`, `4800`, `9600`, `19200`, `38400`, `57600`, `115200`
- **Common ADCP Rates**: `9600`, `19200`, `38400`, `115200`

```bash
adcp-recorder configure --baud 115200
```

> [!TIP]
> Match the baud rate to your ADCP instrument's configuration. Consult your instrument manual for the correct setting.

#### `timeout`

- **Type**: Float (seconds)
- **Default**: `1.0`
- **Description**: Serial port read timeout
- **Range**: `0.1` to `10.0` seconds
- **Recommendation**: `1.0` for most applications

```json
{
    "timeout": 1.0
}
```

#### `output_dir`

- **Type**: String (path)
- **Default**: `~/adcp_data` (Linux), `%USERPROFILE%\adcp_data` (Windows)
- **Description**: Base directory for data storage
- **Requirements**: 
  - Must be writable
  - Should have sufficient disk space
  - Will be created if it doesn't exist

```bash
adcp-recorder configure --output /data/adcp
```

**Directory Structure:**
```
output_dir/
├── adcp.duckdb          # Main database file
├── adcp.duckdb.wal      # Write-ahead log
├── PNORI/               # Daily files per message type
│   ├── 2026-01-12.csv
│   └── 2026-01-13.csv
├── PNORS/
├── PNORC/
└── errors/              # Binary error data
    └── 2026-01-12.bin
```

#### `log_level`

- **Type**: String
- **Default**: `INFO`
- **Description**: Logging verbosity level
- **Valid Values**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

```bash
# Enable debug logging
adcp-recorder configure --debug

# Disable debug logging
adcp-recorder configure --no-debug
```

**Log Levels:**
- `DEBUG`: Detailed diagnostic information (verbose)
- `INFO`: General informational messages (recommended)
- `WARNING`: Warning messages for potential issues
- `ERROR`: Error messages for failures
- `CRITICAL`: Critical errors requiring immediate attention

#### `db_path`

- **Type**: String (path) or `null`
- **Default**: `null` (uses `{output_dir}/adcp.duckdb`)
- **Description**: Custom database file location
- **Use Case**: Separate database from data files

```json
{
    "db_path": "/var/lib/adcp/database.duckdb"
}
```

---

## Environment Variables

Environment variables override configuration file settings. All variables use the `ADCP_RECORDER_` prefix.

### Available Environment Variables

| Variable | Type | Example |
|----------|------|---------|
| `ADCP_RECORDER_SERIAL_PORT` | String | `/dev/ttyUSB0` |
| `ADCP_RECORDER_BAUDRATE` | Integer | `115200` |
| `ADCP_RECORDER_TIMEOUT` | Float | `2.0` |
| `ADCP_RECORDER_OUTPUT_DIR` | String | `/data/adcp` |
| `ADCP_RECORDER_LOG_LEVEL` | String | `DEBUG` |
| `ADCP_RECORDER_DB_PATH` | String | `/var/lib/adcp.duckdb` |

### Setting Environment Variables

**Linux/macOS (bash/zsh):**
```bash
# Temporary (current session)
export ADCP_RECORDER_SERIAL_PORT=/dev/ttyUSB1
export ADCP_RECORDER_BAUDRATE=115200

# Permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export ADCP_RECORDER_OUTPUT_DIR=/data/adcp' >> ~/.bashrc
source ~/.bashrc
```

**Windows (Command Prompt):**
```cmd
REM Temporary (current session)
set ADCP_RECORDER_SERIAL_PORT=COM3
set ADCP_RECORDER_BAUDRATE=115200

REM Permanent (system-wide, requires admin)
setx ADCP_RECORDER_OUTPUT_DIR "C:\ADCP_Data"
```

**Windows (PowerShell):**
```powershell
# Temporary (current session)
$env:ADCP_RECORDER_SERIAL_PORT = "COM3"
$env:ADCP_RECORDER_BAUDRATE = "115200"

# Permanent (user-level)
[Environment]::SetEnvironmentVariable("ADCP_RECORDER_OUTPUT_DIR", "C:\ADCP_Data", "User")
```

### Use Cases for Environment Variables

1. **Docker/Container Deployments**: Pass configuration without mounting config files
2. **CI/CD Pipelines**: Override settings for testing
3. **Multi-Instance Deployments**: Different settings per instance
4. **Security**: Keep sensitive paths out of version control

---

## Serial Port Configuration

### Finding Your Serial Port

**Linux:**
```bash
# List all serial devices
ls -l /dev/tty{USB,ACM}*

# Using adcp-recorder
adcp-recorder list-ports

# Monitor kernel messages when plugging device
dmesg | grep tty
```

**Windows:**
```cmd
REM Using adcp-recorder
adcp-recorder list-ports

REM Or check Device Manager
devmgmt.msc
```

### Serial Port Permissions (Linux)

```bash
# Check current permissions
ls -l /dev/ttyUSB0

# Add user to dialout group
sudo usermod -a -G dialout $USER

# Verify group membership
groups

# Apply changes (logout/login or use newgrp)
newgrp dialout
```

### Common Serial Settings

| ADCP Model | Baud Rate | Data Bits | Parity | Stop Bits |
|------------|-----------|-----------|--------|-----------|
| Nortek Signature | 115200 | 8 | None | 1 |
| Nortek AWAC | 9600 | 8 | None | 1 |
| Generic ADCP | 9600 | 8 | None | 1 |

> [!NOTE]
> The ADCP Recorder uses 8 data bits, no parity, and 1 stop bit (8N1) by default. These are standard for NMEA communication and cannot be changed.

---

## Database Configuration

### Database Location

By default, the database is stored in `{output_dir}/adcp.duckdb`. You can customize this:

```json
{
    "output_dir": "/data/adcp",
    "db_path": "/var/lib/adcp/database.duckdb"
}
```

### Database Performance

**For High-Throughput Scenarios:**

1. **Use SSD Storage**: Place database on SSD for better I/O performance
2. **Separate Database and Data Files**: Use different disks
3. **Increase System Resources**: Allocate more RAM if processing large volumes

**Database Maintenance:**

```bash
# Check database size
ls -lh ~/adcp_data/adcp.duckdb

# Compact database (requires stopping recorder)
# Connect with DuckDB CLI
duckdb ~/adcp_data/adcp.duckdb
# Run: VACUUM;
```

### Database Schema

The database contains the following tables:

- `raw_lines` - All received NMEA sentences
- `errors` - Parse errors and binary data
- Message-specific tables: `pnori`, `pnors`, `pnorc`, `pnorh3`, `pnorh4`, `pnora`, `pnorw`, `pnorb`, `pnore`, `pnorf`, `pnorwd`

See [Database Schema Documentation](../implementation/duckdb/schemas.md) for details.

---

## Logging Configuration

### Log Levels

Configure logging verbosity based on your needs:

**Production (Recommended):**
```bash
adcp-recorder configure --no-debug
# Sets log_level to INFO
```

**Development/Troubleshooting:**
```bash
adcp-recorder configure --debug
# Sets log_level to DEBUG
```

### Log Output

Logs are written to:
- **Console (stdout)**: When running interactively
- **System logs**: When running as a service
  - Linux: `journalctl -u adcp-recorder -f`
  - Windows: Event Viewer → Application logs

### Log Format

```
2026-01-12 22:30:15,123 - adcp_recorder.serial.producer - INFO - Connected to /dev/ttyUSB0
2026-01-12 22:30:15,456 - adcp_recorder.serial.consumer - INFO - Consumer started
2026-01-12 22:30:16,789 - adcp_recorder.parsers.pnors - DEBUG - Parsed PNORS: heading=45.2°
```

### Custom Logging (Advanced)

For advanced logging configuration, you can modify the logging setup in your deployment:

```python
import logging
from adcp_recorder.config import RecorderConfig
from adcp_recorder.core.recorder import AdcpRecorder

# Custom logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/adcp-recorder.log'),
        logging.StreamHandler()
    ]
)

config = RecorderConfig.load()
recorder = AdcpRecorder(config)
recorder.run_blocking()
```

---

## Platform-Specific Settings

### Linux

**Recommended Configuration:**
```json
{
    "serial_port": "/dev/ttyUSB0",
    "baudrate": 9600,
    "timeout": 1.0,
    "output_dir": "/var/lib/adcp-recorder/data",
    "log_level": "INFO",
    "db_path": null
}
```

**Service User:**
```bash
# Create dedicated service user
sudo useradd -r -s /bin/false adcp-recorder
sudo usermod -a -G dialout adcp-recorder

# Set ownership
sudo chown -R adcp-recorder:adcp-recorder /var/lib/adcp-recorder
```

### Windows

**Recommended Configuration:**
```json
{
    "serial_port": "COM3",
    "baudrate": 9600,
    "timeout": 1.0,
    "output_dir": "C:\\ADCP_Data",
    "log_level": "INFO",
    "db_path": null
}
```

> [!IMPORTANT]
> Use double backslashes (`\\`) in JSON paths on Windows, or use forward slashes (`/`).

---

## Configuration Examples

### Example 1: Basic Setup

```bash
# Configure for basic operation
adcp-recorder configure \
    --port /dev/ttyUSB0 \
    --baud 9600 \
    --output ~/adcp_data

# Verify
adcp-recorder status
```

### Example 2: High-Speed ADCP

```bash
# Configure for high-speed instrument
adcp-recorder configure \
    --port /dev/ttyUSB0 \
    --baud 115200 \
    --output /data/adcp

# Enable debug logging for initial testing
adcp-recorder configure --debug
```

### Example 3: Production Deployment

```json
{
    "serial_port": "/dev/ttyUSB0",
    "baudrate": 38400,
    "timeout": 1.0,
    "output_dir": "/var/lib/adcp-recorder/data",
    "log_level": "INFO",
    "db_path": "/var/lib/adcp-recorder/adcp.duckdb"
}
```

### Example 4: Multi-Instance Setup

**Instance 1 (Port 1):**
```bash
export ADCP_RECORDER_SERIAL_PORT=/dev/ttyUSB0
export ADCP_RECORDER_OUTPUT_DIR=/data/adcp1
adcp-recorder start
```

**Instance 2 (Port 2):**
```bash
export ADCP_RECORDER_SERIAL_PORT=/dev/ttyUSB1
export ADCP_RECORDER_OUTPUT_DIR=/data/adcp2
adcp-recorder start
```

### Example 5: Docker Container

```dockerfile
FROM python:3.9-slim

RUN pip install adcp-recorder

ENV ADCP_RECORDER_SERIAL_PORT=/dev/ttyUSB0
ENV ADCP_RECORDER_BAUDRATE=9600
ENV ADCP_RECORDER_OUTPUT_DIR=/data
ENV ADCP_RECORDER_LOG_LEVEL=INFO

CMD ["adcp-recorder", "start"]
```

---

## Validation and Testing

### Verify Configuration

```bash
# Check current configuration
adcp-recorder status

# Expected output:
# ADCP Recorder Status
# ====================
# Configuration File: /home/user/.adcp-recorder/config.json
# Serial Port:       /dev/ttyUSB0
# Baud Rate:         9600
# Output Directory:  /home/user/adcp_data
# Log Level:         INFO
```

### Test Serial Connection

```bash
# List available ports
adcp-recorder list-ports

# Test connection (will attempt to open port)
adcp-recorder start
# Press Ctrl+C after verifying connection
```

### Validate Output Directory

```bash
# Check directory exists and is writable
ls -ld ~/adcp_data
touch ~/adcp_data/test.txt && rm ~/adcp_data/test.txt
```

### Test Database Creation

```bash
# Start recorder briefly
adcp-recorder start
# Press Ctrl+C after a few seconds

# Verify database was created
ls -lh ~/adcp_data/adcp.duckdb

# Query database
duckdb ~/adcp_data/adcp.duckdb "SELECT COUNT(*) FROM raw_lines;"
```

---

## Troubleshooting Configuration

### Configuration Not Persisting

**Issue**: Changes don't persist after restart

**Solution**:
```bash
# Verify config file location
adcp-recorder status | grep "Configuration File"

# Check file permissions
ls -l ~/.adcp-recorder/config.json

# Manually verify content
cat ~/.adcp-recorder/config.json
```

### Environment Variables Not Working

**Issue**: Environment variables not being applied

**Solution**:
```bash
# Verify environment variable is set
echo $ADCP_RECORDER_SERIAL_PORT

# Check if variable is being read
adcp-recorder status

# Ensure variable name is correct (case-sensitive)
env | grep ADCP_RECORDER
```

### Invalid Configuration File

**Issue**: "Could not load config, using defaults"

**Solution**:
```bash
# Validate JSON syntax
python3 -m json.tool ~/.adcp-recorder/config.json

# If invalid, recreate
rm ~/.adcp-recorder/config.json
adcp-recorder configure --port /dev/ttyUSB0 --baud 9600
```

---

## Next Steps

- **Start using the recorder**: See [USAGE.md](USAGE.md)
- **Explore examples**: See [EXAMPLES.md](EXAMPLES.md)
- **Deploy as service**: See [DEPLOYMENT.md](../deployment/DEPLOYMENT.md)
- **Query your data**: See [Query Examples](../examples/query-examples.md)

---

**Configuration complete!** Your ADCP Recorder is ready for operation.
