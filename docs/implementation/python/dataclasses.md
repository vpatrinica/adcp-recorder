[🏠 Home](../../README.md) > [Implementation](../README.md) > Python

# Dataclass Structure Patterns

Patterns for creating immutable, validated data structures.

## Frozen Dataclass Pattern

```python
from dataclasses import dataclass, field
from typing import Optional, ClassVar
import re

@dataclass(frozen=True)
class MessageType:
    """Immutable data structure for NMEA message."""
    
    # Required fields with type hints
    field1: int
    field2: float
    field3: str
    
    # Optional fields with defaults
    checksum: Optional[str] = field(default=None, repr=False)
    
    # Class-level constants
    VALIDATION_PATTERN: ClassVar[re.Pattern] = re.compile(r'^[A-Z0-9]+$')
    MAX_VALUE: ClassVar[int] = 1000
    
    def __post_init__(self):
        """Validate all fields after initialization."""
        self._validate_field1()
        self._validate_field2()
        self._validate_field3()
```

## Post-Init Validation

```python
def __post_init__(self):
    """Validate all fields after initialization."""
    # Type validation (automatic from type hints)
    # Range validation
    if not (0 <= self.field1 <= self.MAX_VALUE):
        raise ValueError(f"field1 out of range: {self.field1}")
    
    # Format validation
    if not self.VALIDATION_PATTERN.match(self.field3):
        raise ValueError(f"Invalid field3 format: {self.field3}")
    
    # Cross-field validation
    if self.field1 > self.field2:
        raise ValueError("field1 must be <= field2")
```

## Private Validation Methods

```python
def _validate_field1(self) -> None:
    """Validate field1 range."""
    if not (0 <= self.field1 <= 1000):
        raise ValueError(f"field1 out of range: {self.field1}")

def _validate_field3(self) -> None:
    """Validate field3 format."""
    if not self.VALIDATION_PATTERN.match(self.field3):
        raise ValueError(f"Invalid field3: {self.field3}")
```

## DuckDB Integration Method

```python
def to_duckdb_dict(self) -> dict:
    """Convert to dictionary for DuckDB insertion."""
    return {
        'field1': self.field1,
        'field2': float(self.field2),
        'field3': self.field3,
        'checksum': self.checksum,
        'checksum_valid': self.validate_checksum() if self.checksum else False
    }
```

## Immutability Benefits

**Thread Safety**: Frozen dataclasses are thread-safe
```python
# Safe to share across threads
shared_config = PNORI.from_nmea(sentence)
```

**Hashable**: Can be used in sets and as dict keys
```python
configs = {config1, config2, config3}  # Set of configs
config_map = {config: timestamp}  # Config as key
```

**Prevents Accidental Mutation**:
```python
config.field1 = 999  # Raises FrozenInstanceError
```

## Related Documents

- [Parser Patterns](parsers.md)
- [Validation Patterns](validation.md)
- [Enumerations](enumerations.md)

---

[⬆️ Back to Implementation](../README.md) | [🏠 Home](../../README.md)
