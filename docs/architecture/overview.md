[🏠 Home](../README.md) > Architecture

# System Architecture Overview

The ADCP Recorder is a Python-based system designed to receive, parse, and store NMEA-format telemetry data from Nortek ADCP (Acoustic Doppler Current Profiler) instruments.

## System Components

```
┌─────────────────┐
│  Serial Port    │
│   (COM Port)    │
└────────┬────────┘
         │
         v
┌─────────────────────────────────────────┐
│         Supervised Service              │
│  ┌────────────────────────────────┐    │
│  │   FIFO Producer Thread         │    │
│  │   - Read from serial           │    │
│  │   - Buffer management          │    │
│  │   - Auto reconnection          │    │
│  └──────────┬─────────────────────┘    │
│             v                            │
│  ┌────────────────────────────────┐    │
│  │   Shared FIFO Queue            │    │
│  └──────────┬─────────────────────┘    │
│             v                            │
│  ┌────────────────────────────────┐    │
│  │   FIFO Consumer Thread         │    │
│  │   - Parse NMEA sentences       │    │
│  │   - Validate checksums         │    │
│  │   - Detect binary data         │    │
│  │   - Route to storage           │    │
│  └──────────┬─────────────────────┘    │
└─────────────┼─────────────────────────┘
              │
              v
     ┌────────┴─────────┐
     │                  │
     v                  v
┌─────────┐      ┌────────────┐
│ DuckDB  │      │ Daily Files│
│ Tables  │      │  (*.dat)   │
└─────────┘      └────────────┘
     │                  │
     v                  v
┌─────────┐      ┌────────────┐
│Raw Lines│      │ Per-Type   │
│Parsed   │      │ Records    │
│Records  │      │PNORI_*.dat │
│Errors   │      │PNORS_*.dat │
└─────────┘      │PNORC_*.dat │
                 └────────────┘
```

## CLI/Control Plane

The command-line interface provides control over the recording system:

### Available Commands

- **List COM Ports**: Enumerate available serial ports
- **Configure Port**: Set COM port to listen on
- **Configure Settings**: Set baud rate, parity, data bits, stop bits
- **Set Output Folder**: Configure data report directory
- **Start/Stop/Restart**: Control the recorder service

## Supervised Service

The service runs continuously with these responsibilities:

### Monitoring
- Health checks on serial connection
- Heartbeat tracking for producer and consumer threads
- Automatic restart on failure (configurable)

### Data Flow
1. **Producer**: Reads from serial port, fills FIFO queue
2. **Consumer**: Processes FIFO queue, parses sentences, stores data

### Error Handling
- Automatic serial reconnection on disconnect
- Graceful degradation on parse errors
- Binary data detection and isolation

## Storage Architecture

### DuckDB Backend

**Raw Lines Table**: All received data with metadata
- Timestamp of reception
- Raw sentence text
- Parse status flag (OK/FAIL)
- Detected record type (or ERROR)

**Record Type Tables**: Parsed data by message type
- One table per NMEA message family
- Structured fields from parsed sentences
- Validation flags

**Error Table**: Unparseable sentences
- Parse error details
- Malformed sentence text
- Error classification

### Daily File Output

Configurable output to daily files per record type:

```
data_report/PNORI_2025_12_30.dat
data_report/PNORC_2025_12_30.dat
data_report/PNORS_2025_12_30.dat
...
```

## Key Features

- **Asynchronous I/O**: Non-blocking serial communication
- **Thread Safety**: Producer/consumer pattern with FIFO queue
- **Resilience**: Auto-reconnection and restart capabilities
- **Validation**: Checksum verification and field validation
- **Binary Detection**: Automatic switch to binary blob recording
- **Performance**: Efficient buffering and batched database writes
- **Observability**: Structured logging to stderr
- **Cross-Platform**: Runs on Windows and Linux

## Related Documents

- [Serial Processing Details](serial-processing.md)
- [DuckDB Integration](duckdb-integration.md)
- [Binary Detection](binary-detection.md)
- [NMEA Protocol Overview](../nmea/overview.md)

---

[⬆️ Back to Documentation](../README.md)
