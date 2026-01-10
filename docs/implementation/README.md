[🏠 Home](../README.md) > Implementation

# Implementation Guides

Practical guides for implementing NMEA parsers and DuckDB integration.

## Python Implementation

### Parser Development
- [Parser Patterns](python/parsers.md) - Factory methods and sentence parsing
- [Dataclass Structures](python/dataclasses.md) - Immutable data structures
- [Enumerations](python/enumerations.md) - Type-safe enum patterns
- [Validation](python/validation.md) - Field and cross-field validation

### Key Patterns

**Frozen Dataclasses**: Immutable, thread-safe data structures
```python
@dataclass(frozen=True)
class PNORI:
    instrument_type: InstrumentType
    # ... fields
```

**Post-Init Validation**: Automatic validation after initialization
```python
def __post_init__(self):
    self._validate_fields()
```

**Factory Methods**: Parse from NMEA sentences
```python
@classmethod
def from_nmea(cls, sentence: str) -> 'PNORI':
    # Parse and return instance
```

## DuckDB Implementation

### Database Design
- [Schema Patterns](duckdb/schemas.md) - Table definitions and type mapping
- [Constraints](duckdb/constraints.md) - CHECK and cross-field constraints
- [Views](duckdb/views.md) - Normalized and materialized views
- [Functions](duckdb/functions.md) - UDFs and stored procedures

### Key Patterns

**Domain Constraints**: Validate data at database level
```sql
CHECK (temperature BETWEEN -5.0 AND 50.0)
```

**Cross-Field Validation**: Complex business rules
```sql
CONSTRAINT valid_signature_config CHECK (
    NOT (instrument_type_code = 4 AND beam_count != 4)
)
```

**Materialized Views**: Pre-computed aggregations
```sql
CREATE MATERIALIZED VIEW mv_stats AS
SELECT ... FROM table GROUP BY ...;
```

## Quick Start

1. **Define data structure**: Create frozen dataclass with validation
2. **Implement parser**: Add `from_nmea()` class method
3. **Add serialization**: Implement `to_nmea()` instance method
4. **Create DB schema**: Define table with constraints
5. **Test round-trip**: Verify parse → serialize → parse

## Related Documents

- [NMEA Protocol](../nmea/overview.md)
- [Message Specifications](../specs/README.md)
- [Examples](../examples/README.md)

---

[🏠 Back to Documentation](../README.md)
