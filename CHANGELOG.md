# Changelog

<!-- markdownlint-disable MD024 -->

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

- Directional spectrum polar plots for wave analysis

## [0.2.1] - 2026-01-24

### Added

- **Stale File Monitoring**: Robust retry mechanism for Parquet files stuck in `.writing` state.
- **Robust Error Handling**: Improved handling of database and Parquet locks in the dashboard with user-friendly messages.

### Changed

- **Improved UI Defaults**:
  - Parquet File Browser is now collapsed by default.
  - Selecting "Parquet Files" data source automatically loads available data.
- **Dependencies**: Moved `numpy` from optional to core dependencies.

### Fixed

- **Type Safety**: Resolved 150+ Mypy type errors across the codebase.
- **Parquet Scanning**: Fixed `OSError` during directory scanning when folders are missing.
- **Testing**: Fixed migration warnings, DuckDB locking issues in tests, and improved test isolation.
- **Coverage**: Achieved 100% test coverage for key UI components (`velocity_profile`, `spectrum_plots`).

## [0.2.0] - 2026-01-18

### Added

- **Database Schema Consolidation**: Unified disparate tables into consolidated families for simpler management and better performance.
  - Consolidated `pnori1`, `pnori2` into `pnori12` with `data_format` discriminator.
  - Consolidated `pnors_df101`, `pnors_df102` into `pnors12`.
  - Consolidated `pnors_df103`, `pnors_df104` into `pnors34`.
  - Consolidated `pnorc_df101`, `pnorc_df102` into `pnorc12`.
  - Consolidated `pnorc_df103`, `pnorc_df104` into `pnorc34`.
  - Consolidated `pnorh_df103`, `pnorh_df104` into `pnorh`.
- **Database Migration Tool**: New `adcp_recorder.db.migration` module to transition existing databases to the consolidated schema.
- **Wave Spectrum Renaming**: Renamed `echo_data` to `pnore_data` to match NMEA family naming conventions.

### Changed

- Updated database insertion logic and query operations to work with consolidated tables.
- Standardized wave parameter field names in `pnorw_data` (e.g., `mean_dir` to `main_dir`, `peak_dir` to `dir_tp`).
- Improved SQL query efficiency using DuckDB's `UNNEST` and index-based joins in consolidated views.

### Breaking Changes

> [!IMPORTANT]
> This version introduces significant database schema changes. Users with existing databases MUST run the migration tool:
> `uv run python -m adcp_recorder.db.migration path/to/adcp.duckdb`

## [0.1.7] - 2026-01-16

### Added

- **Advanced Scientist Dashboard**: Complete rewrite of the Streamlit dashboard with multi-page architecture
  - **Data Explorer**: Browse all 21+- **Unified Data Access Layer**: Thread-safe DuckDB connection handling and generic query API.
- **Interactive Visualizations**: Time Series, Velocity Profiles, Fourier Spectra, and Wave Energy Heatmaps.
- **Directional Spectrum Polar Plots**: Full implementation of wave direction distribution visualizations.
- **Persistable Dashboards**: JSON/YAML-based dashboard persistence with multiple panel types.hboard configurations with YAML persistence
  - **Pre-built Templates**: Overview, Velocity Analysis, and Wave Analysis dashboards ready to use
- **Persistent Dashboard Configuration**: YAML-based config files stored in `~/.adcp-recorder/dashboards/`
- **Pydantic Configuration Models**: Type-safe panel, layout, and series configuration with validation
- **Unified Data Access Layer**: Abstraction over all database tables with column metadata, time-range queries, and aggregation
- **Specialized Visualizations**:
  - Fourier coefficient spectrum plots (A1, B1, A2, B2)
  - Velocity profile depth plots with beam color coding
  - Wave energy density heatmaps with configurable color scales
  - Multi-series time plots with interactive builder

### Changed

- Restructured `dashboard.py` as multi-page Streamlit app with sidebar navigation
- Dashboard now supports saved configurations that persist across sessions

### Dependencies

- Added `pyyaml>=6.0.0` to `[analysis]` optional dependencies

## [0.1.3] - 2026-01-15

### Added

- **DuckLake Architecture**: Transitioned to a multi-layer storage strategy combining DuckDB with partitioned Parquet files.
- **Parquet Storage**: Structured records (PNORS, PNORC, etc.) are now exported to compressed Parquet files in `data/parquet/{prefix}/date={YYYY-MM-DD}/`.
- **FastAPI Data Access**: Introduced a REST API for programmatic access to records, errors, and DuckLake data.
- **Analysis Dashboard**: Integrated a Streamlit-based dashboard for real-time visualization of ADCP profiles, sensor trends, and error analytics.
- **DuckDB Parquet Views**: Automatic creation of DuckDB views (`view_{prefix}`) pointing to Parquet data for seamless querying.

### Changed

- Updated `FileWriter` to coordinate concurrent text (NMEA), binary, and Parquet export.
- Refactored `DatabaseManager` to initialize DuckLake views on startup.
- Enhanced `SerialConsumer` to route structured data to both the database and Parquet storage.

## [0.1.2] - 2026-01-15

### Changed

- **Windows Service now uses Servy**: Replaced pywin32-based Windows service with [Servy](https://github.com/aelassas/servy), a full-featured Windows service wrapper
- Windows service installation now uses `servy-cli install` command with automatic health monitoring, log rotation, and recovery actions
- Simplified Windows installation - no more pywin32 post-install configuration required

### Removed

- Removed pywin32 optional dependency (`[win]` extras no longer needed)
- Deleted `adcp_recorder/service/win_service.py` (pywin32-based service)
- Deleted `scripts/fix-windows-service.bat` and `scripts/test-pywin32.bat` (legacy pywin32 scripts)

### Breaking Changes

> **Windows users upgrading from 0.1.1**: You must uninstall the existing pywin32-based service before upgrading. Then reinstall using the new Servy-based installation scripts.
>
> Upgrade steps:
>
> 1. Stop and remove old service: `sc stop ADCPRecorder && sc delete ADCPRecorder`
> 2. Install Servy: `winget install -e --id aelassas.Servy`
> 3. Run the new `install-windows.bat` as Administrator

### Added

- Servy-based service management with health checks, log rotation, and automatic recovery
- Service logs now written to `C:\ADCP_Data\logs\stdout.log` and `stderr.log` with daily rotation

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

[0.2.0]: https://github.com/vpatrinica/adcp-recorder/compare/v0.1.7...v0.2.0
[0.1.7]: https://github.com/vpatrinica/adcp-recorder/compare/v0.1.3...v0.1.7
[0.1.3]: https://github.com/vpatrinica/adcp-recorder/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/vpatrinica/adcp-recorder/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/vpatrinica/adcp-recorder/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/vpatrinica/adcp-recorder/releases/tag/v0.1.0
