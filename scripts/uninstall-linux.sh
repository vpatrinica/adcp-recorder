#!/bin/bash
#
# uninstall-linux.sh - Uninstall ADCP Recorder service from Linux
#
# This script removes the ADCP Recorder service and optionally removes data.
# It must be run with sudo privileges.
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SERVICE_USER="adcp-recorder"
INSTALL_DIR="/var/lib/adcp-recorder"
LOG_DIR="/var/log/adcp-recorder"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}ADCP Recorder - Linux Uninstallation${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}✗ This script must be run as root (use sudo)${NC}"
    exit 1
fi

# Confirm uninstallation
echo -e "${YELLOW}This will remove the ADCP Recorder service.${NC}"
read -p "Are you sure you want to continue? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Uninstallation cancelled"
    exit 0
fi
echo ""

# Step 1: Stop and disable service
echo -e "${YELLOW}[1/5] Stopping and disabling service...${NC}"
if systemctl is-active --quiet adcp-recorder; then
    systemctl stop adcp-recorder
    echo -e "${GREEN}✓ Service stopped${NC}"
else
    echo "Service is not running"
fi

if systemctl is-enabled --quiet adcp-recorder 2>/dev/null; then
    systemctl disable adcp-recorder
    echo -e "${GREEN}✓ Service disabled${NC}"
else
    echo "Service is not enabled"
fi
echo ""

# Step 2: Remove service file
echo -e "${YELLOW}[2/5] Removing service file...${NC}"
if [ -f /etc/systemd/system/adcp-recorder.service ]; then
    rm /etc/systemd/system/adcp-recorder.service
    systemctl daemon-reload
    echo -e "${GREEN}✓ Service file removed${NC}"
else
    echo "Service file not found"
fi
echo ""

# Step 3: Remove virtual environment and installation
echo -e "${YELLOW}[3/5] Removing installation...${NC}"
if [ -d "$INSTALL_DIR/venv" ]; then
    rm -rf "$INSTALL_DIR/venv"
    echo -e "${GREEN}✓ Virtual environment removed${NC}"
else
    echo "Virtual environment not found"
fi
echo ""

# Step 4: Ask about data removal
echo -e "${YELLOW}[4/5] Data removal...${NC}"
if [ -d "$INSTALL_DIR/data" ]; then
    echo -e "${RED}WARNING: This will permanently delete all collected data!${NC}"
    read -p "Remove data directory $INSTALL_DIR/data? (yes/no): " REMOVE_DATA
    if [ "$REMOVE_DATA" = "yes" ]; then
        rm -rf "$INSTALL_DIR/data"
        echo -e "${GREEN}✓ Data directory removed${NC}"
    else
        echo "Data directory preserved at: $INSTALL_DIR/data"
    fi
else
    echo "Data directory not found"
fi

# Ask about configuration removal
if [ -d "$INSTALL_DIR/.adcp-recorder" ]; then
    read -p "Remove configuration directory? (yes/no): " REMOVE_CONFIG
    if [ "$REMOVE_CONFIG" = "yes" ]; then
        rm -rf "$INSTALL_DIR/.adcp-recorder"
        echo -e "${GREEN}✓ Configuration removed${NC}"
    else
        echo "Configuration preserved at: $INSTALL_DIR/.adcp-recorder"
    fi
fi
echo ""

# Step 5: Remove user and directories
echo -e "${YELLOW}[5/5] Cleanup...${NC}"

# Remove log directory
if [ -d "$LOG_DIR" ]; then
    rm -rf "$LOG_DIR"
    echo -e "${GREEN}✓ Log directory removed${NC}"
fi

# Remove installation directory if empty
if [ -d "$INSTALL_DIR" ]; then
    if [ -z "$(ls -A $INSTALL_DIR)" ]; then
        rmdir "$INSTALL_DIR"
        echo -e "${GREEN}✓ Installation directory removed${NC}"
    else
        echo "Installation directory not empty, preserved at: $INSTALL_DIR"
    fi
fi

# Remove service user
read -p "Remove service user '$SERVICE_USER'? (yes/no): " REMOVE_USER
if [ "$REMOVE_USER" = "yes" ]; then
    if id "$SERVICE_USER" &>/dev/null; then
        userdel "$SERVICE_USER" 2>/dev/null || {
            echo -e "${YELLOW}⚠ Could not remove user (may have running processes)${NC}"
        }
        echo -e "${GREEN}✓ Service user removed${NC}"
    fi
else
    echo "Service user preserved"
fi
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Uninstallation Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "ADCP Recorder has been uninstalled."
echo ""
if [ -d "$INSTALL_DIR" ]; then
    echo "Preserved directories:"
    echo "  $INSTALL_DIR"
    echo ""
    echo "To completely remove all files:"
    echo "  sudo rm -rf $INSTALL_DIR"
fi
echo ""
