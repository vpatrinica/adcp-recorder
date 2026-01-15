[🏠 Home](../../README.md) > [📋 Specs](../README.md)

# PNORWD Specification

**Wave directional spectra message** (DF=501) containing either main direction (MD) or directional spread (DS) data per frequency.

## Format

```nmea
$PNORWD,DirType,Date,Time,Basis,StartFreq,StepFreq,NumFreq,V1,V2,...,VN*CHECKSUM
```

**Field Count**: 8 + N fields (where N = number of frequencies)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Format | Range | Description |
|----------|-------|-------------|-------------|------|--------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | "$PNORWD" | - | Always `$PNORWD` |
| 1 | Direction Type | str | CHAR(2) | - | "CC" | MD/DS | MD=Main direction, DS=Directional spread |
| 2 | Date | str | CHAR(6) | - | MMDDYY | - | Measurement date |
| 3 | Time | str | CHAR(6) | - | hhmmss | - | Measurement time |
| 4 | Spectrum Basis | int | TINYINT | - | N | 0,1,3 | 0=Pressure, 1=Velocity, 3=AST |
| 5 | Start Frequency | float | DECIMAL(4,2) | Hz | d.dd | 0-9.99 | Starting frequency |
| 6 | Step Frequency | float | DECIMAL(4,2) | Hz | d.dd | 0-9.99 | Frequency step size |
| 7 | Number of Frequencies | int | SMALLINT | - | nnn | 1-999 | Count of frequency bins (N) |
| 8 to N+7 | Direction/Spread | float | DECIMAL(8,3) | deg | dddd.ddd | - | Value at each frequency |
| N+8 | Checksum | str | CHAR(2) | - | *hh | - | NMEA checksum |

> [!NOTE]
> Values of -9.0000 indicate **invalid data** per manufacturer specification.

## Direction Types

| Type | Description | Unit |
|------|-------------|------|
| MD | Main direction at each frequency | degrees (0-360) |
| DS | Directional spread at each frequency | degrees |

## Example Sentences

**Main Direction (MD):**

```nmea
$PNORWD,MD,120720,093150,1,0.02,0.01,98,326.5016,335.7948,11.6072,8.1730,...*05
```

**Directional Spread (DS):**

```nmea
$PNORWD,DS,120720,093150,1,0.02,0.01,98,79.3190,76.6542,75.1406,76.6127,...*16
```

**Parsed (MD example)**:

- Direction Type: MD (Main direction)
- Date: July 20, 2012 (MMDDYY = 120720)
- Time: 09:31:50
- Spectrum Basis: 1 (Velocity)
- Start Frequency: 0.02 Hz
- Step Frequency: 0.01 Hz
- Number of Frequencies: 98
- Directions: 326.5016°, 335.7948°, 11.6072°, 8.1730°, ... (per frequency)

## Usage

Wave directional spectra data is used for:

- Frequency-dependent wave direction analysis
- Calculating directional spread characteristics
- Full 2D wave spectrum reconstruction
- Advanced wave climate modeling

## Related Documents

- [PNORW - Wave Parameters](../pnorw/pnorw.md)
- [PNORE - Energy Density Spectrum](../pnore/pnore.md)
- [PNORF - Fourier Coefficients](../pnorf/pnorf.md)
- [All Specifications](../README.md)

---

[📋 All Specs](../README.md) | [🏠 Home](../../README.md)
