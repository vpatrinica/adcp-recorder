[🏠 Home](../../README.md) > [Implementation](../README.md) > Python

# Validation Patterns

Comprehensive validation patterns for NMEA data.

## Multi-Level Validation

```python
def __post_init__(self):
    """Validate at multiple levels."""
    # Level 1: Type validation (automatic from type hints)
    
    # Level 2: Range validation
    self._validate_ranges()
    
    # Level 3: Format validation
    self._validate_formats()
    
    # Level 4: Cross-field validation
    self._validate_cross_fields()
```

## Range Validation

```python
def _validate_ranges(self) -> None:
    """Validate numeric ranges."""
    if not (0 <= self.battery_voltage <= 30):
        raise ValueError(f"Battery out of range: {self.battery_voltage}")
    
    if not (0 <= self.heading < 360):
        raise ValueError(f"Heading out of range: {self.heading}")
    
    if not (-90 <= self.pitch <= 90):
        raise ValueError(f"Pitch out of range: {self.pitch}")
```

## Format Validation

```python
def _validate_formats(self) -> None:
    """Validate string formats."""
    # Date format: MMDDYY
    if not re.match(r'^\d{6}$', self.date_str):
        raise ValueError(f"Invalid date format: {self.date_str}")
    
    # Hex code format: 8 hex chars
    if not re.match(r'^[0-9A-Fa-f]{8}$', self.error_code):
        raise ValueError(f"Invalid error code: {self.error_code}")
```

## Cross-Field Validation

```python
def _validate_cross_fields(self) -> None:
    """Validate relationships between fields."""
    # Signature must have 4 beams
    if self.instrument_type == InstrumentType.SIGNATURE:
        if self.beam_count != 4:
            raise ValueError("Signature requires 4 beams")
    
    # Blanking < total range
    total_range = self.cell_size * self.cell_count
    if self.blanking_distance >= total_range:
        raise ValueError("Blanking exceeds total range")
```

## Invalid Data Handling

```python
def parse_float_or_invalid(value: str) -> Optional[float]:
    """Parse float, treating -9 variants as invalid."""
    try:
        f = float(value)
        # -9, -9.0, -999, etc. are invalid markers
        if f <= -9:
            return None
        return f
    except ValueError:
        return None
```

## Validation Error Collection

```python
def validate(self) -> tuple[bool, list[str]]:
    """
    Validate and collect all errors.
    
    Returns:
        (is_valid, error_list)
    """
    errors = []
    
    try:
        self._validate_ranges()
    except ValueError as e:
        errors.append(str(e))
    
    try:
        self._validate_formats()
    except ValueError as e:
        errors.append(str(e))
    
    try:
        self._validate_cross_fields()
    except ValueError as e:
        errors.append(str(e))
    
    return len(errors) == 0, errors
```

## Related Documents

- [NMEA Validation Rules](../../nmea/validation.md)
- [Parser Patterns](parsers.md)
- [Dataclass Structures](dataclasses.md)

---

[⬆️ Back to Implementation](../README.md) | [🏠 Home](../../README.md)
