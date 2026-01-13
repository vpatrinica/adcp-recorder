# ADCP Recorder

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://github.com/vpatrinica/adcp-recorder/workflows/Tests/badge.svg)](https://github.com/vpatrinica/adcp-recorder/actions/workflows/tests.yml)
[![Build](https://github.com/vpatrinica/adcp-recorder/workflows/Build/badge.svg)](https://github.com/vpatrinica/adcp-recorder/actions/workflows/build.yml)
[![Code Quality](https://github.com/vpatrinica/adcp-recorder/workflows/Code%20Quality/badge.svg)](https://github.com/vpatrinica/adcp-recorder/actions/workflows/code-quality.yml)

**ADCP Recorder** is a production-ready NMEA telemetry recorder for Nortek ADCP (Acoustic Doppler Current Profiler) instruments with a DuckDB backend. It provides reliable, high-performance data collection with comprehensive parsing, validation, and storage capabilities.

## Features

- ✅ **Asynchronous Serial Communication** - Non-blocking serial port polling with automatic reconnection
- ✅ **NMEA Protocol Support** - Full checksum validation and frame parsing for 21+ message types
- ✅ **DuckDB Persistence** - Embedded database with timestamped raw lines and parsed data
- ✅ **Graceful Signal Handling** - Clean shutdown on SIGTERM/SIGINT
- ✅ **Health Monitoring** - Built-in health checks with optional webhook alerting
- ✅ **Binary Data Detection** - Separate error logging for non-NMEA data
- ✅ **Daily File Export** - Automatic CSV export per message type
- ✅ **Cross-Platform** - Full support for Linux and Windows
- ✅ **Service Integration** - Systemd (Linux) and Windows Service support
- ✅ **Production Ready** - Comprehensive testing, logging, and error handling

## Supported NMEA Message Types

**Configuration**: PNORI, PNORI1, PNORI2  
**Sensor Data**: PNORS, PNORS1, PNORS2, PNORS3, PNORS4  
**Current Velocity**: PNORC, PNORC1, PNORC2, PNORC3, PNORC4  
**Headers**: PNORH3, PNORH4  
**Additional**: PNORA, PNORW, PNORB, PNORE, PNORF, PNORWD

## Quick Start

### Installation

```bash
# Install from PyPI (recommended)
pip install adcp-recorder

# Or install from source
git clone https://github.com/your-org/adcp-recorder.git
cd adcp-recorder
pip install .
```

### Basic Usage

```bash
# List available serial ports
adcp-recorder list-ports

# Configure the recorder
adcp-recorder configure --port /dev/ttyUSB0 --baud 9600 --output ~/adcp_data

# Check configuration
adcp-recorder status

# Start recording
adcp-recorder start
```

Press `Ctrl+C` to stop the recorder.

## Documentation

### User Guides

- **[Installation Guide](docs/user-guide/INSTALL.md)** - Complete installation instructions for Linux and Windows
- **[Configuration Guide](docs/user-guide/CONFIGURATION.md)** - Detailed configuration options and examples
- **[Usage Guide](docs/user-guide/USAGE.md)** - CLI commands, workflows, and best practices
- **[Examples](docs/user-guide/EXAMPLES.md)** - Practical examples and common scenarios

### Deployment

- **[Deployment Guide](docs/deployment/DEPLOYMENT.md)** - Production deployment, service setup, and maintenance

### Technical Documentation

- **[Architecture Overview](docs/architecture/overview.md)** - System design and components
- **[NMEA Protocol](docs/nmea/overview.md)** - NMEA sentence format and validation
- **[Message Specifications](docs/specs/README.md)** - Detailed specs for all message types
- **[Implementation Guides](docs/implementation/README.md)** - Parser patterns and database schemas

### Complete Documentation

Browse the full documentation at [docs/README.md](docs/README.md)

## System Requirements

- **Python**: 3.9 or higher
- **Operating System**: Linux (Ubuntu 20.04+, Debian 11+, RHEL 8+) or Windows 10/11
- **RAM**: 512 MB minimum, 1 GB recommended
- **Disk Space**: 100 MB for application, additional space for data storage
- **Serial Port**: USB-to-serial adapter or native serial port

## Installation Methods

### Method 1: PyPI (Recommended for Production)

```bash
pip install adcp-recorder
```

### Method 2: From Source

```bash
git clone https://github.com/your-org/adcp-recorder.git
cd adcp-recorder
pip install .
```

### Method 3: Development Installation

```bash
git clone https://github.com/your-org/adcp-recorder.git
cd adcp-recorder
pip install -e ".[dev]"
pytest  # Run tests
```

## Production Deployment

### Linux (Systemd Service)

```bash
# Automated installation
sudo ./scripts/install-linux.sh

# Or manual installation
sudo cp adcp_recorder/templates/linux/adcp-recorder.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable adcp-recorder
sudo systemctl start adcp-recorder
```

### Windows (Windows Service)

```cmd
REM Automated installation (run as Administrator)
install-windows.bat

REM Or manual service installation
python -m adcp_recorder.service.win_service install
sc config adcp-recorder start= auto
sc start adcp-recorder
```

See [Deployment Guide](docs/deployment/DEPLOYMENT.md) for complete instructions.

## CLI Commands

```bash
# List available serial ports
adcp-recorder list-ports

# Configure settings
adcp-recorder configure [OPTIONS]
  --port TEXT          Serial port device
  --baud INTEGER       Baud rate
  --output TEXT        Output directory
  --debug/--no-debug   Enable/disable debug logging

# Show current status
adcp-recorder status

# Start recording
adcp-recorder start

# Generate service templates
adcp-recorder generate-service --platform {linux|windows}
```

## Data Access

### Database Queries

```bash
# Connect to database
duckdb ~/adcp_data/adcp.duckdb

# Query examples
SELECT COUNT(*) FROM raw_lines;
SELECT * FROM pnors ORDER BY timestamp DESC LIMIT 10;
SELECT AVG(temperature) FROM pnors WHERE temperature IS NOT NULL;
```

### CSV Files

Daily CSV files are automatically exported to `{output_dir}/{MESSAGE_TYPE}/{YYYY-MM-DD}.csv`

```bash
# View today's sensor data
cat ~/adcp_data/PNORS/$(date +%Y-%m-%d).csv
```

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=adcp_recorder --cov-report=html

# Run specific test file
pytest adcp_recorder/tests/test_nmea.py
```

### Code Quality

```bash
# Linting (using ruff)
ruff check adcp_recorder/

# Type checking
mypy adcp_recorder/

# Code formatting
ruff format adcp_recorder/
```

### Building Distribution

```bash
# Build package
./scripts/build.sh

# This will:
# - Run tests
# - Generate coverage reports
# - Build wheel and source distributions
# - Generate checksums
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    ADCP Recorder                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Serial Port  →  Producer  →  Queue  →  Consumer       │
│                                           ↓             │
│                                      Message Router     │
│                                           ↓             │
│                                  ┌────────┴────────┐   │
│                                  ↓                 ↓   │
│                            DuckDB Database    CSV Files│
│                                                         │
└─────────────────────────────────────────────────────────┘
```

See [Architecture Overview](docs/architecture/overview.md) for details.

## Configuration

Configuration is stored in `~/.adcp-recorder/config.json`:

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

Environment variables can override configuration:

```bash
export ADCP_RECORDER_SERIAL_PORT=/dev/ttyUSB1
export ADCP_RECORDER_BAUDRATE=115200
export ADCP_RECORDER_OUTPUT_DIR=/data/adcp
```

See [Configuration Guide](docs/user-guide/CONFIGURATION.md) for all options.

## Monitoring

### Service Status

```bash
# Linux
sudo systemctl status adcp-recorder
sudo journalctl -u adcp-recorder -f

# Windows
sc query adcp-recorder
Get-EventLog -LogName Application -Source adcp-recorder -Newest 20
```

### Health Checks

```bash
# Check data collection rate
duckdb ~/adcp_data/adcp.duckdb \
  "SELECT COUNT(*) FROM raw_lines WHERE timestamp > NOW() - INTERVAL 5 MINUTES"

# Check for errors
duckdb ~/adcp_data/adcp.duckdb \
  "SELECT * FROM errors ORDER BY timestamp DESC LIMIT 10"
```

## Troubleshooting

### Common Issues

**Serial port permission denied (Linux)**:
```bash
sudo usermod -a -G dialout $USER
# Log out and log back in
```

**Service won't start**:
```bash
# Check logs
sudo journalctl -u adcp-recorder -n 50

# Verify configuration
adcp-recorder status

# Test manually
adcp-recorder start
```

**No data being collected**:
```bash
# Enable debug logging
adcp-recorder configure --debug
adcp-recorder start

# Check serial port
adcp-recorder list-ports
```

See [Usage Guide](docs/user-guide/USAGE.md#error-handling-and-recovery) for more troubleshooting.

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Setup

```bash
git clone https://github.com/your-org/adcp-recorder.git
cd adcp-recorder
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [docs/README.md](docs/README.md)
- **Issues**: [GitHub Issues](https://github.com/your-org/adcp-recorder/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/adcp-recorder/discussions)

## Acknowledgments

- Nortek for ADCP instruments and NMEA specifications
- DuckDB for the embedded database engine
- The Python community for excellent libraries

---

**Built with ❤️ for oceanographic research and marine monitoring**
