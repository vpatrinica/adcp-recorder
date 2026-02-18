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
├── ui/                # Dashboard UI (Streamlit/Plotly)
│   ├── data_layer.py  # DataLayer: query abstraction over DuckDB
│   ├── parquet_data_layer.py  # ParquetDataLayer: in-memory DuckDB over Parquet files
│   ├── config.py      # PanelType, DashboardConfig, panel configs (Pydantic)
│   ├── dashboard.py   # Dashboard renderer (dispatches panels by PanelType)
│   ├── components/    # Visualization components
│   │   ├── wave_rose.py           # Polar scatter: Hm0 vs DirTp, colored by Tp
│   │   ├── current_profile_plots.py  # Current speed heatmap + direction polar
│   │   ├── spectrum_plots.py      # Fourier, energy, directional, amplitude heatmaps
│   │   ├── velocity_profile.py    # Depth-velocity profiles
│   │   ├── time_series.py         # Generic time series plots
│   │   └── table_view.py          # Tabular data display
│   └── pages/         # Full-page views
│       ├── plot_builder.py        # Interactive plot creation (9 plot types)
│       ├── data_explorer.py       # Data browsing
│       └── dashboard_editor.py    # Dashboard layout editing
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
- **NaN handling**: `"nan"`, `"-nan"`, `""` → `None` (via `is_nan_string()`).
- **Checksum validation**: Centralized in `parse_nmea_sentence()` — validates if present, optional if absent
- **Date formats**: PNORB/PNORS/PNORC use MMDDYY; PNORE/PNORF/PNORWD use YYMMDD

## UI / Dashboard Architecture

### Data Layers
- **`DataLayer`**: Wraps a DuckDB connection. Provides `get_available_sources()`,
  `query_data()`, `query_time_series()`, `query_wave_rose_data()`,
  `query_current_speed_heatmap()`, `detect_current_profile_view()`, etc.
- **`ParquetDataLayer`**: Inherits from `DataLayer`. Creates an in-memory DuckDB,
  registers Parquet files as views (`pq_{record_type}`), and creates joined views
  matching the DuckDB schema names (`wave_measurement_full`, `current_profile_12`, etc.).
- **`resolve_source_name()`**: Maps DuckDB table/view names to Parquet view names,
  ensuring the same queries work against either backend.

### Auto-Detection Pattern
Current profile visualizations use `DataLayer.detect_current_profile_view()` instead of
manual source selection. This method checks views in priority order and returns the first
with data:

```
current_profile_12 > current_profile_df100 > current_profile_34 > pnorc12 > pnorc_df100 > pnorc34
```

Components using auto-detection: `velocity_profile.py`, `current_profile_plots.py`,
`spectrum_plots.py` (amplitude heatmap).

### Fixed Data Sources per Plot Type
Each plot type uses a known, fixed data source — no free-form source selection:

| Plot Type | Fixed Source(s) |
|-----------|----------------|
| Wave Rose | `wave_measurement_full` or `pnorb_data` |
| Current Speed Heatmap | Auto-detected current profile view |
| Current Direction Polar | Auto-detected current profile view |
| Amplitude Heatmap | Auto-detected current profile view |
| Fourier Spectrum | `pnorf_data` |
| Energy Heatmap | `pnore_data` |
| Directional Spectrum | `pnore_data` + `pnorwd_data` |
| Velocity Profile | Auto-detected current profile view |

### Plot Builder
`pages/plot_builder.py` provides interactive plot creation for all 9 panel types.
Each builder is a thin wrapper calling the component's `render_*()` function with
`config=None` and a unique `key_prefix`. Save-to-dashboard extracts session state
into a `PanelConfig` and appends it to the selected `DashboardConfig`.
