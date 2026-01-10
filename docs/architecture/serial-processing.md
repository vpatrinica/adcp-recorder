[🏠 Home](../README.md) > [Architecture](overview.md)

# Serial Processing Details

The serial processing subsystem uses a producer-consumer pattern with a FIFO queue to decouple data acquisition from parsing.

## Initialization Sequence

```python
init_setup:
   init_logging()
   init_rx_buffer()
   init_fifo()
   test_output_folder(fallback=./data folder in the application root folder)
   configure_duckdb()
   connect_to_duckdb()
   configure_serial()
   connect_to_serial()
   non_nmea_rx_counter=0
   non_nmea_cons_recs=0
   carry_over_payload=""
```

## FIFO Producer Loop

The producer thread continuously reads from the serial port and fills the FIFO queue.

```python
fifo_producer_loop:
    heartbeat_fifo_producer()
    check_on_rx()
    while receive_buffer not empty:
         receive-line-or-chunk(max length 2048 or CRLF)
         fill_fifo(append to end)
    sleep()
```

### Producer Responsibilities

- **Heartbeat Monitoring**: Periodic health check signals
- **Serial Port Polling**: Check for available data
- **Buffering**: Read up to 2048 bytes or until CRLF
- **Queue Management**: Append received data to FIFO
- **Reconnection**: Detect and recover from serial disconnects

## FIFO Consumer Loop

The consumer thread processes the FIFO queue, parsing and validating NMEA sentences.

```python
fifo_consumer_loop:
     heartbeat_fifo_consumer()
     check_fifo()
     if not empty fifo:
         payload = fifo.pop()
         payload = (carry_over_payload + payload)
         find_nmea_id()        # find first comma
         find_checksum_sep()   # find * separator
         find_checksum_value() # extract checksum
         find_prefix_checksum() # validate prefix
         
         non_nmea_chars = scan_for_nonnmea(payload)
         # if non_nmea_chars > MAX_NON_NMEA_CHARS_PER_LINE
         process()

def process(buffer):
     # parse_sentence...
```

### Consumer Responsibilities

- **Heartbeat Monitoring**: Periodic health check signals
- **Queue Processing**: Pop payloads from FIFO
- **Carry-Over Handling**: Manage incomplete sentences across buffers
- **NMEA Frame Detection**: Identify sentence boundaries
- **Checksum Validation**: Verify data integrity
- **Binary Detection**: Identify non-printable characters
- **Parsing**: Convert sentences to structured data
- **Storage Routing**: Save to DuckDB or daily files

## Buffer Management

### Receive Buffer

- **Size**: 2048 bytes maximum per read
- **Termination**: CRLF sequence or max length
- **Overflow**: Partial sentences carried over to next iteration

### FIFO Queue

- **Thread-Safe**: Lock-free or mutex-protected queue
- **Bounded**: Configurable maximum depth to prevent memory exhaustion
- **Backpressure**: Producer blocks when queue is full

### Carry-Over Payload

Handles incomplete sentences split across buffer reads:

1. Previous iteration ends mid-sentence
2. Fragment stored in `carry_over_payload`
3. Next iteration prepends fragment to new data
4. Complete sentence then parsed

**Example**:
```
Read 1: "$PNORI,4,Signature10009000"
Read 2: "01,4,20,0.20,1.00,0*2E\r\n"

Payload = carry_over + new_data
        = "$PNORI,4,Signature1000900001,4,20,0.20,1.00,0*2E"
```

## Reconnection Logic

### Serial Disconnect Detection

- Read returns 0 bytes repeatedly
- Serial port exception raised
- Heartbeat timeout from producer

### Reconnection Procedure

1. Log disconnect event
2. Close serial port handle
3. Wait for reconnection delay (configurable)
4. Attempt to reopen serial port
5. Reset buffers and counters
6. Resume producer loop

### Configurable Parameters

- **Reconnection delay**: Time to wait before retry (default: 5 seconds)
- **Max retries**: Number of reconnection attempts (0 = infinite)
- **Timeout**: Serial read timeout (default: 1 second)

## Heartbeat Mechanism

### Purpose

Monitor thread health and detect deadlocks or infinite loops.

### Implementation

**Producer Heartbeat**:
```python
def heartbeat_fifo_producer():
    producer_last_heartbeat = current_timestamp()
    log_debug("Producer heartbeat")
```

**Consumer Heartbeat**:
```python
def heartbeat_fifo_consumer():
    consumer_last_heartbeat = current_timestamp()
    log_debug("Consumer heartbeat")
```

**Monitoring**:
```python
def check_thread_health():
    now = current_timestamp()
    if (now - producer_last_heartbeat) > HEARTBEAT_TIMEOUT:
        log_error("Producer thread deadlock detected")
        trigger_restart()
    if (now - consumer_last_heartbeat) > HEARTBEAT_TIMEOUT:
        log_error("Consumer thread deadlock detected")
        trigger_restart()
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
