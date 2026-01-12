# ADCP Recorder - Examples

This guide provides practical, real-world examples for using the ADCP Recorder system.

## Table of Contents

- [Basic Setup Examples](#basic-setup-examples)
- [Advanced Configuration](#advanced-configuration)
- [Data Analysis Queries](#data-analysis-queries)
- [Integration Examples](#integration-examples)
- [Troubleshooting Scenarios](#troubleshooting-scenarios)
- [Automation Examples](#automation-examples)

---

## Basic Setup Examples

### Example 1: First-Time Setup on Linux

```bash
# Install the package
pip install adcp-recorder

# Find your ADCP serial port
adcp-recorder list-ports
# Output: Found 1 ports:
#   /dev/ttyUSB0: USB Serial Port (USB VID:PID=0403:6001)

# Configure the recorder
adcp-recorder configure \
    --port /dev/ttyUSB0 \
    --baud 9600 \
    --output ~/adcp_data

# Verify configuration
adcp-recorder status
# Output: ADCP Recorder Status
#         ====================
#         Configuration File: /home/user/.adcp-recorder/config.json
#         Serial Port:       /dev/ttyUSB0
#         Baud Rate:         9600
#         Output Directory:  /home/user/adcp_data
#         Log Level:         INFO

# Start recording
adcp-recorder start
# Press Ctrl+C to stop
```

---

### Example 2: First-Time Setup on Windows

```cmd
REM Install the package
pip install adcp-recorder

REM Find your ADCP COM port
adcp-recorder list-ports
REM Output: Found 1 ports:
REM   COM3: USB Serial Port (USB VID:PID=0403:6001)

REM Configure the recorder
adcp-recorder configure --port COM3 --baud 9600 --output C:\ADCP_Data

REM Verify configuration
adcp-recorder status

REM Start recording
adcp-recorder start
REM Press Ctrl+C to stop
```

---

### Example 3: Quick Test Run

```bash
# Configure for a test directory
adcp-recorder configure --output /tmp/adcp_test --debug

# Start recorder
adcp-recorder start &
RECORDER_PID=$!

# Let it run for 30 seconds
sleep 30

# Stop recorder
kill $RECORDER_PID

# Check collected data
ls -lh /tmp/adcp_test/
duckdb /tmp/adcp_test/adcp.duckdb "SELECT COUNT(*) FROM raw_lines;"

# Cleanup
rm -rf /tmp/adcp_test
```

---

## Advanced Configuration

### Example 4: High-Speed ADCP (115200 baud)

```bash
# Configure for high-speed instrument
adcp-recorder configure \
    --port /dev/ttyUSB0 \
    --baud 115200 \
    --output /data/adcp_highspeed

# Verify settings
adcp-recorder status

# Start with debug logging initially
adcp-recorder configure --debug
adcp-recorder start

# After verifying data collection, disable debug
# Ctrl+C to stop
adcp-recorder configure --no-debug
adcp-recorder start
```

---

### Example 5: Multiple ADCP Instruments

Run multiple recorder instances for different instruments:

**Terminal 1 (ADCP 1):**
```bash
export ADCP_RECORDER_SERIAL_PORT=/dev/ttyUSB0
export ADCP_RECORDER_OUTPUT_DIR=/data/adcp1
export ADCP_RECORDER_BAUDRATE=9600

adcp-recorder start
```

**Terminal 2 (ADCP 2):**
```bash
export ADCP_RECORDER_SERIAL_PORT=/dev/ttyUSB1
export ADCP_RECORDER_OUTPUT_DIR=/data/adcp2
export ADCP_RECORDER_BAUDRATE=115200

adcp-recorder start
```

---

### Example 6: Custom Database Location

```bash
# Separate database from data files
adcp-recorder configure \
    --port /dev/ttyUSB0 \
    --baud 9600 \
    --output /mnt/data/adcp_files

# Manually edit config to set custom database path
cat > ~/.adcp-recorder/config.json << EOF
{
    "serial_port": "/dev/ttyUSB0",
    "baudrate": 9600,
    "timeout": 1.0,
    "output_dir": "/mnt/data/adcp_files",
    "log_level": "INFO",
    "db_path": "/var/lib/adcp/database.duckdb"
}
EOF

# Verify configuration
adcp-recorder status

# Start recorder
adcp-recorder start
```

---

## Data Analysis Queries

### Example 7: Basic Data Exploration

```sql
-- Connect to database
-- duckdb ~/adcp_data/adcp.duckdb

-- Show all tables
SHOW TABLES;

-- Count total messages
SELECT COUNT(*) AS total_messages FROM raw_lines;

-- Count valid vs invalid messages
SELECT 
    valid,
    COUNT(*) AS count
FROM raw_lines
GROUP BY valid;

-- Message type distribution
SELECT 
    SUBSTRING(line, 2, POSITION(',' IN line) - 2) AS message_type,
    COUNT(*) AS count
FROM raw_lines
WHERE valid = true
GROUP BY message_type
ORDER BY count DESC;
```

---

### Example 8: Sensor Data Analysis (PNORS)

```sql
-- Connect to database
-- duckdb ~/adcp_data/adcp.duckdb

-- View recent sensor data
SELECT 
    timestamp,
    heading,
    pitch,
    roll,
    temperature,
    pressure
FROM pnors
ORDER BY timestamp DESC
LIMIT 20;

-- Calculate statistics
SELECT 
    COUNT(*) AS total_records,
    MIN(temperature) AS min_temp,
    MAX(temperature) AS max_temp,
    AVG(temperature) AS avg_temp,
    STDDEV(temperature) AS stddev_temp
FROM pnors
WHERE temperature IS NOT NULL;

-- Heading distribution (10-degree bins)
SELECT 
    FLOOR(heading / 10) * 10 AS heading_bin,
    COUNT(*) AS count
FROM pnors
WHERE heading IS NOT NULL
GROUP BY heading_bin
ORDER BY heading_bin;

-- Time series aggregation (hourly averages)
SELECT 
    DATE_TRUNC('hour', timestamp) AS hour,
    AVG(heading) AS avg_heading,
    AVG(temperature) AS avg_temp,
    AVG(pressure) AS avg_pressure
FROM pnors
GROUP BY hour
ORDER BY hour;
```

---

### Example 9: Current Velocity Analysis (PNORC)

```sql
-- Connect to database
-- duckdb ~/adcp_data/adcp.duckdb

-- View recent current data
SELECT 
    timestamp,
    cell_number,
    velocity_east,
    velocity_north,
    velocity_up
FROM pnorc
ORDER BY timestamp DESC, cell_number
LIMIT 50;

-- Calculate current speed and direction
SELECT 
    timestamp,
    cell_number,
    SQRT(velocity_east * velocity_east + velocity_north * velocity_north) AS speed,
    DEGREES(ATAN2(velocity_east, velocity_north)) AS direction
FROM pnorc
WHERE velocity_east IS NOT NULL 
  AND velocity_north IS NOT NULL
ORDER BY timestamp DESC
LIMIT 20;

-- Average velocity by depth cell
SELECT 
    cell_number,
    COUNT(*) AS measurements,
    AVG(velocity_east) AS avg_vel_east,
    AVG(velocity_north) AS avg_vel_north,
    AVG(velocity_up) AS avg_vel_up
FROM pnorc
GROUP BY cell_number
ORDER BY cell_number;
```

---

### Example 10: Error Analysis

```sql
-- Connect to database
-- duckdb ~/adcp_data/adcp.duckdb

-- View recent errors
SELECT 
    timestamp,
    error_type,
    message
FROM errors
ORDER BY timestamp DESC
LIMIT 20;

-- Error frequency by type
SELECT 
    error_type,
    COUNT(*) AS count,
    MIN(timestamp) AS first_occurrence,
    MAX(timestamp) AS last_occurrence
FROM errors
GROUP BY error_type
ORDER BY count DESC;

-- Errors per hour
SELECT 
    DATE_TRUNC('hour', timestamp) AS hour,
    COUNT(*) AS error_count
FROM errors
GROUP BY hour
ORDER BY hour;

-- Invalid messages (checksum failures)
SELECT 
    timestamp,
    line
FROM raw_lines
WHERE valid = false
ORDER BY timestamp DESC
LIMIT 10;
```

---

### Example 11: Export Data to CSV

```bash
# Export PNORS data for specific date
duckdb ~/adcp_data/adcp.duckdb << EOF
COPY (
    SELECT * FROM pnors 
    WHERE DATE(timestamp) = '2026-01-12'
    ORDER BY timestamp
) TO 'pnors_2026-01-12_export.csv' (HEADER, DELIMITER ',');
EOF

# Export summary statistics
duckdb ~/adcp_data/adcp.duckdb << EOF
COPY (
    SELECT 
        DATE(timestamp) AS date,
        COUNT(*) AS records,
        AVG(heading) AS avg_heading,
        AVG(temperature) AS avg_temp,
        AVG(pressure) AS avg_pressure
    FROM pnors
    GROUP BY DATE(timestamp)
    ORDER BY date
) TO 'pnors_daily_summary.csv' (HEADER, DELIMITER ',');
EOF
```

---

## Integration Examples

### Example 12: Python Integration

```python
#!/usr/bin/env python3
"""
Example: Read ADCP data from database and create plots
"""
import duckdb
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Connect to database
db_path = Path.home() / "adcp_data" / "adcp.duckdb"
conn = duckdb.connect(str(db_path), read_only=True)

# Query sensor data
query = """
SELECT 
    timestamp,
    heading,
    temperature,
    pressure
FROM pnors
WHERE timestamp > NOW() - INTERVAL 24 HOURS
ORDER BY timestamp
"""

df = pd.read_sql(query, conn)
conn.close()

# Convert timestamp to datetime
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Create plots
fig, axes = plt.subplots(3, 1, figsize=(12, 10))

# Heading plot
axes[0].plot(df['timestamp'], df['heading'])
axes[0].set_ylabel('Heading (degrees)')
axes[0].set_title('ADCP Heading - Last 24 Hours')
axes[0].grid(True)

# Temperature plot
axes[1].plot(df['timestamp'], df['temperature'], color='red')
axes[1].set_ylabel('Temperature (°C)')
axes[1].set_title('Water Temperature')
axes[1].grid(True)

# Pressure plot
axes[2].plot(df['timestamp'], df['pressure'], color='green')
axes[2].set_ylabel('Pressure (mbar)')
axes[2].set_xlabel('Time')
axes[2].set_title('Pressure')
axes[2].grid(True)

plt.tight_layout()
plt.savefig('adcp_analysis.png', dpi=300)
print("Plot saved to adcp_analysis.png")
```

---

### Example 13: Automated Data Export Script

```bash
#!/bin/bash
# export_daily_data.sh
# Exports yesterday's data to CSV files

OUTPUT_DIR="/backup/adcp_exports"
DB_PATH="$HOME/adcp_data/adcp.duckdb"
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)

mkdir -p "$OUTPUT_DIR"

# Export PNORS data
duckdb "$DB_PATH" << EOF
COPY (
    SELECT * FROM pnors 
    WHERE DATE(timestamp) = '$YESTERDAY'
) TO '$OUTPUT_DIR/pnors_$YESTERDAY.csv' (HEADER, DELIMITER ',');
EOF

# Export PNORC data
duckdb "$DB_PATH" << EOF
COPY (
    SELECT * FROM pnorc 
    WHERE DATE(timestamp) = '$YESTERDAY'
) TO '$OUTPUT_DIR/pnorc_$YESTERDAY.csv' (HEADER, DELIMITER ',');
EOF

# Export PNORI data
duckdb "$DB_PATH" << EOF
COPY (
    SELECT * FROM pnori 
    WHERE DATE(timestamp) = '$YESTERDAY'
) TO '$OUTPUT_DIR/pnori_$YESTERDAY.csv' (HEADER, DELIMITER ',');
EOF

echo "Data exported to $OUTPUT_DIR"

# Compress exports
tar -czf "$OUTPUT_DIR/adcp_$YESTERDAY.tar.gz" "$OUTPUT_DIR"/*_$YESTERDAY.csv
rm "$OUTPUT_DIR"/*_$YESTERDAY.csv

echo "Compressed to adcp_$YESTERDAY.tar.gz"
```

Add to crontab for daily execution:
```bash
# Run at 1 AM daily
0 1 * * * /path/to/export_daily_data.sh
```

---

### Example 14: Real-Time Monitoring Dashboard

```python
#!/usr/bin/env python3
"""
Example: Simple real-time monitoring dashboard
"""
import duckdb
import time
from pathlib import Path
from datetime import datetime, timedelta

db_path = Path.home() / "adcp_data" / "adcp.duckdb"

def get_stats():
    """Get current statistics from database"""
    conn = duckdb.connect(str(db_path), read_only=True)
    
    # Total messages
    total = conn.execute("SELECT COUNT(*) FROM raw_lines").fetchone()[0]
    
    # Messages in last minute
    recent = conn.execute("""
        SELECT COUNT(*) FROM raw_lines 
        WHERE timestamp > NOW() - INTERVAL 1 MINUTE
    """).fetchone()[0]
    
    # Latest sensor data
    latest = conn.execute("""
        SELECT heading, temperature, pressure 
        FROM pnors 
        ORDER BY timestamp DESC 
        LIMIT 1
    """).fetchone()
    
    # Error count
    errors = conn.execute("SELECT COUNT(*) FROM errors").fetchone()[0]
    
    conn.close()
    
    return {
        'total': total,
        'recent': recent,
        'latest': latest,
        'errors': errors
    }

def display_dashboard():
    """Display monitoring dashboard"""
    while True:
        stats = get_stats()
        
        # Clear screen
        print("\033[2J\033[H")
        
        print("=" * 60)
        print("ADCP Recorder - Real-Time Dashboard")
        print("=" * 60)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print(f"Total Messages:     {stats['total']:,}")
        print(f"Messages/min:       {stats['recent']}")
        print(f"Total Errors:       {stats['errors']}")
        print()
        
        if stats['latest']:
            heading, temp, pressure = stats['latest']
            print("Latest Sensor Data:")
            print(f"  Heading:          {heading:.1f}°")
            print(f"  Temperature:      {temp:.2f}°C")
            print(f"  Pressure:         {pressure:.1f} mbar")
        
        print()
        print("Press Ctrl+C to exit")
        print("=" * 60)
        
        time.sleep(5)

if __name__ == "__main__":
    try:
        display_dashboard()
    except KeyboardInterrupt:
        print("\nDashboard stopped")
```

---

## Troubleshooting Scenarios

### Example 15: Diagnosing Connection Issues

```bash
# Step 1: Check if device is recognized
lsusb  # Linux
# Look for your USB-to-serial adapter

# Step 2: Check kernel messages
dmesg | tail -20
# Look for: "USB Serial device now attached to ttyUSB0"

# Step 3: List available ports
adcp-recorder list-ports

# Step 4: Check permissions
ls -l /dev/ttyUSB0
# Should show: crw-rw---- 1 root dialout

# Step 5: Verify group membership
groups
# Should include: dialout

# Step 6: Test with debug logging
adcp-recorder configure --debug --port /dev/ttyUSB0
adcp-recorder start

# Step 7: Monitor for connection messages
# Look for: "Connected to /dev/ttyUSB0"
# Or errors: "Failed to open serial port"
```

---

### Example 16: Recovering from Disk Full

```bash
# Check disk usage
df -h ~/adcp_data

# Find largest files
du -sh ~/adcp_data/* | sort -h

# Archive old data
ARCHIVE_DATE="2025-12"
tar -czf adcp_archive_$ARCHIVE_DATE.tar.gz \
    ~/adcp_data/PNORS/$ARCHIVE_DATE-*.csv \
    ~/adcp_data/PNORC/$ARCHIVE_DATE-*.csv \
    ~/adcp_data/PNORI/$ARCHIVE_DATE-*.csv

# Move archive to external storage
mv adcp_archive_$ARCHIVE_DATE.tar.gz /mnt/backup/

# Remove archived files
rm ~/adcp_data/PNORS/$ARCHIVE_DATE-*.csv
rm ~/adcp_data/PNORC/$ARCHIVE_DATE-*.csv
rm ~/adcp_data/PNORI/$ARCHIVE_DATE-*.csv

# Verify space recovered
df -h ~/adcp_data

# Restart recorder if it stopped
adcp-recorder start
```

---

### Example 17: Investigating Parse Errors

```bash
# Enable debug logging
adcp-recorder configure --debug

# Start recorder and observe logs
adcp-recorder start

# In another terminal, query errors
duckdb ~/adcp_data/adcp.duckdb << EOF
SELECT 
    timestamp,
    error_type,
    message
FROM errors
ORDER BY timestamp DESC
LIMIT 10;
EOF

# Check for invalid messages
duckdb ~/adcp_data/adcp.duckdb << EOF
SELECT 
    timestamp,
    line
FROM raw_lines
WHERE valid = false
ORDER BY timestamp DESC
LIMIT 10;
EOF

# Examine binary error file
hexdump -C ~/adcp_data/errors/$(date +%Y-%m-%d).bin | head -50
```

---

## Automation Examples

### Example 18: Systemd Service with Auto-Restart

```bash
# Generate service file
adcp-recorder generate-service --platform linux

# Edit service file for production
sudo nano /etc/systemd/system/adcp-recorder.service

# Update User, WorkingDirectory, and paths
# Add restart policy:
# Restart=always
# RestartSec=10

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable adcp-recorder
sudo systemctl start adcp-recorder

# Monitor service
sudo systemctl status adcp-recorder
sudo journalctl -u adcp-recorder -f
```

---

### Example 19: Automated Health Check Script

```bash
#!/bin/bash
# health_check.sh
# Checks ADCP recorder health and sends alerts

DB_PATH="$HOME/adcp_data/adcp.duckdb"
ALERT_EMAIL="admin@example.com"

# Check if service is running
if ! systemctl is-active --quiet adcp-recorder; then
    echo "ALERT: ADCP Recorder service is not running" | \
        mail -s "ADCP Recorder Down" "$ALERT_EMAIL"
    exit 1
fi

# Check data collection rate (should have data in last 5 minutes)
RECENT_COUNT=$(duckdb "$DB_PATH" "SELECT COUNT(*) FROM raw_lines WHERE timestamp > NOW() - INTERVAL 5 MINUTES" | tail -1)

if [ "$RECENT_COUNT" -lt 10 ]; then
    echo "ALERT: No data collected in last 5 minutes (count: $RECENT_COUNT)" | \
        mail -s "ADCP Recorder No Data" "$ALERT_EMAIL"
    exit 1
fi

# Check disk space
DISK_USAGE=$(df -h ~/adcp_data | tail -1 | awk '{print $5}' | sed 's/%//')

if [ "$DISK_USAGE" -gt 90 ]; then
    echo "ALERT: Disk usage is at ${DISK_USAGE}%" | \
        mail -s "ADCP Recorder Disk Full" "$ALERT_EMAIL"
    exit 1
fi

echo "Health check passed at $(date)"
```

Add to crontab:
```bash
# Run every 15 minutes
*/15 * * * * /path/to/health_check.sh
```

---

### Example 20: Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.9-slim

# Install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    usbutils \
    && rm -rf /var/lib/apt/lists/*

# Install adcp-recorder
RUN pip install --no-cache-dir adcp-recorder

# Create data directory
RUN mkdir -p /data

# Set environment variables
ENV ADCP_RECORDER_SERIAL_PORT=/dev/ttyUSB0
ENV ADCP_RECORDER_BAUDRATE=9600
ENV ADCP_RECORDER_OUTPUT_DIR=/data
ENV ADCP_RECORDER_LOG_LEVEL=INFO

# Run recorder
CMD ["adcp-recorder", "start"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  adcp-recorder:
    build: .
    devices:
      - /dev/ttyUSB0:/dev/ttyUSB0
    volumes:
      - ./data:/data
    environment:
      - ADCP_RECORDER_SERIAL_PORT=/dev/ttyUSB0
      - ADCP_RECORDER_BAUDRATE=9600
      - ADCP_RECORDER_OUTPUT_DIR=/data
    restart: unless-stopped
```

Deploy:
```bash
docker-compose up -d
docker-compose logs -f
```

---

## Next Steps

- **Deploy to production**: See [DEPLOYMENT.md](../deployment/DEPLOYMENT.md)
- **Advanced queries**: See [Query Examples](../examples/query-examples.md)
- **Configuration details**: See [CONFIGURATION.md](CONFIGURATION.md)
- **Troubleshooting**: See [USAGE.md](USAGE.md#error-handling-and-recovery)

---

**These examples cover the most common use cases. Adapt them to your specific needs!**
