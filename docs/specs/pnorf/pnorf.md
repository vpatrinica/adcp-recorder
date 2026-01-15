[🏠 Home](../../README.md) > [📋 Specs](../README.md)

# PNORF Specification

**Fourier coefficient spectra message** (DF=501) containing directional wave spectral coefficients (A1, B1, A2, B2).

## Format

```nmea
$PNORF,Flag,Date,Time,Basis,StartFreq,StepFreq,NumFreq,C1,C2,...,CN*CHECKSUM
```

**Field Count**: 8 + N fields (where N = number of frequencies)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Format | Range | Description |
|----------|-------|-------------|-------------|------|--------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | "$PNORF" | - | Always `$PNORF` |
| 1 | Coefficient Flag | str | CHAR(2) | - | "CC" | A1/B1/A2/B2 | Fourier coefficient type |
| 2 | Date | str | CHAR(6) | - | MMDDYY | - | Measurement date |
| 3 | Time | str | CHAR(6) | - | hhmmss | - | Measurement time |
| 4 | Spectrum Basis | int | TINYINT | - | N | 0,1,3 | 0=Pressure, 1=Velocity, 3=AST |
| 5 | Start Frequency | float | DECIMAL(4,2) | Hz | d.dd | 0-9.99 | Starting frequency |
| 6 | Step Frequency | float | DECIMAL(4,2) | Hz | d.dd | 0-9.99 | Frequency step size |
| 7 | Number of Frequencies | int | SMALLINT | - | nnn | 1-999 | Count of frequency bins (N) |
| 8 to N+7 | Fourier Coefficient | float | DECIMAL(8,3) | - | dddd.ddd | - | Coefficient at each frequency |
| N+8 | Checksum | str | CHAR(2) | - | *hh | - | NMEA checksum |

> [!NOTE]
> Values of -9.0000 indicate **invalid data** per manufacturer specification.

## Coefficient Types

| Flag | Description |
|------|-------------|
| A1 | First angular moment (cosine) |
| B1 | First angular moment (sine) |
| A2 | Second angular moment (cosine) |
| B2 | Second angular moment (sine) |

## Example Sentence

```nmea
$PNORF,A1,120720,093150,1,0.02,0.01,98,0.0348,0.0958,0.1372,0.1049,-0.0215,...*0D
```

**Parsed**:

- Coefficient Flag: A1 (first cosine moment)
- Date: July 20, 2012 (MMDDYY = 120720)
- Time: 09:31:50
- Spectrum Basis: 1 (Velocity)
- Start Frequency: 0.02 Hz
- Step Frequency: 0.01 Hz
- Number of Frequencies: 98
- Coefficients: 0.0348, 0.0958, 0.1372, 0.1049, -0.0215, ...

## Usage

Fourier coefficient spectra data is used for:

- Directional wave analysis
- Computing wave direction from spectral moments
- Calculating directional spread
- Advanced oceanographic wave modeling

## Related Documents

- [PNORW - Wave Parameters](../pnorw/pnorw.md)
- [PNORE - Energy Density Spectrum](../pnore/pnore.md)
- [PNORWD - Directional Spectra](../pnorwd/pnorwd.md)
- [All Specifications](../README.md)

---

[📋 All Specs](../README.md) | [🏠 Home](../../README.md)
