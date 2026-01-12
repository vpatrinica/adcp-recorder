[🏠 Home](../README.md)

# ADCP Recorder Documentation

Welcome to the ADCP Recorder documentation. This system provides a CLI/control plane and supervised service for recording NMEA-format telemetry from Nortek ADCP instruments into DuckDB.

## 📚 User Guide

**Start here for installation, configuration, and daily usage:**

- [Installation Guide](user-guide/INSTALL.md) - Complete installation instructions for Linux and Windows
- [Configuration Guide](user-guide/CONFIGURATION.md) - Detailed configuration options and environment variables
- [Usage Guide](user-guide/USAGE.md) - CLI commands, workflows, and best practices
- [Examples](user-guide/EXAMPLES.md) - Practical examples and common scenarios

## 🚀 Deployment

**Production deployment and service management:**

- [Deployment Guide](deployment/DEPLOYMENT.md) - Complete deployment procedures for Linux and Windows
  - Service installation and configuration
  - Security considerations
  - Monitoring and maintenance
  - Backup and recovery
  - Upgrade procedures

## Quick Navigation


### 📐 Architecture
- [System Overview](architecture/overview.md) - High-level system design and components
- [Serial Processing](architecture/serial-processing.md) - FIFO producer/consumer pattern
- [DuckDB Integration](architecture/duckdb-integration.md) - Database backend architecture
- [Binary Detection](architecture/binary-detection.md) - Non-NMEA data handling

### 🌊 NMEA Protocol
- [NMEA Overview](nmea/overview.md) - Sentence format and structure
- [Checksum Calculation](nmea/checksum.md) - XOR algorithm details
- [Data Validation](nmea/validation.md) - Validation rules and constraints

### 📋 Message Specifications

#### Configuration Messages
- [PNORI Family](specs/pnori/README.md) - Instrument configuration (PNORI, PNORI1, PNORI2)

#### Sensor Data Messages
- [PNORS Family](specs/pnors/README.md) - Sensor data (PNORS, PNORS1, PNORS2, PNORS3, PNORS4)

#### Current Velocity Messages
- [PNORC Family](specs/pnorc/README.md) - Current velocity (PNORC, PNORC1, PNORC2, PNORC3, PNORC4)
- [PNORH Family](specs/pnorh/README.md) - Header data (PNORH3, PNORH4)

#### Additional Data Messages
- [PNORA](specs/pnora/pnora.md) - Altitude/range data
- [PNORW](specs/pnorw/pnorw.md) - Wave data
- [PNORB](specs/pnorb/pnorb.md) - Bottom tracking data
- [PNORE](specs/pnore/pnore.md) - Echo intensity data
- [PNORF](specs/pnorf/pnorf.md) - Frequency data
- [PNORWD](specs/pnorwd/pnorwd.md) - Wave directional data

[📋 Complete Specs Index](specs/README.md)

### 💻 Implementation Guides

#### Python Implementation
- [Parser Patterns](implementation/python/parsers.md) - Sentence parsing and serialization
- [Dataclass Structures](implementation/python/dataclasses.md) - Immutable data structures
- [Enumerations](implementation/python/enumerations.md) - Type-safe enums
- [Validation](implementation/python/validation.md) - Data validation patterns

#### DuckDB Implementation
- [Schema Patterns](implementation/duckdb/schemas.md) - Table definitions and types
- [Constraints](implementation/duckdb/constraints.md) - CHECK and cross-field constraints
- [Views](implementation/duckdb/views.md) - Views and materialized views
- [Functions](implementation/duckdb/functions.md) - UDFs and stored procedures

[💻 Complete Implementation Guide](implementation/README.md)

### 📝 Examples
- [Parsing Examples](examples/parsing-examples.md) - Complete parsing code examples
- [Validation Examples](examples/validation-examples.md) - Validation and error handling
- [Query Examples](examples/query-examples.md) - DuckDB query patterns

[📝 All Examples](examples/README.md)

## Key Features

- ✅ Asynchronous serial polling with automatic reconnection
- ✅ NMEA checksum validation and frame parsing
- ✅ DuckDB persistence with timestamped raw lines
- ✅ Graceful signal handling and clean shutdown
- ✅ Health monitoring with optional webhook alerting
- ✅ Binary blob detection and separate error logging
- ✅ Daily output files per record type
- ✅ Cross-platform support (Windows/Linux)

## Valid NMEA Prefixes

`PNORC`, `PNORS`, `PNORI`, `PNORC1`, `PNORI1`, `PNORS1`, `PNORC2`, `PNORI2`, `PNORS2`, `PNORA`, `PNORW`, `PNORH3`, `PNORS3`, `PNORC3`, `PNORH4`, `PNORS4`, `PNORC4`, `PNORB`, `PNORE`, `PNORF`, `PNORWD`

## Getting Started

1. **Understand the architecture**: Start with [System Overview](architecture/overview.md)
2. **Learn NMEA protocol**: Review [NMEA Overview](nmea/overview.md)
3. **Explore message types**: Browse [Specifications](specs/README.md)
4. **Implement parsers**: Follow [Implementation Guides](implementation/README.md)
5. **Try examples**: Run code from [Examples](examples/README.md)

---

For detailed technical specifications, see the original [REQUIREMENTS.md](../REQUIREMENTS.md)
