# ADCP Recorder - Deployment Guide

This guide provides comprehensive instructions for deploying the ADCP Recorder as a production service on Linux and Windows platforms.

## Table of Contents

- [Pre-Deployment Checklist](#pre-deployment-checklist)
- [System Preparation](#system-preparation)
- [Linux Deployment](#linux-deployment)
- [Windows Deployment](#windows-deployment)
- [Service Management](#service-management)
- [Security Considerations](#security-considerations)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Backup and Recovery](#backup-and-recovery)
- [Upgrade Procedures](#upgrade-procedures)
- [Troubleshooting Deployment](#troubleshooting-deployment)

---

## Pre-Deployment Checklist

Before deploying the ADCP Recorder, ensure the following requirements are met:

### Hardware Requirements

- [ ] Serial port or USB-to-serial adapter available
- [ ] Sufficient disk space for data storage (minimum 10 GB recommended)
- [ ] Reliable power supply (UPS recommended for critical deployments)
- [ ] Network connectivity (if remote monitoring is required)

### Software Requirements

- [ ] Python 3.9 or higher installed
- [ ] pip package manager available
- [ ] Virtual environment support (recommended)
- [ ] System service support (systemd for Linux, Windows Service for Windows)

### Configuration Requirements

- [ ] Serial port identified (e.g., `/dev/ttyUSB0`, `COM3`)
- [ ] Baud rate determined (consult ADCP manual)
- [ ] Output directory planned with adequate space
- [ ] Backup strategy defined
- [ ] Monitoring plan established

### Access Requirements

- [ ] User account with serial port access (Linux: `dialout` group)
- [ ] Write permissions for output directory
- [ ] Service installation permissions (root/administrator)

---

## System Preparation

### Linux System Preparation

```bash
# Update system packages
sudo apt-get update && sudo apt-get upgrade -y  # Debian/Ubuntu
# OR
sudo dnf update -y  # RHEL/Fedora

# Install Python and dependencies
sudo apt-get install -y python3 python3-pip python3-venv  # Debian/Ubuntu
# OR
sudo dnf install -y python3 python3-pip  # RHEL/Fedora

# Create service user (recommended for production)
sudo useradd -r -s /bin/false -m -d /var/lib/adcp-recorder adcp-recorder

# Add service user to dialout group for serial port access
sudo usermod -a -G dialout adcp-recorder

# Create data directory
sudo mkdir -p /var/lib/adcp-recorder/data
sudo chown -R adcp-recorder:adcp-recorder /var/lib/adcp-recorder

# Create log directory
sudo mkdir -p /var/log/adcp-recorder
sudo chown adcp-recorder:adcp-recorder /var/log/adcp-recorder
```

### Windows System Preparation

```powershell
# Run PowerShell as Administrator

# Verify Python installation
python --version

# Create service directory
New-Item -ItemType Directory -Path "C:\Program Files\ADCP-Recorder" -Force

# Create data directory
New-Item -ItemType Directory -Path "C:\ADCP_Data" -Force

# Install pywin32 for Windows service support
pip install pywin32
```

---

## Linux Deployment

### Method 1: Automated Installation (Recommended)

Use the provided installation script:

```bash
# Download and run installation script
curl -O https://raw.githubusercontent.com/your-org/adcp-recorder/main/scripts/install-linux.sh
chmod +x install-linux.sh
sudo ./install-linux.sh
```

The script will:
1. Install the package in a virtual environment
2. Configure the system service
3. Set up logging
4. Enable auto-start on boot

### Method 2: Manual Installation

#### Step 1: Install Package

```bash
# Create virtual environment
sudo -u adcp-recorder python3 -m venv /var/lib/adcp-recorder/venv

# Activate virtual environment
sudo -u adcp-recorder /var/lib/adcp-recorder/venv/bin/pip install adcp-recorder
```

#### Step 2: Configure Application

```bash
# Create configuration directory
sudo -u adcp-recorder mkdir -p /var/lib/adcp-recorder/.adcp-recorder

# Create configuration file
sudo -u adcp-recorder tee /var/lib/adcp-recorder/.adcp-recorder/config.json << EOF
{
    "serial_port": "/dev/ttyUSB0",
    "baudrate": 9600,
    "timeout": 1.0,
    "output_dir": "/var/lib/adcp-recorder/data",
    "log_level": "INFO",
    "db_path": null
}
EOF
```

#### Step 3: Create Systemd Service

```bash
# Generate service file
/var/lib/adcp-recorder/venv/bin/adcp-recorder generate-service --platform linux --out /tmp

# Copy and customize service file
sudo cp /tmp/adcp-recorder.service /etc/systemd/system/

# Edit service file
sudo nano /etc/systemd/system/adcp-recorder.service
```

**Service File Template:**
```ini
[Unit]
Description=ADCP Recorder Service
After=network.target
Documentation=https://github.com/your-org/adcp-recorder

[Service]
Type=simple
User=adcp-recorder
Group=adcp-recorder
WorkingDirectory=/var/lib/adcp-recorder

# Set HOME for config file location
Environment="HOME=/var/lib/adcp-recorder"
Environment="PATH=/var/lib/adcp-recorder/venv/bin:/usr/local/bin:/usr/bin:/bin"

# Run the service supervisor
ExecStart=/var/lib/adcp-recorder/venv/bin/python3 -m adcp_recorder.service.supervisor

# Restart policy
Restart=always
RestartSec=10

# Graceful shutdown
KillSignal=SIGTERM
TimeoutStopSec=30

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/adcp-recorder/data /var/log/adcp-recorder

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=adcp-recorder

[Install]
WantedBy=multi-user.target
```

#### Step 4: Enable and Start Service

```bash
# Reload systemd configuration
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable adcp-recorder

# Start service
sudo systemctl start adcp-recorder

# Check status
sudo systemctl status adcp-recorder

# View logs
sudo journalctl -u adcp-recorder -f
```

---

## Windows Deployment

### Method 1: Automated Installation (Recommended)

Use the provided installation script:

```cmd
REM Download and run installation script
REM Run Command Prompt as Administrator
install-windows.bat
```

### Method 2: Manual Installation

#### Step 1: Install Package

```cmd
REM Create installation directory
mkdir "C:\Program Files\ADCP-Recorder"
cd "C:\Program Files\ADCP-Recorder"

REM Create virtual environment
python -m venv venv

REM Activate and install
venv\Scripts\activate
pip install adcp-recorder
pip install pywin32
```

#### Step 2: Configure Application

```cmd
REM Create configuration directory
mkdir "%PROGRAMDATA%\ADCP-Recorder"

REM Create configuration file
echo { > "%PROGRAMDATA%\ADCP-Recorder\config.json"
echo     "serial_port": "COM3", >> "%PROGRAMDATA%\ADCP-Recorder\config.json"
echo     "baudrate": 9600, >> "%PROGRAMDATA%\ADCP-Recorder\config.json"
echo     "timeout": 1.0, >> "%PROGRAMDATA%\ADCP-Recorder\config.json"
echo     "output_dir": "C:\\ADCP_Data", >> "%PROGRAMDATA%\ADCP-Recorder\config.json"
echo     "log_level": "INFO", >> "%PROGRAMDATA%\ADCP-Recorder\config.json"
echo     "db_path": null >> "%PROGRAMDATA%\ADCP-Recorder\config.json"
echo } >> "%PROGRAMDATA%\ADCP-Recorder\config.json"
```

#### Step 3: Install Windows Service

```powershell
# Run PowerShell as Administrator

# Navigate to installation directory
cd "C:\Program Files\ADCP-Recorder"

# Install service
.\venv\Scripts\python.exe -m adcp_recorder.service.win_service install

# Configure service to start automatically
sc config adcp-recorder start= auto

# Start service
sc start adcp-recorder

# Check service status
sc query adcp-recorder
```

**Alternative: Use PowerShell Script**

```powershell
# Generate and run installation script
& "C:\Program Files\ADCP-Recorder\venv\Scripts\adcp-recorder.exe" generate-service --platform windows --out .

# Run the generated script as Administrator
.\install-service-windows.ps1
```

---

## Service Management

### Linux Service Management

```bash
# Start service
sudo systemctl start adcp-recorder

# Stop service
sudo systemctl stop adcp-recorder

# Restart service
sudo systemctl restart adcp-recorder

# Check status
sudo systemctl status adcp-recorder

# View logs (real-time)
sudo journalctl -u adcp-recorder -f

# View logs (last 100 lines)
sudo journalctl -u adcp-recorder -n 100

# View logs since specific time
sudo journalctl -u adcp-recorder --since "1 hour ago"

# Enable auto-start on boot
sudo systemctl enable adcp-recorder

# Disable auto-start
sudo systemctl disable adcp-recorder
```

### Windows Service Management

```cmd
REM Start service
sc start adcp-recorder
REM Or: net start adcp-recorder

REM Stop service
sc stop adcp-recorder
REM Or: net stop adcp-recorder

REM Check status
sc query adcp-recorder

REM Configure auto-start
sc config adcp-recorder start= auto

REM Configure manual start
sc config adcp-recorder start= demand

REM View service properties
sc qc adcp-recorder
```

**Using Services GUI:**
```cmd
REM Open Services management console
services.msc

REM Find "ADCP Recorder Service"
REM Right-click for Start, Stop, Restart options
```

**View Logs (Event Viewer):**
```cmd
REM Open Event Viewer
eventvwr.msc

REM Navigate to: Windows Logs → Application
REM Filter by Source: adcp-recorder
```

---

## Security Considerations

### Principle of Least Privilege

**Linux:**
```bash
# Run service as dedicated user (not root)
# Already configured in systemd service file

# Restrict file permissions
sudo chmod 700 /var/lib/adcp-recorder/data
sudo chmod 600 /var/lib/adcp-recorder/.adcp-recorder/config.json

# Use systemd security features
# See service file: NoNewPrivileges, ProtectSystem, etc.
```

**Windows:**
```powershell
# Run service as dedicated user (not Administrator)
# Configure in Services → Properties → Log On tab

# Restrict folder permissions
icacls "C:\ADCP_Data" /grant "ADCP-Service:(OI)(CI)F" /inheritance:r
```

### Network Security

If exposing data remotely:

```bash
# Use firewall rules to restrict access
sudo ufw allow from 192.168.1.0/24 to any port 3306  # Example for database access

# Use SSH tunneling for remote access
ssh -L 3306:localhost:3306 user@adcp-server

# Consider VPN for production deployments
```

### Data Security

```bash
# Encrypt data at rest (Linux)
# Use LUKS or similar for disk encryption

# Regular security updates
sudo apt-get update && sudo apt-get upgrade -y

# Monitor for unauthorized access
sudo tail -f /var/log/auth.log
```

---

## Monitoring and Maintenance

### Health Monitoring

**Automated Health Checks:**

```bash
# Create health check script
sudo tee /usr/local/bin/adcp-health-check.sh << 'EOF'
#!/bin/bash
# Health check for ADCP Recorder

# Check service status
if ! systemctl is-active --quiet adcp-recorder; then
    echo "CRITICAL: Service is not running"
    exit 2
fi

# Check data collection (last 5 minutes)
DB_PATH="/var/lib/adcp-recorder/data/adcp.duckdb"
RECENT_COUNT=$(duckdb "$DB_PATH" "SELECT COUNT(*) FROM raw_lines WHERE timestamp > NOW() - INTERVAL 5 MINUTES" 2>/dev/null | tail -1)

if [ "$RECENT_COUNT" -lt 10 ]; then
    echo "WARNING: Low data collection rate ($RECENT_COUNT messages in 5 min)"
    exit 1
fi

# Check disk space
DISK_USAGE=$(df /var/lib/adcp-recorder/data | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    echo "WARNING: Disk usage at ${DISK_USAGE}%"
    exit 1
fi

echo "OK: Service healthy, collecting data"
exit 0
EOF

sudo chmod +x /usr/local/bin/adcp-health-check.sh

# Add to cron for periodic checks
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/adcp-health-check.sh") | crontab -
```

**Integration with Monitoring Systems:**

```bash
# Nagios/Icinga check
define service {
    use                     generic-service
    host_name               adcp-server
    service_description     ADCP Recorder Health
    check_command           check_by_ssh!/usr/local/bin/adcp-health-check.sh
}

# Prometheus exporter (custom)
# Export metrics: message_count, error_count, disk_usage
```

### Log Rotation

**Linux (systemd journal):**
```bash
# Configure journald retention
sudo nano /etc/systemd/journald.conf

# Set:
# SystemMaxUse=1G
# MaxRetentionSec=1month

# Restart journald
sudo systemctl restart systemd-journald
```

**Custom log files:**
```bash
# Create logrotate configuration
sudo tee /etc/logrotate.d/adcp-recorder << EOF
/var/log/adcp-recorder/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0640 adcp-recorder adcp-recorder
    sharedscripts
    postrotate
        systemctl reload adcp-recorder > /dev/null 2>&1 || true
    endscript
}
EOF
```

### Database Maintenance

```bash
# Weekly database optimization
sudo -u adcp-recorder tee /usr/local/bin/adcp-db-maintenance.sh << 'EOF'
#!/bin/bash
DB_PATH="/var/lib/adcp-recorder/data/adcp.duckdb"

# Stop service
systemctl stop adcp-recorder

# Optimize database
duckdb "$DB_PATH" "VACUUM; ANALYZE;"

# Start service
systemctl start adcp-recorder

echo "Database maintenance completed"
EOF

sudo chmod +x /usr/local/bin/adcp-db-maintenance.sh

# Add to cron (weekly, Sunday 2 AM)
sudo crontab -e
# Add: 0 2 * * 0 /usr/local/bin/adcp-db-maintenance.sh
```

---

## Backup and Recovery

### Backup Strategy

**Daily Incremental Backups:**

```bash
#!/bin/bash
# /usr/local/bin/adcp-backup.sh

BACKUP_DIR="/backup/adcp"
DATA_DIR="/var/lib/adcp-recorder/data"
DATE=$(date +%Y%m%d)

mkdir -p "$BACKUP_DIR"

# Backup database
cp "$DATA_DIR/adcp.duckdb" "$BACKUP_DIR/adcp_$DATE.duckdb"

# Backup CSV files (last 7 days)
find "$DATA_DIR" -name "*.csv" -mtime -7 -exec tar -czf "$BACKUP_DIR/csv_$DATE.tar.gz" {} +

# Backup configuration
cp /var/lib/adcp-recorder/.adcp-recorder/config.json "$BACKUP_DIR/config_$DATE.json"

# Remove backups older than 30 days
find "$BACKUP_DIR" -name "*.duckdb" -mtime +30 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

Add to cron:
```bash
# Daily at 3 AM
0 3 * * * /usr/local/bin/adcp-backup.sh
```

### Recovery Procedures

**Restore from Backup:**

```bash
# Stop service
sudo systemctl stop adcp-recorder

# Restore database
sudo cp /backup/adcp/adcp_20260112.duckdb /var/lib/adcp-recorder/data/adcp.duckdb
sudo chown adcp-recorder:adcp-recorder /var/lib/adcp-recorder/data/adcp.duckdb

# Restore configuration
sudo cp /backup/adcp/config_20260112.json /var/lib/adcp-recorder/.adcp-recorder/config.json
sudo chown adcp-recorder:adcp-recorder /var/lib/adcp-recorder/.adcp-recorder/config.json

# Start service
sudo systemctl start adcp-recorder

# Verify
sudo systemctl status adcp-recorder
```

---

## Upgrade Procedures

### Upgrading the Package

**Linux:**

```bash
# Stop service
sudo systemctl stop adcp-recorder

# Backup current installation
sudo cp -r /var/lib/adcp-recorder/venv /var/lib/adcp-recorder/venv.backup

# Upgrade package
sudo -u adcp-recorder /var/lib/adcp-recorder/venv/bin/pip install --upgrade adcp-recorder

# Verify installation
sudo -u adcp-recorder /var/lib/adcp-recorder/venv/bin/adcp-recorder --help

# Start service
sudo systemctl start adcp-recorder

# Monitor for issues
sudo journalctl -u adcp-recorder -f
```

**Windows:**

```cmd
REM Stop service
sc stop adcp-recorder

REM Upgrade package
cd "C:\Program Files\ADCP-Recorder"
venv\Scripts\activate
pip install --upgrade adcp-recorder

REM Start service
sc start adcp-recorder

REM Check status
sc query adcp-recorder
```

### Rollback Procedure

If upgrade fails:

```bash
# Stop service
sudo systemctl stop adcp-recorder

# Restore backup
sudo rm -rf /var/lib/adcp-recorder/venv
sudo mv /var/lib/adcp-recorder/venv.backup /var/lib/adcp-recorder/venv

# Start service
sudo systemctl start adcp-recorder
```

---

## Troubleshooting Deployment

### Service Won't Start

**Check service status:**
```bash
sudo systemctl status adcp-recorder
sudo journalctl -u adcp-recorder -n 50
```

**Common issues:**

1. **Permission denied on serial port:**
   ```bash
   sudo usermod -a -G dialout adcp-recorder
   sudo systemctl restart adcp-recorder
   ```

2. **Configuration file not found:**
   ```bash
   sudo -u adcp-recorder ls -la /var/lib/adcp-recorder/.adcp-recorder/
   # Recreate if missing
   ```

3. **Python module not found:**
   ```bash
   sudo -u adcp-recorder /var/lib/adcp-recorder/venv/bin/pip list | grep adcp
   # Reinstall if missing
   ```

### Service Crashes Repeatedly

```bash
# Check crash logs
sudo journalctl -u adcp-recorder --since "1 hour ago" | grep -i error

# Check system resources
free -h
df -h

# Check for database locks
lsof /var/lib/adcp-recorder/data/adcp.duckdb
```

### No Data Being Collected

```bash
# Verify serial port connection
sudo -u adcp-recorder /var/lib/adcp-recorder/venv/bin/adcp-recorder list-ports

# Check configuration
sudo -u adcp-recorder cat /var/lib/adcp-recorder/.adcp-recorder/config.json

# Enable debug logging
sudo -u adcp-recorder /var/lib/adcp-recorder/venv/bin/adcp-recorder configure --debug
sudo systemctl restart adcp-recorder
sudo journalctl -u adcp-recorder -f
```

---

## Production Deployment Checklist

- [ ] System requirements verified
- [ ] Service user created with appropriate permissions
- [ ] Package installed in virtual environment
- [ ] Configuration file created and validated
- [ ] Systemd/Windows service configured
- [ ] Service enabled for auto-start
- [ ] Service started and running
- [ ] Data collection verified
- [ ] Logs reviewed for errors
- [ ] Backup strategy implemented
- [ ] Monitoring configured
- [ ] Documentation updated with deployment details
- [ ] Emergency contacts and procedures documented

---

**Your ADCP Recorder is now deployed and ready for production use!**

For ongoing operations, refer to:
- [USAGE.md](../user-guide/USAGE.md) for daily operations
- [CONFIGURATION.md](../user-guide/CONFIGURATION.md) for configuration changes
- [EXAMPLES.md](../user-guide/EXAMPLES.md) for common scenarios
