# ADCP Recorder - Installation Guide

This guide provides comprehensive instructions for installing the ADCP Recorder system on Linux and Windows platforms.

## Table of Contents

- [System Requirements](#system-requirements)
- [Installation Methods](#installation-methods)
  - [Method 1: Install from PyPI (Recommended)](#method-1-install-from-pypi-recommended)
  - [Method 2: Install from Source](#method-2-install-from-source)
  - [Method 3: Development Installation](#method-3-development-installation)
- [Platform-Specific Instructions](#platform-specific-instructions)
  - [Linux Installation](#linux-installation)
  - [Windows Installation](#windows-installation)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements

- **Python**: 3.13 or higher
- **Operating System**: 
  - Linux (Ubuntu 20.04+, Debian 11+, RHEL 8+, or equivalent)
  - Windows 10/11 or Windows Server 2019+
- **RAM**: 512 MB minimum, 1 GB recommended
- **Disk Space**: 100 MB for application, additional space for data storage
- **Serial Port**: USB-to-serial adapter or native serial port

### Python Dependencies

Core dependencies (automatically installed):
- `pyserial >= 3.5` - Serial port communication
- `duckdb >= 0.9.0` - Embedded database
- `click >= 8.1.0` - CLI framework

Optional dependencies:
- `pytest >= 7.4.0` - For running tests (development)
- `pytest-cov >= 4.1.0` - For coverage reports (development)
- `pytest-mock >= 3.11.0` - For mocking in tests (development)
- `pywin32 >= 306` - For Windows service support (Windows only)

### Hardware Requirements

- **Serial Port Access**: Physical or virtual serial port
- **Permissions**: Read/write access to serial ports
  - Linux: User must be in `dialout` or `uucp` group
  - Windows: Administrator rights may be required for service installation

---

## Installation Methods

### Method 1: Install from PyPI (Recommended)

> [!NOTE]
> This method is recommended for production deployments.

#### Using pip

```bash
# Create and activate virtual environment (recommended)
python3 -m venv adcp-env
source adcp-env/bin/activate  # On Windows: adcp-env\Scripts\activate

# Install the package
pip install adcp-recorder

# Verify installation
adcp-recorder --help
```

#### Using pipx (Isolated Installation)

```bash
# Install pipx if not already installed
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Install adcp-recorder in isolated environment
pipx install adcp-recorder

# Verify installation
adcp-recorder --help
```

---

### Method 2: Install from Source

> [!TIP]
> Use this method if you need the latest development version or want to customize the installation.

```bash
# Clone the repository
git clone https://github.com/your-org/adcp-recorder.git
cd adcp-recorder

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install .

# Verify installation
adcp-recorder --help
```

---

### Method 3: Development Installation

> [!IMPORTANT]
> This method is for developers who want to modify the code.

```bash
# Clone the repository
git clone https://github.com/your-org/adcp-recorder.git
cd adcp-recorder

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with development dependencies
pip install -e ".[dev]"

# Run tests to verify
pytest

# Check code coverage
pytest --cov=adcp_recorder --cov-report=html
```

---

## Platform-Specific Instructions

### Linux Installation

#### Step 1: Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv
```

**RHEL/CentOS/Fedora:**
```bash
sudo dnf install -y python3 python3-pip
```

#### Step 2: Configure Serial Port Permissions

Add your user to the `dialout` group to access serial ports without sudo:

```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Log out and log back in for changes to take effect
# Or use: newgrp dialout
```

Verify serial port access:
```bash
# List available serial ports
ls -l /dev/ttyUSB* /dev/ttyACM*

# Check group membership
groups
```

#### Step 3: Install ADCP Recorder

```bash
# Create virtual environment
python3 -m venv ~/adcp-env
source ~/adcp-env/bin/activate

# Install package
pip install adcp-recorder

# Or install from source
# git clone https://github.com/your-org/adcp-recorder.git
# cd adcp-recorder
# pip install .
```

#### Step 4: Configure and Test

```bash
# List available serial ports
adcp-recorder list-ports

# Configure the recorder
adcp-recorder configure --port /dev/ttyUSB0 --baud 9600 --output ~/adcp_data

# Check status
adcp-recorder status

# Test run (Ctrl+C to stop)
adcp-recorder start
```

#### Step 5: Install as System Service (Optional)

See [DEPLOYMENT.md](../deployment/DEPLOYMENT.md) for systemd service installation.

---

### Windows Installation

#### Step 1: Install Python

1. Download Python 3.13+ from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. **Important**: Check "Add Python to PATH" during installation
4. Verify installation:
   ```cmd
   python --version
   pip --version
   ```

#### Step 2: Install ADCP Recorder

Open Command Prompt or PowerShell:

```cmd
REM Create virtual environment
python -m venv C:\adcp-env

REM Activate virtual environment
C:\adcp-env\Scripts\activate

REM Install package
pip install adcp-recorder

REM Or install from source
REM git clone https://github.com/your-org/adcp-recorder.git
REM cd adcp-recorder
REM pip install .
```

#### Step 3: Install Windows Service Support (Optional)

For running as a Windows service:

```cmd
REM Install pywin32
pip install pywin32

REM Install the service (requires Administrator)
python -m adcp_recorder.service.win_service install
```

#### Step 4: Configure and Test

```cmd
REM List available COM ports
adcp-recorder list-ports

REM Configure the recorder
adcp-recorder configure --port COM3 --baud 9600 --output C:\adcp_data

REM Check status
adcp-recorder status

REM Test run (Ctrl+C to stop)
adcp-recorder start
```

---

## Verification

### Verify Installation

```bash
# Check version
adcp-recorder --help

# List available commands
adcp-recorder --help

# Check configuration
adcp-recorder status
```

### Verify Serial Port Access

```bash
# List available ports
adcp-recorder list-ports

# Expected output:
# Found 2 ports:
#   /dev/ttyUSB0: USB Serial Port (USB VID:PID=0403:6001)
#   /dev/ttyACM0: Arduino Uno (USB VID:PID=2341:0043)
```

### Verify Database Functionality

```bash
# Start recorder briefly to test database creation
adcp-recorder configure --output /tmp/adcp_test
adcp-recorder start
# Press Ctrl+C after a few seconds

# Check that database was created
ls -lh /tmp/adcp_test/adcp.duckdb
```

### Run Test Suite (Development Installation)

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=adcp_recorder --cov-report=term-missing

# Expected: All tests should pass
```

---

## Troubleshooting

### Common Issues

#### Issue: "Command not found: adcp-recorder"

**Cause**: Python scripts directory not in PATH

**Solution**:
```bash
# Linux/macOS - Add to ~/.bashrc or ~/.zshrc
export PATH="$HOME/.local/bin:$PATH"

# Or use full path
~/.local/bin/adcp-recorder --help

# Or activate virtual environment
source ~/adcp-env/bin/activate
```

#### Issue: "Permission denied" on serial port (Linux)

**Cause**: User not in `dialout` group

**Solution**:
```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Log out and log back in, or use:
newgrp dialout

# Verify
groups | grep dialout
```

#### Issue: "No module named 'adcp_recorder'"

**Cause**: Package not installed or wrong Python environment

**Solution**:
```bash
# Verify Python environment
which python
python -c "import adcp_recorder; print(adcp_recorder.__file__)"

# Reinstall if needed
pip install --force-reinstall adcp-recorder
```

#### Issue: Serial port not found (Windows)

**Cause**: USB driver not installed or wrong COM port

**Solution**:
1. Open Device Manager (Win+X → Device Manager)
2. Check "Ports (COM & LPT)" section
3. Install driver if device shows with yellow warning
4. Note the correct COM port number
5. Use `adcp-recorder list-ports` to verify

#### Issue: "ImportError: DLL load failed" (Windows)

**Cause**: Missing Visual C++ Redistributable

**Solution**:
1. Download and install [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)
2. Restart Command Prompt
3. Reinstall package: `pip install --force-reinstall adcp-recorder`

#### Issue: Database locked error

**Cause**: Another process is using the database

**Solution**:
```bash
# Stop all recorder instances
pkill -f adcp-recorder  # Linux
# Or use Task Manager on Windows

# Check for lock files
ls -la ~/adcp_data/*.lock

# Remove stale locks if no process is running
rm ~/adcp_data/*.lock
```

### Getting Help

If you encounter issues not covered here:

1. Check the [Configuration Guide](CONFIGURATION.md) for setup details
2. Review the [Usage Guide](USAGE.md) for operational guidance
3. See [EXAMPLES.md](EXAMPLES.md) for common scenarios
4. Check the [Deployment Guide](../deployment/DEPLOYMENT.md) for service-related issues
5. Review logs in the output directory
6. Enable debug logging: `adcp-recorder configure --debug`

### Diagnostic Commands

```bash
# System information
python --version
pip list | grep adcp

# Configuration check
adcp-recorder status

# Serial port diagnostics
adcp-recorder list-ports

# Test with debug logging
adcp-recorder configure --debug
adcp-recorder start
```

---

## Next Steps

After successful installation:

1. **Configure the recorder**: See [CONFIGURATION.md](CONFIGURATION.md)
2. **Learn basic usage**: See [USAGE.md](USAGE.md)
3. **Explore examples**: See [EXAMPLES.md](EXAMPLES.md)
4. **Deploy as service**: See [DEPLOYMENT.md](../deployment/DEPLOYMENT.md)

---

**Installation complete!** You're ready to start recording ADCP data.
