[🏠 Home](../../README.md) > [📋 Specs](../README.md)

# PNORE Specification

**Wave energy density spectrum message** (DF=501) containing spectral energy distribution data.

## Format

```nmea
$PNORE,Date,Time,Basis,StartFreq,StepFreq,NumFreq,E1,E2,...,EN*CHECKSUM
```

**Field Count**: 7 + N fields (where N = number of frequencies)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Format | Range | Description |
|----------|-------|-------------|-------------|------|--------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | "$PNORE" | - | Always `$PNORE` |
| 1 | Date | str | CHAR(6) | - | MMDDYY | - | Measurement date |
| 2 | Time | str | CHAR(6) | - | hhmmss | - | Measurement time |
| 3 | Spectrum Basis | int | TINYINT | - | N | 0,1,3 | 0=Pressure, 1=Velocity, 3=AST |
| 4 | Start Frequency | float | DECIMAL(4,2) | Hz | d.dd | 0-9.99 | Starting frequency |
| 5 | Step Frequency | float | DECIMAL(4,2) | Hz | d.dd | 0-9.99 | Frequency step size |
| 6 | Number of Frequencies | int | SMALLINT | - | nnn | 1-999 | Count of frequency bins (N) |
| 7 to N+6 | Energy Density | float | DECIMAL(8,3) | cm²/Hz | dddd.ddd | - | Energy at each frequency |
| N+7 | Checksum | str | CHAR(2) | - | *hh | - | NMEA checksum |

> [!NOTE]
> Values of -9, -9.00, -999, etc. indicate **invalid data** per manufacturer specification.

## Example Sentence

```nmea
$PNORE,120720,093150,1,0.02,0.01,98,0.000,0.000,0.000,0.000,0.003,0.012,...*71
```

**Parsed**:

- Date: July 20, 2012 (MMDDYY = 120720)
- Time: 09:31:50
- Spectrum Basis: 1 (Velocity)
- Start Frequency: 0.02 Hz
- Step Frequency: 0.01 Hz
- Number of Frequencies: 98
- Energy Densities: 0.000, 0.000, 0.000, 0.000, 0.003, 0.012, ... cm²/Hz

## Usage

Wave energy density spectrum data is used for:

- Spectral wave analysis
- Wave height calculations (integration of spectrum)
- Identifying dominant wave frequencies
- Oceanographic research and wave modeling

## Related Documents

- [PNORW - Wave Parameters](../pnorw/pnorw.md)
- [PNORF - Fourier Coefficients](../pnorf/pnorf.md)
- [PNORWD - Directional Spectra](../pnorwd/pnorwd.md)
- [All Specifications](../README.md)

---

[📋 All Specs](../README.md) | [🏠 Home](../../README.md)
