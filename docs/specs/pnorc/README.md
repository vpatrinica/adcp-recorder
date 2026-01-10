[🏠 Home](../../README.md) > [📋 Specs](../README.md) > PNORC Family

# PNORC Message Family

The PNORC family contains current velocity measurement data from ADCP profiling.

## Message Variants

- **[PNORC](pnorc.md)** - Base current velocity format
- **PNORC1** - Current velocity variant 1
- **PNORC2** - Current velocity variant 2 (tagged format)
- **PNORC3** - Current velocity variant 3 (extended precision)
- **PNORC4** - Current velocity variant 4 (compact format)

## Common Fields

| Field | Type | Unit | Description |
|-------|------|------|-------------|
| Date | String (MMDDYY) | - | Measurement date |
| Time | String (HHMMSS) | - | Measurement time |
| Cell Index | Integer | - | Measurement cell number (1-based) |
| Velocity East (or X) | Float | m/s | Eastward velocity component |
| Velocity North (or Y) | Float | m/s | Northward velocity component |
| Velocity Up (or Z) | Float | m/s | Upward velocity component |

## Coordinate Systems

Velocity components depend on the configured coordinate system (from PNORI):

- **ENU**: East, North, Up (geographic coordinates)
- **XYZ**: X, Y, Z (instrument-fixed coordinates)
- **BEAM**: Individual beam velocities

## Example Sentence

```
$PNORC,102115,090715,1,12.34,56.78,90.12*XX
```

## Related Documents

- [PNORC Base Specification](pnorc.md)
- [PNORI Configuration](../pnori/README.md) - Required for coordinate system context

---

[⬆️ Back to Specifications](../README.md) | [🏠 Home](../../README.md)
