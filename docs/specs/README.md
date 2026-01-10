[🏠 Home](../README.md) > Specifications

# NMEA Message Specifications

Complete specifications for all supported Nortek NMEA message types.

## Message Families

### Configuration Messages

**[PNORI Family](pnori/README.md)** - Instrument Configuration
- [PNORI](pnori/pnori.md) - Base configuration format
- [PNORI1](pnori/pnori1.md) - Untagged configuration format
- [PNORI2](pnori/pnori2.md) - Tagged configuration format

Contains instrument type, serial number, beam configuration, cell settings, and coordinate system.

---

### Sensor Data Messages

**[PNORS Family](pnors/README.md)** - Sensor Data
- [PNORS](pnors/pnors.md) - Base sensor data format
- [PNORS1](pnors/pnors1.md) - Sensor data variant 1
- [PNORS2](pnors/pnors2.md) - Sensor data variant 2
- [PNORS3](pnors/pnors3.md) - Sensor data variant 3
- [PNORS4](pnors/pnors4.md) - Sensor data variant 4

Contains timestamp, error/status codes, battery, sound speed, heading, pitch, roll, pressure, temperature, and analog inputs.

---

### Current Velocity Messages

**[PNORC Family](pnorc/README.md)** - Current Velocity Data
- [PNORC](pnorc/pnorc.md) - Base current velocity format
- [PNORC1](pnorc/pnorc1.md) - Current velocity variant 1
- [PNORC2](pnorc/pnorc2.md) - Current velocity variant 2
- [PNORC3](pnorc/pnorc3.md) - Current velocity variant 3
- [PNORC4](pnorc/pnorc4.md) - Current velocity variant 4

Contains timestamp, cell index, velocity components (East, North, Up or X, Y, Z), and quality metrics.

**[PNORH Family](pnorh/README.md)** - Header Data
- [PNORH3](pnorh/pnorh3.md) - Header data variant 3
- [PNORH4](pnorh/pnorh4.md) - Header data variant 4

Contains metadata headers for current velocity measurement series.

---

### Additional Data Messages

**[PNORA](pnora/pnora.md)** - Altitude/Range Data  
Distance measurements from instrument to surface or bottom.

**[PNORW](pnorw/pnorw.md)** - Wave Data  
Wave height, period, and direction measurements.

**[PNORB](pnorb/pnorb.md)** - Bottom Tracking Data  
Velocity relative to seabed using bottom-tracking mode.

**[PNORE](pnore/pnore.md)** - Echo Intensity Data  
Acoustic backscatter intensity measurements.

**[PNORF](pnorf/pnorf.md)** - Frequency Data  
Acoustic frequency measurements and diagnostics.

**[PNORWD](pnorwd/pnorwd.md)** - Wave Directional Data  
Directional wave spectrum and propagation data.

---

## Message Type Reference Table

| Prefix | Family | Type | Description |
|--------|--------|------|-------------|
| PNORI | Configuration | Base | Instrument configuration |
| PNORI1 | Configuration | Untagged | Instrument configuration (untagged) |
| PNORI2 | Configuration | Tagged | Instrument configuration (tagged) |
| PNORS | Sensor | Base | Sensor data |
| PNORS1 | Sensor | Variant 1 | Sensor data variant 1 |
| PNORS2 | Sensor | Variant 2 | Sensor data variant 2 |
| PNORS3 | Sensor | Variant 3 | Sensor data variant 3 |
| PNORS4 | Sensor | Variant 4 | Sensor data variant 4 |
| PNORC | Current | Base | Current velocity |
| PNORC1 | Current | Variant 1 | Current velocity variant 1 |
| PNORC2 | Current | Variant 2 | Current velocity variant 2 |
| PNORC3 | Current | Variant 3 | Current velocity variant 3 |
| PNORC4 | Current | Variant 4 | Current velocity variant 4 |
| PNORH3 | Current | Header 3 | Header data variant 3 |
| PNORH4 | Current | Header 4 | Header data variant 4 |
| PNORA | Altitude | Single | Altitude/range data |
| PNORW | Wave | Single | Wave data |
| PNORB | Bottom | Single | Bottom tracking data |
| PNORE | Echo | Single | Echo intensity data |
| PNORF | Frequency | Single | Frequency data |
| PNORWD | Wave Dir | Single | Wave directional data |

## Common Patterns

### Tagged vs. Positional Fields

**Positional Format** (PNORI1, PNORS, PNORC, etc.):
```
$PREFIX,value1,value2,value3,...*CHECKSUM
```

**Tagged Format** (PNORI2, PNORS2, PNORC2, etc.):
```
$PREFIX,TAG1=value1,TAG2=value2,...*CHECKSUM
```

### Field Order

Each specification document includes:
1. **Format Description** - Sentence structure and field count
2. **Field Definitions** - Each field with name, type, unit, and range
3. **Python Data Structure** - Dataclass implementation
4. **DuckDB Schema** - Table definition with constraints
5. **Validation Rules** - Field and cross-field validation
6. **Example Sentences** - Valid sentence examples
7. **Related Documents** - Links to family and implementation guides

## Navigation

- [🏠 Home](../README.md)
- [NMEA Protocol](../nmea/overview.md)
- [Python Parsers](../implementation/python/parsers.md)
- [DuckDB Schemas](../implementation/duckdb/schemas.md)
- [Examples](../examples/README.md)

---

[🏠 Back to Documentation](../README.md)
