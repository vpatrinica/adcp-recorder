# Project Architecture

## Directory Structure

```
adcp_recorder/
├── core/              # Core utilities shared across project
│   ├── nmea.py        # NMEA checksum computation & validation
│   └── enums.py       # InstrumentType, CoordinateSystem, etc.
│
├── parsers/           # NMEA sentence parsers (one per sentence type)
│   ├── __init__.py    # Re-exports all parser classes
│   ├── utils.py       # Shared parsing utilities (parse_nmea_sentence, validators)
│   ├── sentinels.py   # Per-field sentinel value registry (invalid/no-data markers)
│   ├── pnori.py       # PNORI/PNORI2 — Instrument configuration
│   ├── pnors.py       # PNORS — System status (battery, heading, pitch, roll)
│   ├── pnora.py       # PNORA — Altimeter/pressure data
│   ├── pnorb.py       # PNORB — Wave parameter summary
│   ├── pnorc.py       # PNORC/1/2/3/4 — Current profiles (cell-based velocity data)
│   ├── pnore.py       # PNORE — Wave energy density spectra
│   ├── pnorf.py       # PNORF — Fourier coefficient spectra
│   ├── pnorh.py       # PNORH/3 — Hardware/heading data
│   ├── pnorw.py       # PNORW — Full wave statistics
│   └── pnorwd.py      # PNORWD — Wave directional spectra
│
├── serial/            # Serial port communication
│   └── consumer.py    # Real-time NMEA sentence consumer
│
├── ui/                # Dashboard UI (Dash/Plotly)
│   └── components/    # UI components (spectrum plots, table views, etc.)
│
└── tests/             # Test suites
    └── parsers/       # Parser-specific tests (one per parser file)
```

## Data Flow

```
Serial Port → consumer.py → Parser.from_nmea(sentence) → Dataclass → .to_dict() → Parquet/Dashboard
```

1. **Serial consumer** reads raw NMEA sentences from the instrument
2. **Parsers** validate + parse each sentence into a frozen `@dataclass`
3. Parsed data is converted to `dict` for storage or display
4. **Parquet writer** saves to columnar Parquet files
5. **Dashboard UI** reads from Parquet for visualization

## Parser Design Pattern

Every parser follows the same pattern:

```python
@dataclass(frozen=True)
class PNORX:
    field1: str
    field2: float | None
    checksum: str | None = field(default=None, repr=False)
    
    def __post_init__(self):
        # Validation (dates, ranges, required fields)
        ...
    
    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORX":
        # 1. Parse via parse_nmea_sentence(sentence)
        # 2. Validate prefix
        # 3. Extract fields
        # 4. Return frozen dataclass
        ...
    
    def to_dict(self) -> dict:
        # Convert to dict for serialization
        ...
```

## Key Design Decisions

- **Frozen dataclasses**: All parser outputs are immutable
- **Optional fields**: Many NMEA fields are optional; we use `float | None` with `parse_optional_float()`
- **NaN handling**: `"nan"`, `"-nan"`, `""` → `None` (via `is_nan_string()`)
- **Sentinel handling**: Format-specific sentinel strings (e.g. `"-9.00"`, `"-999.99"`) → `None`.
  Each `(parser, field)` pair has its own sentinel tuple registered in `parsers/sentinels.py`.
  Sentinels are passed explicitly to `parse_optional_float()` and `parse_optional_int()`.
- **Checksum validation**: Centralized in `parse_nmea_sentence()` — validates if present, optional if absent
- **Date formats**: PNORB/PNORS/PNORC use MMDDYY; PNORE/PNORF/PNORWD use YYMMDD
