# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned

- Additional NMEA message type support
- Web-based monitoring dashboard
- Data export to additional formats (Parquet, NetCDF)

## [0.1.1] - 2026-01-15

### Changed

- **Python 3.13+ required**: Updated minimum Python version to 3.13 for improved performance and modern features
- Windows installation script now auto-installs Python 3.13+ via `winget` if needed
- Linux installation script provides clearer upgrade guidance for Python version

### Fixed

- NMEA telemetry format specification alignment audit
- Various CI/CD improvements and dependency updates
- Windows file handle cleanup timing for better reliability
- Performance test stability improvements for system load variations

### Infrastructure

- Updated GitHub Actions dependencies (checkout v6, setup-python v6, upload-artifact v6, codecov v5, action-gh-release v2)
- Enhanced Windows installer with Visual C++ Redistributable checks
- Improved `pywin32` post-installation configuration

## [0.1.0] - 2026-01-12

### Added

- Initial release of ADCP Recorder
- Support for 21 NMEA message types (PNORI, PNORS, PNORC, PNORH, PNORA, PNORW, PNORB, PNORE, PNORF, PNORWD families)
- Asynchronous serial communication with automatic reconnection
- DuckDB backend for data persistence
- Daily CSV file export per message type
- CLI interface with 5 commands (list-ports, configure, status, start, generate-service)
- Cross-platform support (Linux and Windows)
- Systemd service support (Linux)
- Windows Service support
- Comprehensive NMEA protocol validation and checksum verification
- Binary data detection and error logging
- Health monitoring and graceful shutdown
- Complete user documentation (Installation, Configuration, Usage, Examples)
- Production deployment guide
- Automated installation scripts for Linux and Windows
- Build and packaging scripts
- 100% test coverage for core components
- Performance testing suite
- Integration tests for full pipeline

### Documentation

- Installation guide with platform-specific instructions
- Configuration guide with all parameters documented
- Usage guide with CLI reference and workflows
- Examples guide with 20 practical scenarios
- Deployment guide for production environments
- Architecture documentation
- NMEA protocol specifications
- Database schema documentation

### Infrastructure

- Automated build script with testing and checksums
- Linux installation/uninstallation scripts
- Windows installation/uninstallation scripts
- Enhanced systemd service template with security hardening
- PowerShell service installer for Windows
- GitHub repository setup
- MIT License

## [0.0.1] - Development

### Added

- Initial project structure
- Core NMEA parsing framework
- Basic serial communication
- DuckDB integration

---

[Unreleased]: https://github.com/vpatrinica/adcp-recorder/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/vpatrinica/adcp-recorder/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/vpatrinica/adcp-recorder/releases/tag/v0.1.0
