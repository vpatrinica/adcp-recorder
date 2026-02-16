# Parser Development Guide

## How to Add a New Parser

### 1. Create the parser file

Create `adcp_recorder/parsers/pnorx.py`:

```python
"""PNORX <description> parser."""

from dataclasses import dataclass, field
from typing import Any, cast

from .utils import (
    parse_nmea_sentence,
    parse_optional_float,
    validate_date_mm_dd_yy,  # or validate_date_yy_mm_dd
    validate_range,
    validate_time_string,
)


@dataclass(frozen=True)
class PNORX:
    """PNORX <description>.
    Format: $PNORX,field1,field2,...*CS
    """
    
    date: str
    time: str
    # ... your fields
    checksum: str | None = field(default=None, repr=False)
    
    def __post_init__(self):
        validate_date_mm_dd_yy(self.date)
        validate_time_string(self.time)
        # Add any field-specific validation
    
    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORX":
        res = parse_nmea_sentence(sentence)
        fields, checksum = cast(list[str], res[0]), cast(str | None, res[1])
        
        if fields[0] != "$PNORX":
            raise ValueError(f"Invalid prefix: {fields[0]}")
        
        if len(fields) < EXPECTED_FIELD_COUNT:
            raise ValueError(f"Expected {EXPECTED_FIELD_COUNT} fields, got {len(fields)}")
        
        return cls(
            date=fields[1],
            time=fields[2],
            # ... parse remaining fields
            checksum=checksum,
        )
    
    def to_dict(self) -> dict:
        return {
            "sentence_type": "PNORX",
            "date": self.date,
            "time": self.time,
            # ... all fields
            "checksum": self.checksum,
        }
```

### 2. Register in `__init__.py`

Add your class to `adcp_recorder/parsers/__init__.py`.

### 3. Write tests

Create `adcp_recorder/tests/parsers/test_pnorx.py`. See existing tests for patterns.

**Important test rules:**
- Always compute correct checksums for test sentences (use `fix_tests.py`)
- For f-strings with dynamic values, **omit the checksum** — it can't be pre-computed
- For sentences testing invalid prefixes, **omit the checksum** — checksum validation fires first
- Test NaN handling: `"nan"`, `"-nan"` → `None`
- Test sentinel handling: use the correct format-specific sentinel for each field
  (e.g. `"-9.00"` for `ddd.dd` fields, NOT `"-9.0000"`)
- See `sentinels.py` for the exact sentinel tuples per field

## Shared Utilities (utils.py)

| Function | Purpose |
|----------|---------|
| `parse_nmea_sentence(sentence)` | Split into fields + validate checksum |
| `parse_optional_float(value, sentinels)` | Parse float, return `None` for NaN/empty/sentinel |
| `parse_optional_int(value, sentinels)` | Parse int, return `None` for NaN/empty/sentinel |
| `is_nan_string(value)` | Check if string is NaN (`"nan"`, `"-nan"`, case-insensitive) |
| `parse_tagged_field(field)` | Parse `TAG=VALUE` format |
| `validate_date_mm_dd_yy(date)` | Validate MMDDYY format |
| `validate_date_yy_mm_dd(date)` | Validate YYMMDD format |
| `validate_time_string(time)` | Validate HHMMSS format |
| `validate_hex_string(hex)` | Validate hex string |
| `validate_range(val, name, min, max)` | Validate numeric range |

## Sentinel Values (sentinels.py)

Nortek instruments emit sentinel strings (e.g. `"-9.00"`, `"-999.99"`) to indicate
invalid/missing data. Each field has format-specific sentinels determined by its spec
notation (integer digits + decimal places).

### How to use sentinels in parsers

```python
from .sentinels import get_float_sentinels as _fs
from .sentinels import get_int_sentinels as _is  # only if needed

_p = "PNORX"  # parser prefix, set once at top of from_nmea()

# Single field:
battery=parse_optional_float(fields[5], _fs(_p, "battery")),

# Tagged fields with dynamic names:
field_name = cls.TAG_IDS[tag]
data[field_name] = parse_optional_float(val, _fs(_p, field_name))

# List comprehensions (look up once, reuse):
_ed_sent = _fs(_p, "energy_density")
energies = [parse_optional_float(fields[i], _ed_sent) for i in range(7, n)]

# Integer fields:
num_no_detects=parse_optional_int(fields[17], _is(_p, "num_no_detects")),
```

### How to add sentinels for a new parser

1. Determine the field format from the spec (e.g. `ddd.dd`)
2. Find the matching tuple constant in `sentinels.py` (e.g. `_D3_2`)
3. Add `("PNORX", "field_name"): _D3_2` to `FLOAT_SENTINELS` (or `INT_SENTINELS`)
4. Pass `_fs(_p, "field_name")` at each call site in `from_nmea()`

### Format-to-sentinel mapping

| Constant | Format | Example fields |
|----------|--------|---------------|
| `_D1_1`  | `d.d`  | PNORA pitch/roll |
| `_D1_2`  | `d.dd` | freq_low/high, start/step_frequency |
| `_D2_1`  | `dd.d` | battery, pitch, roll, PNORC distance |
| `_D2_2`  | `dd.dd`| temperature, std_dev, blanking_distance, cell_size |
| `_D2_3`  | `dd.ddd`| velocity (PNORC1/2), speed (PNORC3/4) |
| `_D3_1`  | `ddd.d`| heading, direction, amplitude (dB) |
| `_D3_2`  | `ddd.dd`| wave heights/periods/directions (PNORB/PNORW) |
| `_D3_3`  | `ddd.ddd`| pressure, distance (PNORS/PNORA) |
| `_D4_1`  | `dddd.d`| sound_speed |
| `_D4_3`  | `dddd.ddd`| energy_density (PNORE) |
| `_D4_4`  | `dddd.dddd`| coefficient (PNORF), value (PNORWD) |
| `_INT_WAVE`| integer | num_no_detects, num_bad_detects, num_frequencies |

## Parser Formats

### Positional Parsers (DF=100/200/etc.)
Fields are comma-separated in a fixed order:
```
$PNORB,102115,090715,1,4,0.02,0.20,0.27,7.54,12.00,82.42,75.46,82.10,0000*63
```

### Tagged Parsers (DF=101/201/etc.)
Fields use `TAG=VALUE` format, order-independent:
```
$PNORI2,IT=4,SN=Sig1000,NB=4,NC=20,BD=0.20,CS=1.00,CY=ENU
```

### Variable-Length Parsers
Some parsers (PNORE, PNORF, PNORWD) have variable-length arrays:
```
$PNORE,120720,093150,1,0.02,0.01,10,E1,E2,...,E10*CS
```
The `num_frequencies` field tells how many values follow.
