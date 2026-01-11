[🏠 Home](../README.md) > [Architecture](overview.md)

# Serial Processing Details

The serial processing subsystem uses a producer-consumer pattern with a FIFO queue to decouple data acquisition from parsing.

## Initialization Sequence

The system is initialized through the `SerialConnectionManager`, `SerialProducer`, and `SerialConsumer` classes.

```python
# Setup
manager = SerialConnectionManager(port, baudrate=115200)
queue = Queue(maxsize=1000)
db = DatabaseManager(db_path)
router = MessageRouter()
router.register_parser('PNORI', PNORI)
# ... register other parsers ...

# Start
producer = SerialProducer(manager, queue)
consumer = SerialConsumer(queue, db, router)

producer.start()
consumer.start()
```

## FIFO Producer Loop

The `SerialProducer` runs in a background thread, reading from the serial port and pushing data to the queue.

### Producer Responsibilities

- **Connection Management**: Uses `SerialConnectionManager` to handle connections and reconnection.
- **Heartbeat Monitoring**: Updates `last_heartbeat` timestamp on every successful read or reconnection.
- **Serial Port Reading**: Uses `readline()` to get complete sentences.
- **Binary Detection**: Checks for high-bit characters/null bytes using `is_binary_data()`.
- **Queue Management**: Pushes lines as bytes to the FIFO queue.
- **Drop-Oldest Logic**: If the queue is full, the oldest item is discarded to prevent memory bloat.

## FIFO Consumer Loop

The `SerialConsumer` runs in a background thread, pulling from the queue and routing to parsers.

### Consumer Responsibilities

- **Heartbeat Monitoring**: Updates `last_heartbeat` timestamp on every processed line.
- **Queue Processing**: Pulls from the queue with a timeout.
- **Message Routing**: Uses `MessageRouter` to identify NMEA prefixes and select the correct parser.
- **Database Storage**: Calls appropriate `insert_*` functions from `adcp_recorder.db.operations`.
- **Error Tracking**: Logs parse errors and binary data to the `parse_errors` and `raw_lines` tables.

## Buffer Management

### Receive Buffer

- **Implementation**: Handled by `pyserial` and `SerialConnectionManager.read_line()`.
- **Termination**: Line terminators (CRLF) are used to delimit sentences.

### FIFO Queue

- **Thread-Safe**: Uses `queue.Queue` from the standard library.
- **Bounded**: Maximum size is configurable (default: 1000).
- **Backpressure**: Implements "drop-oldest" non-blocking push.

## Reconnection Logic

### Serial Disconnect Detection

- Caught by `SerialException` or `OSError` during read operations.
- Triggers `disconnect()` and sets connection state to closed.

### Reconnection Procedure

1. **Wait and Retry**: Uses exponential backoff (base 2.0, capped at 60s).
2. **Reconnection Attempts**: Tries up to `max_retries` (default: 5) per cycle.
3. **Recovery**: Resumes read operations once a new connection is established.

## Heartbeat Mechanism

### Purpose

Monitor thread health and detect if either thread has stopped processing data.

### Implementation

Both `SerialProducer` and `SerialConsumer` maintain a `last_heartbeat` property that is updated during active processing. A central monitor (e.g., in the control plane) can check these timestamps to detect hangs.

```python
@property
def last_heartbeat(self) -> float:
    """Get timestamp of last heartbeat update."""
    return self._last_heartbeat
```

## Error Handling

### Serial Errors

- **Device not found**: Wait and retry
- **Permission denied**: Log critical error, exit
- **Device busy**: Wait and retry
- **Read timeout**: Continue (normal for idle periods)

### Parse Errors

- **Invalid checksum**: Log to error table, continue
- **Unknown prefix**: Log to error table, continue
- **Malformed sentence**: Log to error table, continue
- **Binary data**: Switch to blob recording mode

### Queue Errors

- **Queue full**: Producer blocks, log warning
- **Queue empty**: Consumer sleeps, normal operation

## Performance Optimization

- **Batch writes**: Accumulate parsed records, write in batches to DuckDB
- **Buffer reuse**: Preallocate buffers to reduce allocations
- **Lazy parsing**: Only parse when consumer has capacity
- **Async I/O**: Use non-blocking serial reads where available

## Related Documents

- [System Overview](overview.md)
- [DuckDB Integration](duckdb-integration.md)
- [Binary Detection](binary-detection.md)
- [NMEA Checksum](../nmea/checksum.md)

---

[⬆️ Back to Architecture](overview.md) | [🏠 Home](../README.md)

See the [alignment protocol log](../quality-reports/alignment-protocol-log.md) for the reality-check notes feeding the tracksheet.

