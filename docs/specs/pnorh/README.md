[🏠 Home](../../README.md) > [📋 Specs](../README.md) > PNORH Family

# PNORH Message Family

The PNORH family contains header metadata for current velocity measurement series.

## Message Variants

- **PNORH3** - Header data variant 3
- **PNORH4** - Header data variant 4

## Purpose

PNORH messages provide metadata that applies to a series of subsequent PNORC measurements:

- Timestamp for the measurement series
- Configuration parameters
- Quality indicators
- Processing flags

## Relationship to PNORC

**Pattern**:
```
1. PNORH3/4 → Header for measurement series
2. PNORC1-4 → Velocity data for cell 1
3. PNORC1-4 → Velocity data for cell 2
...
N. PNORC1-4 → Velocity data for cell N
```

## Related Documents

- [PNORC Family](../pnorc/README.md) - Current velocity data
- [PNORI Family](../pnori/README.md) - Configuration required for interpretation

---

[⬆️ Back to Specifications](../README.md) | [🏠 Home](../../README.md)
