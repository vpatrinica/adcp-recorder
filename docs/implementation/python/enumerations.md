[🏠 Home](../../README.md) > [Implementation](../README.md) > Python

# Enumeration Patterns

Type-safe enumeration patterns for NMEA message fields.

## IntEnum Pattern

```python
from enum import IntEnum

class InstrumentType(IntEnum):
    """Instrument type codes."""
    AQUADOPP = 0
    AQUADOPP_PROFILER = 2
    SIGNATURE = 4
    
    @classmethod
    def from_code(cls, code: int) -> 'InstrumentType':
        """Parse from numeric code with validation."""
        try:
            return cls(code)
        except ValueError:
            raise ValueError(f"Invalid instrument type: {code}")
    
    @property
    def beam_constraint(self) -> tuple[int, ...]:
        """Valid beam counts for this instrument."""
        if self == InstrumentType.SIGNATURE:
            return (4,)
        return (1, 2, 3)
```

## String Enum Pattern

```python
from enum import Enum

class CoordinateSystem(Enum):
    """Coordinate system enumeration."""
    ENU = "ENU"
    XYZ = "XYZ"
    BEAM = "BEAM"
    
    @classmethod
    def from_value(cls, value: str | int) -> 'CoordinateSystem':
        """Parse from string or numeric code."""
        if isinstance(value, str):
            value = value.upper()
            try:
                return cls(value)
            except ValueError:
                # Try numeric mapping
                mapping = {"0": cls.ENU, "1": cls.XYZ, "2": cls.BEAM}
                if value in mapping:
                    return mapping[value]
                raise ValueError(f"Invalid coord system: {value}")
        else:
            # Integer code
            mapping = {0: cls.ENU, 1: cls.XYZ, 2: cls.BEAM}
            if value in mapping:
                return mapping[value]
            raise ValueError(f"Invalid coord system code: {value}")
    
    def to_numeric_code(self) -> int:
        """Convert to numeric code."""
        mapping = {self.ENU: 0, self.XYZ: 1, self.BEAM: 2}
        return mapping[self]
```

## Bitmask Enum Pattern

```python
from enum import IntFlag

class ErrorCode(IntFlag):
    """Error code bitmask."""
    NO_ERROR = 0x00
    TEMPERATURE_ERROR = 0x01
    PRESSURE_ERROR = 0x02
    COMPASS_ERROR = 0x04
    TILT_ERROR = 0x08
    BATTERY_LOW = 0x10
    
    @classmethod
    def from_hex(cls, hex_str: str) -> set['ErrorCode']:
        """Parse hex string to set of error flags."""
        value = int(hex_str, 16)
        errors = set()
        for error in cls:
            if value & error:
                errors.add(error)
        return errors
```

## Usage Examples

```python
# IntEnum
inst_type = InstrumentType.from_code(4)
print(inst_type.name)  # "SIGNATURE"
print(inst_type.value)  # 4
print(inst_type.beam_constraint)  # (4,)

# String Enum
coord_sys = CoordinateSystem.from_value("ENU")
print(coord_sys.value)  # "ENU"
print(coord_sys.to_numeric_code())  # 0

# Bitmask  
errors = ErrorCode.from_hex("00000005")
print(errors)  # {TEMPERATURE_ERROR, TILT_ERROR}
```

## Related Documents

- [Parser Patterns](parsers.md)
- [Dataclass Structures](dataclasses.md)
- [Validation Patterns](validation.md)

---

[⬆️ Back to Implementation](../README.md) | [🏠 Home](../../README.md)
