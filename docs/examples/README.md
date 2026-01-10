[🏠 Home](../README.md) > Examples

# Code Examples

Practical examples for parsing, validating, and querying NMEA data.

## Quick Examples

### Parse a PNORI Sentence

```python
from parsers import PNORI

sentence = "$PNORI,4,Signature1000900001,4,20,0.20,1.00,0*2E"
pnori = PNORI.from_nmea(sentence)

print(f"Instrument: {pnori.instrument_type.name}")
print(f"Serial: {pnori.head_id}")
print(f"Cells: {pnori.cell_count}")
```

### Validate and Store

```python
import duckdb

conn = duckdb.connect('adcp_data.db')

# Parse and validate
pnori = PNORI.from_nmea(sentence)
is_valid = pnori.validate_checksum()

# Insert to database
conn.execute("""
    INSERT INTO pnori_configurations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", [
    uuid4(),
    pnori.instrument_type.name,
    pnori.instrument_type.value,
    pnori.head_id,
    # ... etc
])
```

### Query Statistics

```sql
-- Daily record counts
SELECT 
    DATE(received_at) as date,
    sentence_type,
    COUNT(*) as records
FROM raw_lines
WHERE parse_status = 'OK'
GROUP BY DATE(received_at), sentence_type
ORDER BY date DESC;
```

## Detailed Examples

For comprehensive examples, see:

- [Parsing Examples](parsing-examples.md) - Complete parsing workflows
- [Validation Examples](validation-examples.md) - Validation and error handling
- [Query Examples](query-examples.md) - DuckDB query patterns

## Related Documents

- [Python Parsers](../implementation/python/parsers.md)
- [DuckDB Schemas](../implementation/duckdb/schemas.md)
- [Message Specifications](../specs/README.md)

---

[🏠 Back to Documentation](../README.md)
