#!/bin/bash
#
# install-linux.sh - Install ADCP Recorder as a system service on Linux
#
# This script automates the installation of ADCP Recorder as a systemd service.
# It must be run with sudo privileges.
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_USER="adcp-recorder"
INSTALL_DIR="/var/lib/adcp-recorder"
DATA_DIR="$INSTALL_DIR/data"
VENV_DIR="$INSTALL_DIR/venv"
CONFIG_DIR="$INSTALL_DIR/.adcp-recorder"
LOG_DIR="/var/log/adcp-recorder"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}ADCP Recorder - Linux Installation${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}✗ This script must be run as root (use sudo)${NC}"
    exit 1
fi

# Step 1: Check system requirements
echo -e "${YELLOW}[1/10] Checking system requirements...${NC}"

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    echo "Please install Python 3.9+ first:"
    echo "  sudo apt-get install python3 python3-pip python3-venv  # Debian/Ubuntu"
    echo "  sudo dnf install python3 python3-pip  # RHEL/Fedora"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"
python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" || {
    echo -e "${RED}✗ Python 3.9+ required${NC}"
    exit 1
}

# Check systemd
if ! command -v systemctl &> /dev/null; then
    echo -e "${RED}✗ systemd not found${NC}"
    echo "This script requires systemd for service management"
    exit 1
fi

echo -e "${GREEN}✓ System requirements met${NC}"
echo ""

# Step 2: Create service user
echo -e "${YELLOW}[2/10] Creating service user...${NC}"
if id "$SERVICE_USER" &>/dev/null; then
    echo "User $SERVICE_USER already exists"
else
    useradd -r -s /bin/false -m -d "$INSTALL_DIR" "$SERVICE_USER"
    echo -e "${GREEN}✓ Created user: $SERVICE_USER${NC}"
fi

# Add user to dialout group for serial port access
if getent group dialout > /dev/null 2>&1; then
    usermod -a -G dialout "$SERVICE_USER"
    echo -e "${GREEN}✓ Added $SERVICE_USER to dialout group${NC}"
elif getent group uucp > /dev/null 2>&1; then
    usermod -a -G uucp "$SERVICE_USER"
    echo -e "${GREEN}✓ Added $SERVICE_USER to uucp group${NC}"
else
    echo -e "${YELLOW}⚠ No dialout or uucp group found, serial port access may require manual configuration${NC}"
fi
echo ""

# Step 3: Create directories
echo -e "${YELLOW}[3/10] Creating directories...${NC}"
mkdir -p "$DATA_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$LOG_DIR"
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
chown "$SERVICE_USER:$SERVICE_USER" "$LOG_DIR"
echo -e "${GREEN}✓ Directories created${NC}"
echo ""

# Step 4: Create virtual environment
echo -e "${YELLOW}[4/10] Creating virtual environment...${NC}"
if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment already exists, removing..."
    rm -rf "$VENV_DIR"
fi
sudo -u "$SERVICE_USER" python3 -m venv "$VENV_DIR"
echo -e "${GREEN}✓ Virtual environment created${NC}"
echo ""

# Step 5: Install package
echo -e "${YELLOW}[5/10] Installing ADCP Recorder...${NC}"
sudo -u "$SERVICE_USER" "$VENV_DIR/bin/pip" install --quiet --upgrade pip
sudo -u "$SERVICE_USER" "$VENV_DIR/bin/pip" install --quiet adcp-recorder
echo -e "${GREEN}✓ Package installed${NC}"
echo ""

# Step 6: Configure application
echo -e "${YELLOW}[6/10] Creating configuration...${NC}"

# Prompt for serial port
echo -e "${BLUE}Available serial ports:${NC}"
"$VENV_DIR/bin/adcp-recorder" list-ports || echo "No ports detected"
echo ""
read -p "Enter serial port (e.g., /dev/ttyUSB0): " SERIAL_PORT
SERIAL_PORT=${SERIAL_PORT:-/dev/ttyUSB0}

read -p "Enter baud rate (default: 9600): " BAUD_RATE
BAUD_RATE=${BAUD_RATE:-9600}

# Create configuration file
sudo -u "$SERVICE_USER" tee "$CONFIG_DIR/config.json" > /dev/null << EOF
{
    "serial_port": "$SERIAL_PORT",
    "baudrate": $BAUD_RATE,
    "timeout": 1.0,
    "output_dir": "$DATA_DIR",
    "log_level": "INFO",
    "db_path": null
}
EOF

echo -e "${GREEN}✓ Configuration created${NC}"
echo ""

# Step 7: Create systemd service file
echo -e "${YELLOW}[7/10] Creating systemd service...${NC}"

tee /etc/systemd/system/adcp-recorder.service > /dev/null << EOF
[Unit]
Description=ADCP Recorder Service
After=network.target
Documentation=https://github.com/your-org/adcp-recorder

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR

# Set HOME for config file location
Environment="HOME=$INSTALL_DIR"
Environment="PATH=$VENV_DIR/bin:/usr/local/bin:/usr/bin:/bin"

# Run the service supervisor
ExecStart=$VENV_DIR/bin/python3 -m adcp_recorder.service.supervisor

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
ReadWritePaths=$DATA_DIR $LOG_DIR

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=adcp-recorder

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✓ Systemd service created${NC}"
echo ""

# Step 8: Reload systemd and enable service
echo -e "${YELLOW}[8/10] Enabling service...${NC}"
systemctl daemon-reload
systemctl enable adcp-recorder
echo -e "${GREEN}✓ Service enabled${NC}"
echo ""

# Step 9: Start service
echo -e "${YELLOW}[9/10] Starting service...${NC}"
systemctl start adcp-recorder
sleep 2
echo -e "${GREEN}✓ Service started${NC}"
echo ""

# Step 10: Verify installation
echo -e "${YELLOW}[10/10] Verifying installation...${NC}"

# Check service status
if systemctl is-active --quiet adcp-recorder; then
    echo -e "${GREEN}✓ Service is running${NC}"
else
    echo -e "${RED}✗ Service is not running${NC}"
    echo "Check logs with: sudo journalctl -u adcp-recorder -n 50"
    exit 1
fi

# Check data directory
if [ -d "$DATA_DIR" ]; then
    echo -e "${GREEN}✓ Data directory exists${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Installation Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Service Status:"
systemctl status adcp-recorder --no-pager || true
echo ""
echo "Configuration:"
echo "  Config file: $CONFIG_DIR/config.json"
echo "  Data directory: $DATA_DIR"
echo "  Serial port: $SERIAL_PORT"
echo "  Baud rate: $BAUD_RATE"
echo ""
echo "Useful Commands:"
echo "  View status:  sudo systemctl status adcp-recorder"
echo "  View logs:    sudo journalctl -u adcp-recorder -f"
echo "  Stop service: sudo systemctl stop adcp-recorder"
echo "  Restart:      sudo systemctl restart adcp-recorder"
echo ""
echo "Next Steps:"
echo "  1. Monitor logs: sudo journalctl -u adcp-recorder -f"
echo "  2. Verify data collection: ls -lh $DATA_DIR"
echo "  3. Query database: duckdb $DATA_DIR/adcp.duckdb"
echo ""
