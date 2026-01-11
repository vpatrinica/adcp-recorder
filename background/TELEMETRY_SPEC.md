# Master Index: AD2CP NMEA Telemetry Data Formats

## Overview
This documentation specifies all NMEA telemetry data formats for Nortek AD2CP instruments. Each message type is documented in a separate file below.
Parser and persistence has to use logical interpretation of the fields definitions below, the nortek definitions are just for reference. In case there is no discrepancy between the nortek definition and our implementation, we will follow the fields specification.
---

## Averaging Mode (SET/GETTMAVG)

### Data Format 100 (Legacy Aquadopp/AWAC)
1. **[PNORI-DF100.md](PNORI-DF100.md)** - Configuration information
2. **[PNORS-DF100.md](PNORS-DF100.md)** - Sensor data
3. **[PNORC-DF100.md](PNORC-DF100.md)** - Current velocity data

### Data Format 101 (No Tags)
4. **[PNORI1-DF101.md](PNORI1-DF101.md)** - Information data without tags
5. **[PNORS1-DF101.md](PNORS1-DF101.md)** - Sensor data without tags
6. **[PNORC1-DF101.md](PNORC1-DF101.md)** - Averaged data without tags

### Data Format 102 (With Tags)
7. **[PNORI2-DF102.md](PNORI2-DF102.md)** - Information data with tags
8. **[PNORS2-DF102.md](PNORS2-DF102.md)** - Sensor data with tags
9. **[PNORC2-DF102.md](PNORC2-DF102.md)** - Averaged data with tags

### Data Format 103 (With Tags)
10. **[PNORH3-DF103.md](PNORH3-DF103.md)** - Header data with tags
11. **[PNORS3-DF103.md](PNORS3-DF103.md)** - Sensor data with tags
12. **[PNORC3-DF103.md](PNORC3-DF103.md)** - Averaged data with tags

### Data Format 104 (No Tags)
13. **[PNORH4-DF104.md](PNORH4-DF104.md)** - Header data without tags
14. **[PNORS4-DF104.md](PNORS4-DF104.md)** - Sensor data without tags
15. **[PNORC4-DF104.md](PNORC4-DF104.md)** - Averaged data without tags

---

## Burst Mode (SET/GETTMBURST)

### Data Format 101 (No Tags)
16. **[PNORI1-BURST-DF101.md](PNORI1-BURST-DF101.md)** - Information data without tags
17. **[PNORS1-BURST-DF101.md](PNORS1-BURST-DF101.md)** - Sensor data without tags
18. **[PNORC1-BURST-DF101.md](PNORC1-BURST-DF101.md)** - Averaged data without tags

### Data Format 102 (With Tags)
19. **[PNORI2-BURST-DF102.md](PNORI2-BURST-DF102.md)** - Information data with tags
20. **[PNORS2-BURST-DF102.md](PNORS2-BURST-DF102.md)** - Sensor data with tags
21. **[PNORC2-BURST-DF102.md](PNORC2-BURST-DF102.md)** - Averaged data with tags

### Data Format 103 (With Tags)
22. **[PNORH3-BURST-DF103.md](PNORH3-BURST-DF103.md)** - Header data with tags
23. **[PNORS3-BURST-DF103.md](PNORS3-BURST-DF103.md)** - Sensor data with tags
24. **[PNORC3-BURST-DF103.md](PNORC3-BURST-DF103.md)** - Averaged data with tags

### Data Format 104 (No Tags)
25. **[PNORH4-BURST-DF104.md](PNORH4-BURST-DF104.md)** - Header data without tags
26. **[PNORS4-BURST-DF104.md](PNORS4-BURST-DF104.md)** - Sensor data without tags
27. **[PNORC4-BURST-DF104.md](PNORC4-BURST-DF104.md)** - Averaged data without tags

---

## Altimeter Mode (SET/GETTMALTI)

28. **[PNORA-DF200.md](PNORA-DF200.md)** - Altimeter data without tags
29. **[PNORA-DF201.md](PNORA-DF201.md)** - Altimeter data with tags

---

## Waves Mode (SET/GETTMWAVE)

30. **[PNORW-DF501.md](PNORW-DF501.md)** - Wave parameters
31. **[PNORB-DF501.md](PNORB-DF501.md)** - Wave band parameters
32. **[PNORE-DF501.md](PNORE-DF501.md)** - Wave energy density spectrum
33. **[PNORF-DF501.md](PNORF-DF501.md)** - Fourier coefficient spectra
34. **[PNORWD-DF501.md](PNORWD-DF501.md)** - Wave directional spectra

---

## Binary Formats (Not NMEA)
- DF=3 (Averaging/Burst) - Binary format as described in Data Record Definition
- DF=500 (Waves) - Binary format
- DF=502 (Waves) - AWAC-compatible binary format

---

## Common Notes

### Checksum Calculation
- Calculated per NMEA standard
- XOR of all characters between `$` and `*` (excluding these delimiters)
- Represented as two hexadecimal characters

### Invalid Data Indicators
- Waves data uses `-9.00`, `-999`, etc. to indicate invalid data
- Empty fields indicate unused parameters

### Coordinate Systems
- **ENU**: East-North-Up (CY=0)
- **XYZ**: Instrument coordinates (CY=1)
- **BEAM**: Beam coordinates (CY=2)

### Instrument Types
- 0: Aquadopp
- 2: Aquadopp Profiler
- 4: Signature

### Spectrum Basis Types (Waves)
- 0: Pressure-based
- 1: Velocity-based
- 3: AST (Acoustic Surface Tracking)

### Processing Methods (Waves)
- 1: PUV
- 2: SUV
- 3: MLM
- 4: MLMST

---

## Quick Reference Table

| Mode | DF | Format | Key Sentences |
|------|----|--------|---------------|
| Averaging | 100 | Legacy | PNORI, PNORS, PNORC |
| Averaging | 101 | No Tags | PNORI1, PNORS1, PNORC1 |
| Averaging | 102 | With Tags | PNORI2, PNORS2, PNORC2 |
| Averaging | 103 | With Tags | PNORH3, PNORS3, PNORC3 |
| Averaging | 104 | No Tags | PNORH4, PNORS4, PNORC4 |
| Burst | 101 | No Tags | PNORI1, PNORS1, PNORC1 |
| Burst | 102 | With Tags | PNORI2, PNORS2, PNORC2 |
| Burst | 103 | With Tags | PNORH3, PNORS3, PNORC3 |
| Burst | 104 | No Tags | PNORH4, PNORS4, PNORC4 |
| Altimeter | 200 | No Tags | PNORA |
| Altimeter | 201 | With Tags | PNORA |
| Waves | 501 | NMEA | PNORW, PNORB, PNORE, PNORF, PNORWD |

---

**© 2025 Nortek AS** - All rights reserved. This documentation is proprietary to Nortek AS and is provided for integration purposes only.

---

**PNORI-DF100.md**
```markdown
# PNORI - Configuration Information (DF=100)

## Description
NMEA-formatted configuration information from the Averaging telemetry mode (Data Format 100). Provides instrument setup and measurement parameters.

## Format
`$PNORI,<instrument_type>,<head_id>,<num_beams>,<num_cells>,<blanking>,<cell_size>,<coord_system>*<checksum>`

## Data Fields
- Column=0, Field=Identifier, Data Type=String, Format="$PNORI", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Instrument Type, Data Type=Integer, Format=N, Unit=-, Description=Instrument model, Notes/Enums=0=Aquadopp, 2=Aquadopp Profiler, 4=Signature
- Column=2, Field=Head ID, Data Type=String, Format=Text, Unit=-, Description=Instrument serial number, Notes=Unique identifier
- Column=3, Field=Number of Beams, Data Type=Integer, Format=N, Unit=-, Description=Acoustic beams, Notes=Typically 3 or 4
- Column=4, Field=Number of Cells, Data Type=Integer, Format=N, Unit=-, Description=Measurement cells, Notes=1-128 typically
- Column=5, Field=Blanking Distance, Data Type=Float, Format=dd.dd, Unit=m, Description=Distance to first cell, Notes=0.00-99.99 m
- Column=6, Field=Cell Size, Data Type=Float, Format=dd.dd, Unit=m, Description=Size of each cell, Notes=0.00-99.99 m
- Column=7, Field=Coordinate System, Data Type=Integer, Format=N, Unit=-, Description=Velocity coordinate system, Notes/Enums=0=ENU, 1=XYZ, 2=BEAM
- Column=8, Field=Checksum, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Enumerations
### Instrument Type
- 0: Aquadopp
- 2: Aquadopp Profiler
- 4: Signature

### Coordinate System
- 0: ENU - East-North-Up (geographic)
- 1: XYZ - Instrument coordinates
- 2: BEAM - Beam coordinates (radial)

## Example
```
$PNORI,4,Signature1000900001,4,20,0.20,1.00,0*2E
```

## Interpretation
- Instrument: Signature (4)
- Serial: Signature1000900001
- Beams: 4-beam system
- Cells: 20 measurement cells
- Blanking: 0.20 m to first cell
- Cell size: 1.00 m each
- Coordinates: ENU (0)
- Checksum: 2E

## Notes
- Used in Averaging mode with DF=100
- Provides static configuration (doesn't change frequently)
- Must match actual instrument setup
- Part of the legacy Aquadopp/AWAC compatibility format
```

**PNORS-DF100.md**
```markdown
# PNORS - Sensor Data (DF=100)

## Description
NMEA-formatted sensor data from the Averaging telemetry mode (Data Format 100). Contains time, orientation, environmental measurements, and system status.

## Format
`$PNORS,<date>,<time>,<error_code>,<status_code>,<battery>,<sound_speed>,<heading>,<pitch>,<roll>,<pressure>,<temperature>,<analog1>,<analog2>*<checksum>`

## Data Fields
- Column=0, Field=Identifier, Data Type=String, Format="$PNORS", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Date, Data Type=Integer, Format=MMDDYY, Unit=-, Description=Measurement date, Notes=MonthDayYear
- Column=2, Field=Time, Data Type=Integer, Format=HHMMSS, Unit=-, Description=Measurement time, Notes=HourMinuteSecond
- Column=3, Field=Error Code, Data Type=Hex, Format=hh, Unit=-, Description=System error code, Notes=8 hex digits
- Column=4, Field=Status Code, Data Type=Hex, Format=hh, Unit=-, Description=System status code, Notes=8 hex digits
- Column=5, Field=Battery Voltage, Data Type=Float, Format=dd.d, Unit=V, Description=Power supply voltage, Notes=Typically 10.0-16.0V
- Column=6, Field=Sound Speed, Data Type=Float, Format=dddd.d, Unit=m/s, Description=Measured sound speed, Notes=1400.0-1600.0 m/s
- Column=7, Field=Heading, Data Type=Float, Format=ddd.d, Unit=deg, Description=Compass heading, Notes=0.0-359.9°, magnetic
- Column=8, Field=Pitch, Data Type=Float, Format=dd.d, Unit=deg, Description=Instrument pitch, Notes=-90.0 to +90.0°
- Column=9, Field=Roll, Data Type=Float, Format=dd.d, Unit=deg, Description=Instrument roll, Notes=-90.0 to +90.0°
- Column=10, Field=Pressure, Data Type=Float, Format=ddd.ddd, Unit=dBar, Description=Water pressure, Notes=Depth equivalent
- Column=11, Field=Temperature, Data Type=Float, Format=dd.dd, Unit=°C, Description=Water temperature, Notes=-5.00 to +35.00°C
- Column=12, Field=Analog Input 1, Data Type=Integer, Format=n/a, Unit=-, Description=Unused/placeholder, Notes=Always 0
- Column=13, Field=Analog Input 2, Data Type=Integer, Format=n/a, Unit=-, Description=Unused/placeholder, Notes=Always 0
- Column=14, Field=Checksum, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Example
```
$PNORS,102115,090715,00000000,2A480000,14.4,1523.0,275.9,15.7,-2.3,0.000,22.45,0,0*1C
```

## Interpretation
- Date: October 21, 2015
- Time: 09:07:15 UTC
- Error: 0x00000000 (no errors)
- Status: 0x2A480000 (system normal)
- Battery: 14.4 volts
- Sound speed: 1523.0 m/s
- Heading: 275.9° (west-northwest)
- Pitch: 15.7° (tilted forward)
- Roll: -2.3° (slight left tilt)
- Pressure: 0.000 dBar (surface)
- Temperature: 22.45°C
- Checksum: 1C

## Error Code Interpretation
- 0x00000000: No errors
- Other values: See instrument error codes documentation

## Status Code Interpretation
- Bitfield indicating various system states
- See instrument status codes documentation for bit definitions

## Notes
- Used in Averaging mode with DF=100
- Time is instrument internal clock (not GPS-synchronized)
- Pressure is absolute (includes atmospheric pressure)
- Pitch/Roll are relative to horizontal plane
- Analog inputs are placeholders (always 0 in this format)
- Sound speed is calculated from temperature, salinity, pressure
```

**PNORC-DF100.md**
```markdown
# PNORC - Averaged Current Velocity Data (DF=100)

## Description
NMEA-formatted current velocity data from the Averaging telemetry mode (Data Format 100).

## Format
`$PNORC,<date>,<time>,<cell>,<vel1>,<vel2>,<vel3>,<vel4>,<speed>,<direction>,<amp_unit>,<amp1>,<amp2>,<amp3>,<amp4>,<corr1>,<corr2>,<corr3>,<corr4>*<checksum>`

## Data Fields
- Column=0, Field=Identifier, Data Type=String, Format="$PNORC", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Date, Data Type=Integer, Format=MMDDYY, Unit=-, Description=Measurement date, Notes=MonthDayYear
- Column=2, Field=Time, Data Type=Integer, Format=HHMMSS, Unit=-, Description=Measurement time, Notes=HourMinuteSecond
- Column=3, Field=Cell Number, Data Type=Integer, Format=N, Unit=-, Description=Measurement cell, Notes=1-indexed
- Column=4, Field=Velocity 1, Data Type=Float, Format=dd.dd, Unit=m/s, Description=Beam1/X/East velocity, Notes=± range
- Column=5, Field=Velocity 2, Data Type=Float, Format=dd.dd, Unit=m/s, Description=Beam2/Y/North velocity, Notes=± range
- Column=6, Field=Velocity 3, Data Type=Float, Format=dd.dd, Unit=m/s, Description=Beam3/Z1/Up1 velocity, Notes=± range
- Column=7, Field=Velocity 4, Data Type=Float, Format=dd.dd, Unit=m/s, Description=Beam4/Z2/Up2 velocity, Notes=Empty for 3-beam
- Column=8, Field=Speed, Data Type=Float, Format=dd.dd, Unit=m/s, Description=Current speed magnitude, Notes=0.00-99.99 m/s
- Column=9, Field=Direction, Data Type=Float, Format=ddd.d, Unit=deg, Description=Current direction, Notes=0.0-359.9°
- Column=10, Field=Amplitude Unit, Data Type=String, Format=C, Unit=-, Description="C" = Counts, Notes=Always "C"
- Column=11, Field=Amplitude Beam 1, Data Type=Integer, Format=N, Unit=counts, Description=Echo amplitude, Notes=0-255 typically
- Column=12, Field=Amplitude Beam 2, Data Type=Integer, Format=N, Unit=counts, Description=Echo amplitude, Notes=0-255 typically
- Column=13, Field=Amplitude Beam 3, Data Type=Integer, Format=N, Unit=counts, Description=Echo amplitude, Notes=0-255 typically
- Column=14, Field=Amplitude Beam 4, Data Type=Integer, Format=N, Unit=counts, Description=Echo amplitude, Notes=Empty for 3-beam
- Column=15, Field=Correlation Beam 1, Data Type=Integer, Format=N, Unit=%, Description=Correlation percentage, Notes=0-100%
- Column=16, Field=Correlation Beam 2, Data Type=Integer, Format=N, Unit=%, Description=Correlation percentage, Notes=0-100%
- Column=17, Field=Correlation Beam 3, Data Type=Integer, Format=N, Unit=%, Description=Correlation percentage, Notes=0-100%
- Column=18, Field=Correlation Beam 4, Data Type=Integer, Format=N, Unit=%, Description=Correlation percentage, Notes=Empty for 3-beam
- Column=19, Field=Checksum, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Velocity Mapping
- ENU Coordinates: Velocity 1=East (E), Velocity 2=North (N), Velocity 3=Up 1 (U), Velocity 4=Up 2 (U2)
- XYZ Coordinates: Velocity 1=X, Velocity 2=Y, Velocity 3=Z1, Velocity 4=Z2
- BEAM Coordinates: Velocity 1=Beam 1, Velocity 2=Beam 2, Velocity 3=Beam 3, Velocity 4=Beam 4

## Example
```
$PNORC,102115,090715,4,0.56,-0.80,-1.99,-1.33,0.98,305.2,C,80,88,67,78,13,17,10,18*22
```

## Interpretation
- Date: October 21, 2015
- Time: 09:07:15 UTC
- Cell: Cell #4
- Velocities: 0.56, -0.80, -1.99, -1.33 m/s
- Speed: 0.98 m/s
- Direction: 305.2° (NW)
- Amplitude unit: Counts
- Amplitudes: 80, 88, 67, 78 counts
- Correlations: 13%, 17%, 10%, 18%
- Checksum: 22

## Notes
- Used in Averaging mode with DF=100
- One sentence per measurement cell
- Fields 7, 14, 18 are empty for 3-beam systems
- Direction follows oceanographic convention (coming from)
- Speed and direction calculated from vector components
- Amplitude in counts (not dB)
- Correlation indicates data quality (higher = better)
- Negative velocities indicate flow toward instrument
- Empty fields for Velocity 4, Amplitude 4, Correlation 4 in 3-beam systems
```

**PNORI1-DF101.md**
```markdown
# PNORI1 - Information Data Format 1 (DF=101)

## Description
NMEA-formatted configuration information without tags from Averaging or Burst telemetry modes (Data Format 101).

## Format
`$PNORI1,<instrument_type>,<head_id>,<num_beams>,<num_cells>,<blanking>,<cell_size>,<coord_system>*<checksum>`

## Data Fields
- Column=0, Field=Identifier, Tag=-, Data Type=String, Format="$PNORI1", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Instrument Type, Tag=IT, Data Type=Integer, Format=N, Unit=-, Description=Instrument model, Notes/Enums=0=Aquadopp, 2=Aquadopp Profiler, 4=Signature
- Column=2, Field=Head ID, Tag=SN, Data Type=Integer, Format=N, Unit=-, Description=Instrument serial number, Notes=Numeric only
- Column=3, Field=Number of Beams, Tag=NB, Data Type=Integer, Format=N, Unit=-, Description=Acoustic beams, Notes=3 or 4
- Column=4, Field=Number of Cells, Tag=NC, Data Type=Integer, Format=N, Unit=-, Description=Measurement cells, Notes=1-128
- Column=5, Field=Blanking Distance, Tag=BD, Data Type=Float, Format=dd.dd, Unit=m, Description=Distance to first cell, Notes=0.00-99.99 m
- Column=6, Field=Cell Size, Tag=CS, Data Type=Float, Format=dd.dd, Unit=m, Description=Size of each cell, Notes=0.00-99.99 m
- Column=7, Field=Coordinate System, Tag=CY, Data Type=String, Format=Text, Unit=-, Description=Velocity coordinates, Notes/Enums=ENU, XYZ, or BEAM
- Column=8, Field=Checksum, Tag=-, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Enumerations
### Instrument Type (IT)
- 0: Aquadopp
- 2: Aquadopp Profiler
- 4: Signature

### Coordinate System (CY)
- ENU: East-North-Up (geographic)
- XYZ: Instrument coordinates
- BEAM: Beam coordinates (radial)

## Example
```
$PNORI1,4,123456,4,30,1.00,5.00,BEAM*5B
```

## Interpretation
- Instrument: Signature (4)
- Serial: 123456
- Beams: 4-beam system
- Cells: 30 measurement cells
- Blanking: 1.00 m to first cell
- Cell size: 5.00 m each
- Coordinates: BEAM (beam coordinates)
- Checksum: 5B

## Notes
- Used in Averaging mode (DF=101) and Burst mode (DF=101)
- No tags in data fields (tagless format)
- Head ID is numeric only (string in DF=100)
- Coordinate system as text (not numeric code)
- Consistent format with other DF=101 sentences
```

**PNORS1-DF101.md**
```markdown
# PNORS1 - Sensor Data Format 1 (DF=101)

## Description
NMEA-formatted sensor data without tags from Averaging or Burst telemetry modes (Data Format 101).

## Format
`$PNORS1,<date>,<time>,<error_code>,<status_code>,<battery>,<sound_speed>,<heading_stddev>,<heading>,<pitch>,<pitch_stddev>,<roll>,<roll_stddev>,<pressure>,<pressure_stddev>,<temperature>*<checksum>`

## Data Fields
- Column=0, Field=Identifier, Tag=-, Data Type=String, Format="$PNORS1", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Date, Tag=DATE, Data Type=Integer, Format=MMDDYY, Unit=-, Description=Measurement date, Notes=MonthDayYear
- Column=2, Field=Time, Tag=TIME, Data Type=Integer, Format=HHMMSS, Unit=-, Description=Measurement time, Notes=HourMinuteSecond
- Column=3, Field=Error Code, Tag=EC, Data Type=Integer, Format=N, Unit=-, Description=System error code, Notes=0=no error
- Column=4, Field=Status Code, Tag=SC, Data Type=Hex, Format=hhhhhhhh, Unit=-, Description=System status, Notes=8 hex digits
- Column=5, Field=Battery Voltage, Tag=BV, Data Type=Float, Format=dd.d, Unit=V, Description=Power supply, Notes=10.0-16.0V typical
- Column=6, Field=Sound Speed, Tag=SS, Data Type=Float, Format=dddd.d, Unit=m/s, Description=Measured sound speed, Notes=1400.0-1600.0 m/s
- Column=7, Field=Heading Std. Dev., Tag=HSD, Data Type=Float, Format=dd.dd, Unit=deg, Description=Heading uncertainty, Notes=0.00-99.99°
- Column=8, Field=Heading, Tag=H, Data Type=Float, Format=ddd.d, Unit=deg, Description=Compass heading, Notes=0.0-359.9°
- Column=9, Field=Pitch, Tag=PI, Data Type=Float, Format=dd.d, Unit=deg, Description=Instrument pitch, Notes=-90.0 to +90.0°
- Column=10, Field=Pitch Std. Dev., Tag=PISD, Data Type=Float, Format=dd.dd, Unit=deg, Description=Pitch uncertainty, Notes=0.00-99.99°
- Column=11, Field=Roll, Tag=R, Data Type=Float, Format=dd.d, Unit=deg, Description=Instrument roll, Notes=-90.0 to +90.0°
- Column=12, Field=Roll Std. Dev., Tag=RSD, Data Type=Float, Format=dd.dd, Unit=deg, Description=Roll uncertainty, Notes=0.00-99.99°
- Column=13, Field=Pressure, Tag=P, Data Type=Float, Format=ddd.ddd, Unit=dBar, Description=Water pressure, Notes=Depth equivalent
- Column=14, Field=Pressure Std. Dev., Tag=PSD, Data Type=Float, Format=dd.dd, Unit=dBar, Description=Pressure uncertainty, Notes=0.00-99.99 dBar
- Column=15, Field=Temperature, Tag=T, Data Type=Float, Format=dd.dd, Unit=°C, Description=Water temperature, Notes=-5.00 to +35.00°C
- Column=16, Field=Checksum, Tag=-, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Example
```
$PNORS1,083013,132455,0,34000034,22.9,1500.0,0.02,123.4,45.6,0.02,23.4,0.02,123.456,0.02,24.56*39
```

## Interpretation
- Date: August 30, 2013
- Time: 13:24:55 UTC
- Error: 0 (no errors)
- Status: 0x34000034
- Battery: 22.9 volts
- Sound speed: 1500.0 m/s
- Heading std dev: 0.02°
- Heading: 123.4°
- Pitch: 45.6°
- Pitch std dev: 0.02°
- Roll: 23.4°
- Roll std dev: 0.02°
- Pressure: 123.456 dBar
- Pressure std dev: 0.02 dBar
- Temperature: 24.56°C
- Checksum: 39

## Notes
- Used in Averaging mode (DF=101) and Burst mode (DF=101)
- No tags in data fields (tagless format)
- Includes standard deviation measurements (not in DF=100)
- Error code as integer (not hex)
- Temperature with two decimal places
```

**PNORC1-DF101.md**
```markdown
# PNORC1 - Averaged Current Data Format 1 (DF=101)

## Description
NMEA-formatted averaged current data without tags from Averaging or Burst telemetry modes (Data Format 101).

## Format
`$PNORC1,<date>,<time>,<cell_num>,<cell_pos>,<velocity_fields>,<amplitude_fields>,<correlation_fields>*<checksum>`

## Data Fields Nortek Definition
- Column=0, Field=Identifier, Tag=-, Data Type=String, Format="$PNORC1", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Date, Tag=DATE, Data Type=Integer, Format=MMDDYY, Unit=-, Description=Measurement date, Notes=Always present
- Column=2, Field=Time, Tag=TIME, Data Type=Integer, Format=HHMMSS, Unit=-, Description=Measurement time, Notes=Always present
- Column=3, Field=Cell Number, Tag=CN, Data Type=Integer, Format=N, Unit=-, Description=Measurement cell index, Notes=Always present
- Column=4, Field=Cell Position, Tag=CP, Data Type=Float, Format=dd.d, Unit=m, Description=Distance from transducer, Notes=Always present
- Column=5, Field=Velocity East, Tag=VE, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=East velocity component, Notes=CY=ENU only
- Column=6, Field=Velocity North, Tag=VN, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=North velocity component, Notes=CY=ENU only
- Column=7, Field=Velocity Up, Tag=VU, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Up velocity component, Notes=CY=ENU only
- Column=8, Field=Velocity Up 2, Tag=VU2, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Second up velocity, Notes=CY=ENU only
- Column=9, Field=Velocity X, Tag=VX, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=X velocity component, Notes=CY=XYZ only
- Column=10, Field=Velocity Y, Tag=VY, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Y velocity component, Notes=CY=XYZ only
- Column=11, Field=Velocity Z, Tag=VZ, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Z velocity component, Notes=CY=XYZ only
- Column=12, Field=Velocity Z2, Tag=VZ2, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Second Z velocity, Notes=CY=XYZ only
- Column=13, Field=Velocity Beam 1, Tag=V1, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Beam 1 velocity, Notes=CY=BEAM only
- Column=14, Field=Velocity Beam 2, Tag=V2, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Beam 2 velocity, Notes=CY=BEAM only
- Column=15, Field=Velocity Beam 3, Tag=V3, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Beam 3 velocity, Notes=CY=BEAM only
- Column=16, Field=Velocity Beam 4, Tag=V4, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Beam 4 velocity, Notes=CY=BEAM only
- Column=17, Field=Amplitude Beam 1, Tag=A1, Data Type=Float, Format=ddd.d, Unit=dB, Description=Echo amplitude beam 1, Notes=Always present
- Column=18, Field=Amplitude Beam 2, Tag=A2, Data Type=Float, Format=ddd.d, Unit=dB, Description=Echo amplitude beam 2, Notes=Always present
- Column=19, Field=Amplitude Beam 3, Tag=A3, Data Type=Float, Format=ddd.d, Unit=dB, Description=Echo amplitude beam 3, Notes=Always present
- Column=20, Field=Amplitude Beam 4, Tag=A4, Data Type=Float, Format=ddd.d, Unit=dB, Description=Echo amplitude beam 4, Notes=Always present
- Column=21, Field=Correlation Beam 1, Tag=C1, Data Type=Integer, Format=N, Unit=%, Description=Correlation beam 1, Notes=Always present
- Column=22, Field=Correlation Beam 2, Tag=C2, Data Type=Integer, Format=N, Unit=%, Description=Correlation beam 2, Notes=Always present
- Column=23, Field=Correlation Beam 3, Tag=C3, Data Type=Integer, Format=N, Unit=%, Description=Correlation beam 3, Notes=Always present
- Column=24, Field=Correlation Beam 4, Tag=C4, Data Type=Integer, Format=N, Unit=%, Description=Correlation beam 4, Notes=Always present
- Column=25, Field=Checksum, Tag=-, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Data Fields Logical Interpretation for Parser 
- Column=0, Field=Identifier, Tag=-, Data Type=String, Format="$PNORC1", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Date, Tag=DATE, Data Type=Integer, Format=MMDDYY, Unit=-, Description=Measurement date, Notes=Always present
- Column=2, Field=Time, Tag=TIME, Data Type=Integer, Format=HHMMSS, Unit=-, Description=Measurement time, Notes=Always present
- Column=3, Field=Cell Number, Tag=CN, Data Type=Integer, Format=N, Unit=-, Description=Measurement cell index, Notes=Always present
- Column=4, Field=Cell Position, Tag=CP, Data Type=Float, Format=dd.d, Unit=m, Description=Distance from transducer, Notes=Always present
- Column=5, Field=Velocity 1, Tag=V1/VE/VX, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Velocity component 1, Notes=Meaning depends on CY
- Column=6, Field=Velocity 2, Tag=V2/VN/VY, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Velocity component 2, Notes=Meaning depends on CY
- Column=7, Field=Velocity 3, Tag=V3/VU/VZ, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Velocity component 3, Notes=Meaning depends on CY
- Column=8, Field=Velocity 4, Tag=V4/VU2/VZ2, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Velocity component 4, Notes=Meaning depends on CY
- Column=9, Field=Amplitude Beam 1, Tag=A1, Data Type=Float, Format=ddd.d, Unit=dB, Description=Echo amplitude beam 1, Notes=Always present
- Column=10, Field=Amplitude Beam 2, Tag=A2, Data Type=Float, Format=ddd.d, Unit=dB, Description=Echo amplitude beam 2, Notes=Always present
- Column=11, Field=Amplitude Beam 3, Tag=A3, Data Type=Float, Format=ddd.d, Unit=dB, Description=Echo amplitude beam 3, Notes=Always present
- Column=12, Field=Amplitude Beam 4, Tag=A4, Data Type=Float, Format=ddd.d, Unit=dB, Description=Echo amplitude beam 4, Notes=Always present
- Column=13, Field=Correlation Beam 1, Tag=C1, Data Type=Integer, Format=N, Unit=%, Description=Correlation beam 1, Notes=Always present
- Column=14, Field=Correlation Beam 2, Tag=C2, Data Type=Integer, Format=N, Unit=%, Description=Correlation beam 2, Notes=Always present
- Column=15, Field=Correlation Beam 3, Tag=C3, Data Type=Integer, Format=N, Unit=%, Description=Correlation beam 3, Notes=Always present
- Column=16, Field=Correlation Beam 4, Tag=C4, Data Type=Integer, Format=N, Unit=%, Description=Correlation beam 4, Notes=Always present
- Column=17, Field=Checksum, Tag=-, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Coordinate System Dependencies
- CY=ENU: Velocity fields VE, VN, VU, VU2
- CY=XYZ: Velocity fields VX, VY, VZ, VZ2
- CY=BEAM: Velocity fields V1, V2, V3, V4

## Examples
**ENU Coordinate System:**
```
$PNORC1,083013,132455,3,11.0,0.332,0.332,0.332,0.332,78.9,78.9,78.9,78.9,78,78,78,78*46
```

**BEAM Coordinate System:**
```
$PNORC1,083013,132455,3,11.0,0.332,0.332,0.332,0.332,78.9,78.9,78.9,78.9,78,78,78,78*46
```

## Notes
- Used in Averaging mode (DF=101) and Burst mode (DF=101)
- Velocity fields depend on coordinate system (CY parameter)
- Repeated for each measurement cell
- No tags in data fields (tagless format)
- Amplitudes in dB (not counts like DF=100)
- Three decimal places for velocities
- Cell position in meters from transducer
```

**PNORI2-DF102.md**
```markdown
# PNORI2 - Information Data Format 2 (DF=102)

## Description
NMEA-formatted configuration information with tags from Averaging or Burst telemetry modes (Data Format 102).

## Format
`$PNORI2,IT=<instrument_type>,SN=<head_id>,NB=<num_beams>,NC=<num_cells>,BD=<blanking>,CS=<cell_size>,CY=<coord_system>*<checksum>`

## Data Fields
- Column=0, Field=Identifier, Tag=-, Data Type=String, Format="$PNORI2", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Instrument Type, Tag=IT, Data Type=Integer, Format=N, Unit=-, Description=Instrument model, Notes/Enums=0=Aquadopp, 2=Aquadopp Profiler, 4=Signature
- Column=2, Field=Head ID, Tag=SN, Data Type=Integer, Format=N, Unit=-, Description=Instrument serial number, Notes=Numeric only
- Column=3, Field=Number of Beams, Tag=NB, Data Type=Integer, Format=N, Unit=-, Description=Acoustic beams, Notes=3 or 4
- Column=4, Field=Number of Cells, Tag=NC, Data Type=Integer, Format=N, Unit=-, Description=Measurement cells, Notes=1-128
- Column=5, Field=Blanking Distance, Tag=BD, Data Type=Float, Format=dd.dd, Unit=m, Description=Distance to first cell, Notes=0.00-99.99 m
- Column=6, Field=Cell Size, Tag=CS, Data Type=Float, Format=dd.dd, Unit=m, Description=Size of each cell, Notes=0.00-99.99 m
- Column=7, Field=Coordinate System, Tag=CY, Data Type=String, Format=Text, Unit=-, Description=Velocity coordinates, Notes/Enums=ENU, XYZ, or BEAM
- Column=8, Field=Checksum, Tag=-, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Enumerations
### Instrument Type (IT)
- 0: Aquadopp
- 2: Aquadopp Profiler
- 4: Signature

### Coordinate System (CY)
- ENU: East-North-Up (geographic)
- XYZ: Instrument coordinates
- BEAM: Beam coordinates (radial)

## Example
```
$PNORI2,IT=4,SN=123456,NB=4,NC=30,BD=1.00,CS=5.00,CY=BEAM*68
```

## Interpretation
- Instrument: Signature (IT=4)
- Serial: 123456 (SN=123456)
- Beams: 4-beam system (NB=4)
- Cells: 30 measurement cells (NC=30)
- Blanking: 1.00 m to first cell (BD=1.00)
- Cell size: 5.00 m each (CS=5.00)
- Coordinates: BEAM (beam coordinates, CY=BEAM)
- Checksum: 68

## Notes
- Used in Averaging mode (DF=102) and Burst mode (DF=102)
- All fields have tags (IT=, SN=, etc.)
- Self-describing format
- Easier parsing with tags
- Same data as PNORI1 but with tags
- Coordinate system as text
```

**PNORS2-DF102.md**
```markdown
# PNORS2 - Sensor Data Format 2 (DF=102)

## Description
NMEA-formatted sensor data with tags from Averaging or Burst telemetry modes (Data Format 102).

## Format
`$PNORS2,DATE=<date>,TIME=<time>,EC=<error_code>,SC=<status_code>,BV=<battery>,SS=<sound_speed>,HSD=<heading_stddev>,H=<heading>,PI=<pitch>,PISD=<pitch_stddev>,R=<roll>,RSD=<roll_stddev>,P=<pressure>,PSD=<pressure_stddev>,T=<temperature>*<checksum>`

## Data Fields
- Column=0, Field=Identifier, Tag=-, Data Type=String, Format="$PNORS2", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Date, Tag=DATE, Data Type=Integer, Format=MMDDYY, Unit=-, Description=Measurement date, Notes=MonthDayYear
- Column=2, Field=Time, Tag=TIME, Data Type=Integer, Format=HHMMSS, Unit=-, Description=Measurement time, Notes=HourMinuteSecond
- Column=3, Field=Error Code, Tag=EC, Data Type=Integer, Format=N, Unit=-, Description=System error code, Notes=0=no error
- Column=4, Field=Status Code, Tag=SC, Data Type=Hex, Format=hhhhhhhh, Unit=-, Description=System status, Notes=8 hex digits
- Column=5, Field=Battery Voltage, Tag=BV, Data Type=Float, Format=dd.d, Unit=V, Description=Power supply, Notes=10.0-16.0V typical
- Column=6, Field=Sound Speed, Tag=SS, Data Type=Float, Format=dddd.d, Unit=m/s, Description=Measured sound speed, Notes=1400.0-1600.0 m/s
- Column=7, Field=Heading Std. Dev., Tag=HSD, Data Type=Float, Format=dd.dd, Unit=deg, Description=Heading uncertainty, Notes=0.00-99.99°
- Column=8, Field=Heading, Tag=H, Data Type=Float, Format=ddd.d, Unit=deg, Description=Compass heading, Notes=0.0-359.9°
- Column=9, Field=Pitch, Tag=PI, Data Type=Float, Format=dd.d, Unit=deg, Description=Instrument pitch, Notes=-90.0 to +90.0°
- Column=10, Field=Pitch Std. Dev., Tag=PISD, Data Type=Float, Format=dd.dd, Unit=deg, Description=Pitch uncertainty, Notes=0.00-99.99°
- Column=11, Field=Roll, Tag=R, Data Type=Float, Format=dd.d, Unit=deg, Description=Instrument roll, Notes=-90.0 to +90.0°
- Column=12, Field=Roll Std. Dev., Tag=RSD, Data Type=Float, Format=dd.dd, Unit=deg, Description=Roll uncertainty, Notes=0.00-99.99°
- Column=13, Field=Pressure, Tag=P, Data Type=Float, Format=ddd.ddd, Unit=dBar, Description=Water pressure, Notes=Depth equivalent
- Column=14, Field=Pressure Std. Dev., Tag=PSD, Data Type=Float, Format=dd.dd, Unit=dBar, Description=Pressure uncertainty, Notes=0.00-99.99 dBar
- Column=15, Field=Temperature, Tag=T, Data Type=Float, Format=dd.dd, Unit=°C, Description=Water temperature, Notes=-5.00 to +35.00°C
- Column=16, Field=Checksum, Tag=-, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Example
```
$PNORS2,DATE=083013,TIME=132455,EC=0,SC=34000034,BV=22.9,SS=1500.0,HSD=0.02,H=123.4,PI=45.6,PISD=0.02,R=23.4,RSD=0.02,P=123.456,PSD=0.02,T=24.56*3F
```

## Interpretation
- Date: August 30, 2013 (DATE=083013)
- Time: 13:24:55 UTC (TIME=132455)
- Error: 0 (EC=0)
- Status: 0x34000034 (SC=34000034)
- Battery: 22.9 volts (BV=22.9)
- Sound speed: 1500.0 m/s (SS=1500.0)
- Heading std dev: 0.02° (HSD=0.02)
- Heading: 123.4° (H=123.4)
- Pitch: 45.6° (PI=45.6)
- Pitch std dev: 0.02° (PISD=0.02)
- Roll: 23.4° (R=23.4)
- Roll std dev: 0.02° (RSD=0.02)
- Pressure: 123.456 dBar (P=123.456)
- Pressure std dev: 0.02 dBar (PSD=0.02)
- Temperature: 24.56°C (T=24.56)
- Checksum: 3F

## Notes
- Used in Averaging mode (DF=102) and Burst mode (DF=102)
- All fields have tags (DATE=, TIME=, etc.)
- Self-describing format
- Easier parsing with tags
- Includes standard deviation measurements
- Same data as PNORS1 but with tags
```

**PNORC2-DF102.md**
```markdown
# PNORC2 - Averaged Current Data Format 2 (DF=102)

## Description
NMEA-formatted averaged current data with tags from Averaging or Burst telemetry modes (Data Format 102).

## Format
`$PNORC2,DATE=<date>,TIME=<time>,CN=<cell_num>,CP=<cell_pos>,<velocity_tags>,<amplitude_tags>,<correlation_tags>*<checksum>`

## Data Fields Nortek definition
- Column=0, Field=Identifier, Tag=-, Data Type=String, Format="$PNORC2", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Date, Tag=DATE, Data Type=Integer, Format=MMDDYY, Unit=-, Description=Measurement date, Notes=Always present
- Column=2, Field=Time, Tag=TIME, Data Type=Integer, Format=HHMMSS, Unit=-, Description=Measurement time, Notes=Always present
- Column=3, Field=Cell Number, Tag=CN, Data Type=Integer, Format=N, Unit=-, Description=Measurement cell index, Notes=Always present
- Column=4, Field=Cell Position, Tag=CP, Data Type=Float, Format=dd.d, Unit=m, Description=Distance from transducer, Notes=Always present
- Column=5, Field=Velocity East, Tag=VE, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=East velocity component, Notes=CY=ENU only
- Column=6, Field=Velocity North, Tag=VN, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=North velocity component, Notes=CY=ENU only
- Column=7, Field=Velocity Up, Tag=VU, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Up velocity component, Notes=CY=ENU only
- Column=8, Field=Velocity Up 2, Tag=VU2, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Second up velocity, Notes=CY=ENU only
- Column=9, Field=Velocity X, Tag=VX, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=X velocity component, Notes=CY=XYZ only
- Column=10, Field=Velocity Y, Tag=VY, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Y velocity component, Notes=CY=XYZ only
- Column=11, Field=Velocity Z, Tag=VZ, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Z velocity component, Notes=CY=XYZ only
- Column=12, Field=Velocity Z2, Tag=VZ2, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Second Z velocity, Notes=CY=XYZ only
- Column=13, Field=Velocity Beam 1, Tag=V1, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Beam 1 velocity, Notes=CY=BEAM only
- Column=14, Field=Velocity Beam 2, Tag=V2, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Beam 2 velocity, Notes=CY=BEAM only
- Column=15, Field=Velocity Beam 3, Tag=V3, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Beam 3 velocity, Notes=CY=BEAM only
- Column=16, Field=Velocity Beam 4, Tag=V4, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Beam 4 velocity, Notes=CY=BEAM only
- Column=17, Field=Amplitude Beam 1, Tag=A1, Data Type=Float, Format=ddd.d, Unit=dB, Description=Echo amplitude beam 1, Notes=Always present
- Column=18, Field=Amplitude Beam 2, Tag=A2, Data Type=Float, Format=ddd.d, Unit=dB, Description=Echo amplitude beam 2, Notes=Always present
- Column=19, Field=Amplitude Beam 3, Tag=A3, Data Type=Float, Format=ddd.d, Unit=dB, Description=Echo amplitude beam 3, Notes=Always present
- Column=20, Field=Amplitude Beam 4, Tag=A4, Data Type=Float, Format=ddd.d, Unit=dB, Description=Echo amplitude beam 4, Notes=Always present
- Column=21, Field=Correlation Beam 1, Tag=C1, Data Type=Integer, Format=N, Unit=%, Description=Correlation beam 1, Notes=Always present
- Column=22, Field=Correlation Beam 2, Tag=C2, Data Type=Integer, Format=N, Unit=%, Description=Correlation beam 2, Notes=Always present
- Column=23, Field=Correlation Beam 3, Tag=C3, Data Type=Integer, Format=N, Unit=%, Description=Correlation beam 3, Notes=Always present
- Column=24, Field=Correlation Beam 4, Tag=C4, Data Type=Integer, Format=N, Unit=%, Description=Correlation beam 4, Notes=Always present
- Column=25, Field=Checksum, Tag=-, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Data Fields Logical Interpretation for Parser
- Column=0, Field=Identifier, Tag=-, Data Type=String, Format="$PNORC2", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Date, Tag=DATE, Data Type=Integer, Format=MMDDYY, Unit=-, Description=Measurement date, Notes=Always present
- Column=2, Field=Time, Tag=TIME, Data Type=Integer, Format=HHMMSS, Unit=-, Description=Measurement time, Notes=Always present
- Column=3, Field=Cell Number, Tag=CN, Data Type=Integer, Format=N, Unit=-, Description=Measurement cell index, Notes=Always present
- Column=4, Field=Cell Position, Tag=CP, Data Type=Float, Format=dd.d, Unit=m, Description=Distance from transducer, Notes=Always present
- Column=5, Field=Velocity 1, Tag=V1/VE/VX, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Velocity component 1, Notes=Tag depends on CY (VE, VX, V1)
- Column=6, Field=Velocity 2, Tag=V2/VN/VY, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Velocity component 2, Notes=Tag depends on CY (VN, VY, V2)
- Column=7, Field=Velocity 3, Tag=V3/VU/VZ, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Velocity component 3, Notes=Tag depends on CY (VU, VZ, V3)
- Column=8, Field=Velocity 4, Tag=V4/VU2/VZ2, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Velocity component 4, Notes=Tag depends on CY (VU2, VZ2, V4)
- Column=9, Field=Amplitude Beam 1, Tag=A1, Data Type=Float, Format=ddd.d, Unit=dB, Description=Echo amplitude beam 1, Notes=Always present
- Column=10, Field=Amplitude Beam 2, Tag=A2, Data Type=Float, Format=ddd.d, Unit=dB, Description=Echo amplitude beam 2, Notes=Always present
- Column=11, Field=Amplitude Beam 3, Tag=A3, Data Type=Float, Format=ddd.d, Unit=dB, Description=Echo amplitude beam 3, Notes=Always present
- Column=12, Field=Amplitude Beam 4, Tag=A4, Data Type=Float, Format=ddd.d, Unit=dB, Description=Echo amplitude beam 4, Notes=Always present
- Column=13, Field=Correlation Beam 1, Tag=C1, Data Type=Integer, Format=N, Unit=%, Description=Correlation beam 1, Notes=Always present
- Column=14, Field=Correlation Beam 2, Tag=C2, Data Type=Integer, Format=N, Unit=%, Description=Correlation beam 2, Notes=Always present
- Column=15, Field=Correlation Beam 3, Tag=C3, Data Type=Integer, Format=N, Unit=%, Description=Correlation beam 3, Notes=Always present
- Column=16, Field=Correlation Beam 4, Tag=C4, Data Type=Integer, Format=N, Unit=%, Description=Correlation beam 4, Notes=Always present
- Column=17, Field=Checksum, Tag=-, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Coordinate System Dependencies
- CY=ENU: Velocity fields VE=, VN=, VU=, VU2=
- CY=XYZ: Velocity fields VX=, VY=, VZ=, VZ2=
- CY=BEAM: Velocity fields V1=, V2=, V3=, V4=

## Examples
**ENU Coordinate System:**
```
$PNORC2,DATE=083013,TIME=132455,CN=3,CP=11.0,VE=0.332,VN=0.332,VU=0.332,VU2=0.332,A1=78.9,A2=78.9,A3=78.9,A4=78.9,C1=78,C2=78,C3=78,C4=78*49
```

**BEAM Coordinate System:**
```
$PNORC2,DATE=083013,TIME=132455,CN=3,CP=11.0,V1=0.332,V2=0.332,V3=-0.332,V4=-0.332,A1=78.9,A2=78.9,A3=78.9,A4=78.9,C1=78,C2=78,C3=78,C4=78*49
```

## Notes
- Used in Averaging mode (DF=102) and Burst mode (DF=102)
- All fields have tags (DATE=, TIME=, etc.)
- Velocity fields depend on coordinate system (CY parameter)
- Self-describing format
- Easier parsing with tags
- Repeated for each measurement cell
- Amplitudes in dB
- Three decimal places for velocities
```

**PNORH3-DF103.md**
```markdown
# PNORH3 - Header Data Format 3 (DF=103)

## Description
NMEA-formatted header data with tags from Averaging or Burst telemetry modes (Data Format 103). Simplified header compared to DF=101/102.

## Format
`$PNORH3,DATE=<date>,TIME=<time>,EC=<error_code>,SC=<status_code>*<checksum>`

## Data Fields
- Column=0, Field=Identifier, Tag=-, Data Type=String, Format="$PNORH3", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Date, Tag=DATE, Data Type=Integer, Format=YYMMDD, Unit=-, Description=Measurement date, Notes=YearMonthDay
- Column=2, Field=Time, Tag=TIME, Data Type=Integer, Format=HHMMSS, Unit=-, Description=Measurement time, Notes=HourMinuteSecond
- Column=3, Field=Error Code, Tag=EC, Data Type=Integer, Format=N, Unit=-, Description=System error code, Notes=0=no error
- Column=4, Field=Status Code, Tag=SC, Data Type=Hex, Format=hhhhhhhh, Unit=-, Description=System status, Notes=8 hex digits
- Column=5, Field=Checksum, Tag=-, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Example
```
$PNORH3,DATE=141112,TIME=081946,EC=0,SC=2A4C0000*5F
```

## Interpretation
- Date: November 14, 2012 (DATE=141112)
- Time: 08:19:46 UTC (TIME=081946)
- Error: 0 (EC=0)
- Status: 0x2A4C0000 (SC=2A4C0000)
- Checksum: 5F

## Notes
- Used in Averaging mode (DF=103) and Burst mode (DF=103)
- Simplified header format
- Date format: YYMMDD (different from MMDDYY in DF=101/102)
- All fields have tags
- No instrument configuration data (separate from PNORI1/PNORI2)
- Status code as 8-character hex
```

**PNORS3-DF103.md**
```markdown
# PNORS3 - Sensor Data Format 3 (DF=103)

## Description
NMEA-formatted sensor data with tags from Averaging or Burst telemetry modes (Data Format 103). Simplified sensor data.

## Format
`$PNORS3,BV=<battery>,SS=<sound_speed>,H=<heading>,PI=<pitch>,R=<roll>,P=<pressure>,T=<temperature>*<checksum>`

## Data Fields
- Column=0, Field=Identifier, Tag=-, Data Type=String, Format="$PNORS3", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Battery Voltage, Tag=BV, Data Type=Float, Format=dd.d, Unit=V, Description=Power supply, Notes=10.0-16.0V typical
- Column=2, Field=Sound Speed, Tag=SS, Data Type=Float, Format=dddd.d, Unit=m/s, Description=Measured sound speed, Notes=1400.0-1600.0 m/s
- Column=3, Field=Heading, Tag=H, Data Type=Float, Format=ddd.d, Unit=deg, Description=Compass heading, Notes=0.0-359.9°
- Column=4, Field=Pitch, Tag=PI, Data Type=Float, Format=dd.d, Unit=deg, Description=Instrument pitch, Notes=-90.0 to +90.0°
- Column=5, Field=Roll, Tag=R, Data Type=Float, Format=dd.d, Unit=deg, Description=Instrument roll, Notes=-90.0 to +90.0°
- Column=6, Field=Pressure, Tag=P, Data Type=Float, Format=ddd.ddd, Unit=dBar, Description=Water pressure, Notes=Depth equivalent
- Column=7, Field=Temperature, Tag=T, Data Type=Float, Format=dd.dd, Unit=°C, Description=Water temperature, Notes=-5.00 to +35.00°C
- Column=8, Field=Checksum, Tag=-, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Example
```
$PNORS3,BV=22.9,SS=1546.1,H=151.1,PI=-12.0,R=-5.2,P=705.669,T=24.96*7A
```

## Interpretation
- Battery: 22.9 volts (BV=22.9)
- Sound speed: 1546.1 m/s (SS=1546.1)
- Heading: 151.1° (H=151.1)
- Pitch: -12.0° (PI=-12.0, tilted backward)
- Roll: -5.2° (R=-5.2, tilted left)
- Pressure: 705.669 dBar (P=705.669, ~700 m depth)
- Temperature: 24.96°C (T=24.96)
- Checksum: 7A

## Notes
- Used in Averaging mode (DF=103) and Burst mode (DF=103)
- Simplified sensor data format
- No date/time (in header PNORH3)
- No error/status codes (in header PNORH3)
- No standard deviation measurements
- All fields have tags
- Temperature with two decimal places
```

**PNORC3-DF103.md**
```markdown
# PNORC3 - Averaged Current Data Format 3 (DF=103)

## Description
NMEA-formatted averaged current data with tags from Averaging or Burst telemetry modes (Data Format 103). Simplified current data.

## Format
`$PNORC3,CP=<cell_position>,SP=<speed>,DIR=<direction>,AC=<avg_correlation>,AA=<avg_amplitude>*<checksum>`

## Data Fields
- Column=0, Field=Identifier, Tag=-, Data Type=String, Format="$PNORC3", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Cell Position, Tag=CP, Data Type=Float, Format=dd.d, Unit=m, Description=Distance from transducer, Notes=Always present
- Column=2, Field=Speed, Tag=SP, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Current speed magnitude, Notes=0.000-99.999 m/s
- Column=3, Field=Direction, Tag=DIR, Data Type=Float, Format=ddd.d, Unit=deg, Description=Current direction, Notes=0.0-359.9°
- Column=4, Field=Averaged Correlation, Tag=AC, Data Type=Integer, Format=N, Unit=-, Description=Average correlation, Notes=0-100 typically
- Column=5, Field=Averaged Amplitude, Tag=AA, Data Type=Integer, Format=N, Unit=-, Description=Average amplitude, Notes=0-255 typically
- Column=6, Field=Checksum, Tag=-, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Example
```
$PNORC3,CP=4.5,SP=3.519,DIR=110.9,AC=6,AA=28*3B
```

## Interpretation
- Cell position: 4.5 m from transducer (CP=4.5)
- Speed: 3.519 m/s (SP=3.519)
- Direction: 110.9° (DIR=110.9, ESE)
- Average correlation: 6 (AC=6)
- Average amplitude: 28 (AA=28)
- Checksum: 3B

## Notes
- Used in Averaging mode (DF=103) and Burst mode (DF=103)
- Simplified current data format
- No beam-specific velocities (only speed/direction)
- No individual beam amplitudes/correlations (only averages)
- All fields have tags
- Repeated for each measurement cell
- Direction follows oceanographic convention (coming from)
- Speed with three decimal places
```

**PNORH4-DF104.md**
```markdown
# PNORH4 - Header Data Format 4 (DF=104)

## Description
NMEA-formatted header data without tags from Averaging or Burst telemetry modes (Data Format 104). Simplified header format without tags.

## Format
`$PNORH4,<date>,<time>,<error_code>,<status_code>*<checksum>`

## Data Fields
- Column=0, Field=Identifier, Tag=-, Data Type=String, Format="$PNORH4", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Date, Tag=DATE, Data Type=Integer, Format=YYMMDD, Unit=-, Description=Measurement date, Notes=YearMonthDay
- Column=2, Field=Time, Tag=TIME, Data Type=Integer, Format=HHMMSS, Unit=-, Description=Measurement time, Notes=HourMinuteSecond
- Column=3, Field=Error Code, Tag=EC, Data Type=Integer, Format=N, Unit=-, Description=System error code, Notes=0=no error
- Column=4, Field=Status Code, Tag=SC, Data Type=Hex, Format=hhhhhhhh, Unit=-, Description=System status, Notes=8 hex digits
- Column=5, Field=Checksum, Tag=-, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Example
```
$PNORH4,141112,083149,0,2A4C0000*4A68
```

## Interpretation
- Date: November 14, 2012 (141112)
- Time: 08:31:49 UTC (083149)
- Error: 0 (no error)
- Status: 0x2A4C0000 (2A4C0000)
- Checksum: 4A68

## Notes
- Used in Averaging mode (DF=104) and Burst mode (DF=104)
- Simplified header format
- No tags in data fields
- Date format: YYMMDD (different from MMDDYY in DF=101/102)
- Same data as PNORH3 but without tags
- Checksum may include more characters
```

**PNORS4-DF104.md**
```markdown
# PNORS4 - Sensor Data Format 4 (DF=104)

## Description
NMEA-formatted sensor data without tags from Averaging or Burst telemetry modes (Data Format 104). Simplified sensor data without tags.

## Format
`$PNORS4,<battery>,<sound_speed>,<heading>,<pitch>,<roll>,<pressure>,<temperature>*<checksum>`

## Data Fields
- Column=0, Field=Identifier, Tag=-, Data Type=String, Format="$PNORS4", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Battery Voltage, Tag=BV, Data Type=Float, Format=dd.d, Unit=V, Description=Power supply, Notes=10.0-16.0V typical
- Column=2, Field=Sound Speed, Tag=SS, Data Type=Float, Format=dddd.d, Unit=m/s, Description=Measured sound speed, Notes=1400.0-1600.0 m/s
- Column=3, Field=Heading, Tag=H, Data Type=Float, Format=ddd.d, Unit=deg, Description=Compass heading, Notes=0.0-359.9°
- Column=4, Field=Pitch, Tag=PI, Data Type=Float, Format=dd.d, Unit=deg, Description=Instrument pitch, Notes=-90.0 to +90.0°
- Column=5, Field=Roll, Tag=R, Data Type=Float, Format=dd.d, Unit=deg, Description=Instrument roll, Notes=-90.0 to +90.0°
- Column=6, Field=Pressure, Tag=P, Data Type=Float, Format=ddd.ddd, Unit=dBar, Description=Water pressure, Notes=Depth equivalent
- Column=7, Field=Temperature, Tag=T, Data Type=Float, Format=dd.dd, Unit=°C, Description=Water temperature, Notes=-5.00 to +35.00°C
- Column=8, Field=Checksum, Tag=-, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Example
```
$PNORS4,22.9,1546.1,151.2,-11.9,-5.3,705.658,24.95*5A
```

## Interpretation
- Battery: 22.9 volts
- Sound speed: 1546.1 m/s
- Heading: 151.2°
- Pitch: -11.9° (tilted backward)
- Roll: -5.3° (tilted left)
- Pressure: 705.658 dBar (~700 m depth)
- Temperature: 24.95°C
- Checksum: 5A

## Notes
- Used in Averaging mode (DF=104) and Burst mode (DF=104)
- Simplified sensor data format
- No tags in data fields
- No date/time (in header PNORH4)
- No error/status codes (in header PNORH4)
- No standard deviation measurements
- Same data as PNORS3 but without tags
```

**PNORC4-DF104.md**
```markdown
# PNORC4 - Averaged Current Data Format 4 (DF=104)

## Description
NMEA-formatted averaged current data without tags from Averaging or Burst telemetry modes (Data Format 104). Simplified current data without tags.

## Format
`$PNORC4,<cell_position>,<speed>,<direction>,<avg_correlation>,<avg_amplitude>*<checksum>`

## Data Fields
- Column=0, Field=Identifier, Tag=-, Data Type=String, Format="$PNORC4", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Cell Position, Tag=CP, Data Type=Float, Format=dd.d, Unit=m, Description=Distance from transducer, Notes=Always present
- Column=2, Field=Speed, Tag=SP, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Current speed magnitude, Notes=0.000-99.999 m/s
- Column=3, Field=Direction, Tag=DIR, Data Type=Float, Format=ddd.d, Unit=deg, Description=Current direction, Notes=0.0-359.9°
- Column=4, Field=Averaged Correlation, Tag=AC, Data Type=Integer, Format=N, Unit=-, Description=Average correlation, Notes=0-100 typically
- Column=5, Field=Averaged Amplitude, Tag=AA, Data Type=Integer, Format=N, Unit=-, Description=Average amplitude, Notes=0-255 typically
- Column=6, Field=Checksum, Tag=-, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Example
```
$PNORC4,27.5,1.815,322.6,4,28*70
```

## Interpretation
- Cell position: 27.5 m from transducer
- Speed: 1.815 m/s
- Direction: 322.6° (NW)
- Average correlation: 4
- Average amplitude: 28
- Checksum: 70

## Notes
- Used in Averaging mode (DF=104) and Burst mode (DF=104)
- Simplified current data format
- No tags in data fields
- No beam-specific velocities (only speed/direction)
- No individual beam amplitudes/correlations (only averages)
- Same data as PNORC3 but without tags
- Repeated for each measurement cell
- Direction follows oceanographic convention (coming from)
```

**PNORA-DF200.md**
```markdown
# PNORA - Altimeter Data (DF=200)

## Description
NMEA-formatted altimeter data without tags from Altimeter telemetry mode (Data Format 200). Always uses Leading Edge algorithm.

## Format
`$PNORA,<date>,<time>,<pressure>,<altimeter_distance>,<quality>,<status>,<pitch>,<roll>*<checksum>`

## Data Fields
- Column=0, Field=Identifier, Data Type=String, Format="$PNORA", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Date, Data Type=Integer, Format=YYMMDD, Unit=-, Description=Measurement date, Notes=YearMonthDay
- Column=2, Field=Time, Data Type=Integer, Format=hhmmss, Unit=-, Description=Measurement time, Notes=HourMinuteSecond
- Column=3, Field=Pressure, Data Type=Float, Format=ddd.ddd, Unit=dBar, Description=Water pressure, Notes=Depth equivalent
- Column=4, Field=Altimeter Distance, Data Type=Float, Format=ddd.ddd, Unit=m, Description=Leading edge distance, Notes=Range dependent
- Column=5, Field=Quality Parameter, Data Type=Integer, Format=N, Unit=-, Description=Quality indicator, Notes=See notes
- Column=6, Field=Status, Data Type=String, Format=XX, Unit=-, Description=Status code, Notes=2 hex characters
- Column=7, Field=Pitch, Data Type=Float, Format=d.d, Unit=deg, Description=Instrument pitch, Notes=Signed, -9.9 to +9.9°
- Column=8, Field=Roll, Data Type=Float, Format=d.d, Unit=deg, Description=Instrument roll, Notes=Signed, -9.9 to +9.9°
- Column=9, Field=Checksum, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Example
```
$PNORA,190902,122341,0.000,24.274,13068,08,-2.6,-0.8*7E
```

## Interpretation
- Date: September 2, 2019 (190902)
- Time: 12:23:41 UTC (122341)
- Pressure: 0.000 dBar (surface)
- Altimeter distance: 24.274 m
- Quality parameter: 13068
- Status: 08 (hex)
- Pitch: -2.6° (tilted backward)
- Roll: -0.8° (slight left tilt)
- Checksum: 7E

## Quality Parameter
- Bitfield indicating measurement quality
- Higher values generally indicate better quality
- Specific bit definitions in instrument documentation

## Status Codes
- 2-character hex code
- 00: Normal operation
- Other values indicate specific states/errors

## Notes
- Used in Altimeter mode with DF=200
- No tags in data fields
- Always uses Leading Edge algorithm
- Date format: YYMMDD
- Time format: hhmmss
```

**PNORA-DF201.md**
```markdown
# PNORA - Altimeter Data with Tags (DF=201)

## Description
NMEA-formatted altimeter data with tags from Altimeter telemetry mode (Data Format 201). Always uses Leading Edge algorithm.

## Format
`$PNORA,DATE=<date>,TIME=<time>,P=<pressure>,A=<altimeter_distance>,Q=<quality>,ST=<status>,PI=<pitch>,R=<roll>*<checksum>`

## Data Fields
- Column=0, Field=Identifier, Tag=-, Data Type=String, Format="$PNORA", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Date, Tag=DATE, Data Type=Integer, Format=YYMMDD, Unit=-, Description=Measurement date, Notes=YearMonthDay
- Column=2, Field=Time, Tag=TIME, Data Type=Integer, Format=hhmmss, Unit=-, Description=Measurement time, Notes=HourMinuteSecond
- Column=3, Field=Pressure, Tag=P, Data Type=Float, Format=ddd.ddd, Unit=dBar, Description=Water pressure, Notes=Depth equivalent
- Column=4, Field=Altimeter Distance, Tag=A, Data Type=Float, Format=ddd.ddd, Unit=m, Description=Leading edge distance, Notes=Range dependent
- Column=5, Field=Quality Parameter, Tag=Q, Data Type=Integer, Format=N, Unit=-, Description=Quality indicator, Notes=See notes
- Column=6, Field=Status, Tag=ST, Data Type=String, Format=XX, Unit=-, Description=Status code, Notes=2 hex characters
- Column=7, Field=Pitch, Tag=PI, Data Type=Float, Format=d.d, Unit=deg, Description=Instrument pitch, Notes=Signed, -9.9 to +9.9°
- Column=8, Field=Roll, Tag=R, Data Type=Float, Format=d.d, Unit=deg, Description=Instrument roll, Notes=Signed, -9.9 to +9.9°
- Column=9, Field=Checksum, Tag=-, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Example
```
$PNORA,DATE=190902,TIME=122341,P=0.000,A=24.274,Q=13068,ST=08,PI=-2.6,R=-0.8*72
```

## Interpretation
- Date: September 2, 2019 (DATE=190902)
- Time: 12:23:41 UTC (TIME=122341)
- Pressure: 0.000 dBar (P=0.000, surface)
- Altimeter distance: 24.274 m (A=24.274)
- Quality parameter: 13068 (Q=13068)
- Status: 08 (hex, ST=08)
- Pitch: -2.6° (PI=-2.6, tilted backward)
- Roll: -0.8° (R=-0.8, slight left tilt)
- Checksum: 72

## Quality Parameter
- Bitfield indicating measurement quality
- Higher values generally indicate better quality
- Specific bit definitions in instrument documentation

## Status Codes
- 2-character hex code
- 00: Normal operation
- Other values indicate specific states/errors

## Notes
- Used in Altimeter mode with DF=201
- All fields have tags
- Always uses Leading Edge algorithm
- Date format: YYMMDD
- Time format: hhmmss
- Same data as DF=200 but with tags
```

**PNORW-DF501.md**
```markdown
# PNORW - Wave Parameters (DF=501)

## Description
NMEA-formatted wave parameters from Waves telemetry mode (Data Format 501). Contains bulk wave statistics.

## Format
`$PNORW,<date>,<time>,<spectrum_basis>,<processing_method>,<hm0>,<h3>,<h10>,<hmax>,<tm02>,<tp>,<tz>,<dirtp>,<sprtp>,<main_dir>,<uni_index>,<mean_pressure>,<num_no_detects>,<num_bad_detects>,<near_surface_speed>,<near_surface_dir>,<wave_error_code>*<checksum>`

## Data Fields
- Column=0, Field=Identifier, Data Type=String, Format="$PNORW", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Date, Data Type=Integer, Format=MMDDYY, Unit=-, Description=Measurement date, Notes=MonthDayYear
- Column=2, Field=Time, Data Type=Integer, Format=hhmmss, Unit=-, Description=Measurement time, Notes=HourMinuteSecond
- Column=3, Field=Spectrum Basis Type, Data Type=Integer, Format=N, Unit=-, Description=Spectrum source, Notes/Enums=0=Pressure, 1=Velocity, 3=AST
- Column=4, Field=Processing Method, Data Type=Integer, Format=N, Unit=-, Description=Processing algorithm, Notes/Enums=1=PUV, 2=SUV, 3=MLM, 4=MLMST
- Column=5, Field=Hm0, Data Type=Float, Format=dd.dd, Unit=m, Description=Significant wave height, Notes=0.00-99.99 m
- Column=6, Field=H3, Data Type=Float, Format=dd.dd, Unit=m, Description=1/3 highest wave height, Notes=0.00-99.99 m
- Column=7, Field=H10, Data Type=Float, Format=dd.dd, Unit=m, Description=1/10 highest wave height, Notes=0.00-99.99 m
- Column=8, Field=Hmax, Data Type=Float, Format=dd.dd, Unit=m, Description=Maximum wave height, Notes=0.00-99.99 m
- Column=9, Field=Tm02, Data Type=Float, Format=dd.dd, Unit=s, Description=Mean wave period, Notes=0.00-99.99 s
- Column=10, Field=Tp, Data Type=Float, Format=dd.dd, Unit=s, Description=Peak period, Notes=0.00-99.99 s
- Column=11, Field=Tz, Data Type=Float, Format=dd.dd, Unit=s, Description=Zero-crossing period, Notes=0.00-99.99 s
- Column=12, Field=DirTp, Data Type=Float, Format=ddd.dd, Unit=deg, Description=Direction at peak frequency, Notes=0.00-359.99°
- Column=13, Field=SprTp, Data Type=Float, Format=ddd.dd, Unit=deg, Description=Spread at peak frequency, Notes=0.00-359.99°
- Column=14, Field=Main Direction, Data Type=Float, Format=ddd.dd, Unit=deg, Description=Mean wave direction, Notes=0.00-359.99°
- Column=15, Field=Unidirectivity Index, Data Type=Float, Format=dd.dd, Unit=-, Description=Directional spreading index, Notes=0.00-1.00
- Column=16, Field=Mean Pressure, Data Type=Float, Format=dd.dd, Unit=dbar, Description=Average pressure, Notes=-99.99 to 99.99 dbar
- Column=17, Field=Number of No Detects, Data Type=Integer, Format=N, Unit=-, Description=Failed detections, Notes=Count
- Column=18, Field=Number of Bad Detects, Data Type=Integer, Format=N, Unit=-, Description=Poor quality detections, Notes=Count
- Column=19, Field=Near Surface Current Speed, Data Type=Float, Format=dd.dd, Unit=m/s, Description=Surface current speed, Notes=0.00-99.99 m/s
- Column=20, Field=Near Surface Current Direction, Data Type=Float, Format=ddd.dd, Unit=deg, Description=Surface current direction, Notes=0.00-359.99°
- Column=21, Field=Wave Error Code, Data Type=Hex, Format=hhhh, Unit=-, Description=Wave processing errors, Notes=4 hex digits
- Column=22, Field=Checksum, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Enumerations
### Spectrum Basis Type
- 0: Pressure-based
- 1: Velocity-based
- 3: AST (Acoustic Surface Tracking)

### Processing Method
- 1: PUV (Pressure-U-V)
- 2: SUV (Surface U-V)
- 3: MLM (Maximum Likelihood Method)
- 4: MLMST (MLM Surface Tracking)

## Example
```
$PNORW,120720,093150,0,1,0.89,-9.00,1.13,1.49,1.41,1.03,-9.00,190.03,80.67,113.52,0.54,0.00,1024,0,1.19,144.11,0D8B*7B
```

## Interpretation
- Date: July 20, 2012 (120720)
- Time: 09:31:50 UTC (093150)
- Spectrum basis: Pressure-based (0)
- Processing: PUV (1)
- Hm0: 0.89 m
- H3: -9.00 (invalid)
- H10: 1.13 m
- Hmax: 1.49 m
- Tm02: 1.41 s
- Tp: 1.03 s
- Tz: -9.00 (invalid)
- DirTp: 190.03°
- SprTp: 80.67°
- Main direction: 113.52°
- Unidirectivity index: 0.54
- Mean pressure: 0.00 dbar
- No detects: 1024
- Bad detects: 0
- Near surface speed: 1.19 m/s
- Near surface direction: 144.11°
- Wave error code: 0D8B
- Checksum: 7B

## Invalid Data Indicators
- Values like -9.00, -999 indicate invalid/missing data
- Empty fields indicate unused parameters

## Notes
- Used in Waves mode with DF=501
- Contains bulk wave statistics
- Error code indicates wave processing issues
- Near surface currents from upper bins
- Pressure mean for depth reference
- Invalid data marked with -9.00 or similar
```

**PNORB-DF501.md**
```markdown
# PNORB - Wave Band Parameters (DF=501)

## Description
NMEA-formatted wave band parameters from Waves telemetry mode (Data Format 501). Contains statistics for specific frequency bands.

## Format
`$PNORB,<date>,<time>,<spectrum_basis>,<processing_method>,<freq_low>,<freq_high>,<hmo>,<tm02>,<tp>,<dirtp>,<sprtp>,<main_dir>,<wave_error_code>*<checksum>`

## Data Fields
- Column=0, Field=Identifier, Data Type=String, Format="$PNORB", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Date, Data Type=Integer, Format=MMDDYY, Unit=-, Description=Measurement date, Notes=MonthDayYear
- Column=2, Field=Time, Data Type=Integer, Format=hhmmss, Unit=-, Description=Measurement time, Notes=HourMinuteSecond
- Column=3, Field=Spectrum Basis Type, Data Type=Integer, Format=N, Unit=-, Description=Spectrum source, Notes/Enums=0=Pressure, 1=Velocity, 3=AST
- Column=4, Field=Processing Method, Data Type=Integer, Format=N, Unit=-, Description=Processing algorithm, Notes/Enums=1=PUV, 2=SUV, 3=MLM, 4=MLMST
- Column=5, Field=Frequency Low, Data Type=Float, Format=d.dd, Unit=Hz, Description=Band lower frequency, Notes=0.00-9.99 Hz
- Column=6, Field=Frequency High, Data Type=Float, Format=d.dd, Unit=Hz, Description=Band upper frequency, Notes=0.00-9.99 Hz
- Column=7, Field=Hmo, Data Type=Float, Format=dd.dd, Unit=m, Description=Significant wave height in band, Notes=0.00-99.99 m
- Column=8, Field=Tm02, Data Type=Float, Format=dd.dd, Unit=s, Description=Mean period in band, Notes=0.00-99.99 s
- Column=9, Field=Tp, Data Type=Float, Format=dd.dd, Unit=s, Description=Peak period in band, Notes=0.00-99.99 s
- Column=10, Field=DirTp, Data Type=Float, Format=ddd.dd, Unit=deg, Description=Direction at peak in band, Notes=0.00-359.99°
- Column=11, Field=SprTp, Data Type=Float, Format=ddd.dd, Unit=deg, Description=Spread at peak in band, Notes=0.00-359.99°
- Column=12, Field=Main Direction, Data Type=Float, Format=ddd.dd, Unit=deg, Description=Mean direction in band, Notes=0.00-359.99°
- Column=13, Field=Wave Error Code, Data Type=Hex, Format=hhhh, Unit=-, Description=Wave processing errors, Notes=4 hex digits
- Column=14, Field=Checksum, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Enumerations
### Spectrum Basis Type
- 0: Pressure-based
- 1: Velocity-based
- 3: AST (Acoustic Surface Tracking)

### Processing Method
- 1: PUV (Pressure-U-V)
- 2: SUV (Surface U-V)
- 3: MLM (Maximum Likelihood Method)
- 4: MLMST (MLM Surface Tracking)

## Examples
```
$PNORB,120720,093150,1,4,0.02,0.20,0.27,7.54,12.00,82.42,75.46,82.10,0000*67
$PNORB,120720,093150,1,4,0.21,0.99,0.83,1.36,1.03,45.00,0.00,172.16,0000*5C
```

## Interpretation Example 1
- Date: July 20, 2012 (120720)
- Time: 09:31:50 UTC (093150)
- Spectrum basis: Velocity-based (1)
- Processing: MLMST (4)
- Frequency band: 0.02-0.20 Hz
- Hmo: 0.27 m
- Tm02: 7.54 s
- Tp: 12.00 s
- DirTp: 82.42°
- SprTp: 75.46°
- Main direction: 82.10°
- Wave error code: 0000
- Checksum: 67

## Interpretation Example 2
- Date: July 20, 2012 (120720)
- Time: 09:31:50 UTC (093150)
- Spectrum basis: Velocity-based (1)
- Processing: MLMST (4)
- Frequency band: 0.21-0.99 Hz
- Hmo: 0.83 m
- Tm02: 1.36 s
- Tp: 1.03 s
- DirTp: 45.00°
- SprTp: 0.00°
- Main direction: 172.16°
- Wave error code: 0000
- Checksum: 5C

## Notes
- Used in Waves mode with DF=501
- Multiple sentences for different frequency bands
- Band-specific wave statistics
- Error code indicates processing issues
- Frequency bands defined by instrument configuration
- Typically used for swell/wind sea separation
```

**PNORE-DF501.md**
```markdown
# PNORE - Wave Energy Density Spectrum (DF=501)

## Description
NMEA-formatted wave energy density spectrum from Waves telemetry mode (Data Format 501). Contains spectral energy values at discrete frequencies.

## Format
`$PNORE,<date>,<time>,<spectrum_basis>,<start_freq>,<step_freq>,<num_freq>,<energy1>,<energy2>,...,<energyN>*<checksum>`

## Data Fields
- Column=0, Field=Identifier, Data Type=String, Format="$PNORE", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Date, Data Type=Integer, Format=MMDDYY, Unit=-, Description=Measurement date, Notes=MonthDayYear
- Column=2, Field=Time, Data Type=Integer, Format=hhmmss, Unit=-, Description=Measurement time, Notes=HourMinuteSecond
- Column=3, Field=Spectrum Basis Type, Data Type=Integer, Format=N, Unit=-, Description=Spectrum source, Notes/Enums=0=Pressure, 1=Velocity, 3=AST
- Column=4, Field=Start Frequency, Data Type=Float, Format=d.dd, Unit=Hz, Description=First frequency bin, Notes=0.00-9.99 Hz
- Column=5, Field=Step Frequency, Data Type=Float, Format=d.dd, Unit=Hz, Description=Frequency resolution, Notes=0.00-9.99 Hz
- Column=6, Field=Number of Frequencies, Data Type=Integer, Format=mm, Unit=-, Description=Number of frequency bins, Notes=1-99
- Column=7, Field=Energy Density (frequency 1), Data Type=Float, Format=dddd.ddd, Unit=cm²/Hz, Description=Spectral energy at first frequency, Notes=0.000-9999.999
- Column=8, Field=Energy Density (frequency 2), Data Type=Float, Format=dddd.ddd, Unit=cm²/Hz, Description=Spectral energy at second frequency, Notes=0.000-9999.999
- ... (continues for N frequencies)
- Column=N+6, Field=Energy Density (frequency N), Data Type=Float, Format=dddd.ddd, Unit=cm²/Hz, Description=Spectral energy at last frequency, Notes=0.000-9999.999
- Column=N+7, Field=Checksum, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Enumerations
### Spectrum Basis Type
- 0: Pressure-based
- 1: Velocity-based
- 3: AST (Acoustic Surface Tracking)

## Example (truncated)
```
$PNORE,120720,093150,1,0.02,0.01,98,0.000,0.000,0.000,0.000,0.003,0.012,0.046,0.039,0.041,0.039,0.036,0.039,0.041,0.034,0.034,0.031,0.026,0.027,0.025,0.024,0.023,0.025,0.023,0.020,0.020,0.025,0.023,0.027,0.029,0.033,0.029,0.033,0.028,0.032,0.031,0.033,0.029,0.032,0.032,0.031,0.041,0.038,0.043,0.050,0.048,0.042,0.034,0.030,0.033,0.039,0.036,0.035,0.042,0.039,0.038,0.044,0.042,0.054,0.064,0.054,0.051,0.064,0.062,0.051,0.049,0.066,0.068,0.073,0.062,0.064,0.062,0.063,0.059,0.060,0.051,0.049,0.059,0.075,0.096,0.093,0.084,0.084,0.074,0.081,0.076,0.103,0.113,0.117,0.125,0.131,0.144,0.143,0.129*71
```

## Interpretation
- Date: July 20, 2012 (120720)
- Time: 09:31:50 UTC (093150)
- Spectrum basis: Velocity-based (1)
- Start frequency: 0.02 Hz
- Step frequency: 0.01 Hz
- Number of frequencies: 98 bins
- Energy densities: Series of 98 values (0.000 to 0.144 cm²/Hz)
- Checksum: 71

## Notes
- Used in Waves mode with DF=501
- Contains full energy spectrum
- Unit: cm²/Hz (centimeter squared per Hertz)
- Frequencies calculated as: Start + (n-1)*Step
- N frequencies means N+7 total columns
- Long sentences may exceed NMEA length limits
- Typically split into multiple sentences if needed
- Energy values indicate wave power distribution
```

**PNORF-DF501.md**
```markdown
# PNORF - Fourier Coefficient Spectra (DF=501)

## Description
NMEA-formatted Fourier coefficient spectra from Waves telemetry mode (Data Format 501). Contains directional Fourier coefficients A1, B1, A2, B2.

## Format
`$PNORF,<coeff_flag>,<date>,<time>,<spectrum_basis>,<start_freq>,<step_freq>,<num_freq>,<coeff1>,<coeff2>,...,<coeffN>*<checksum>`

## Data Fields
- Column=0, Field=Identifier, Data Type=String, Format="$PNORF", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Fourier Coefficient Flag, Data Type=String, Format="CC", Unit=-, Description=Coefficient type, Notes/Enums=A1, B1, A2, B2
- Column=2, Field=Date, Data Type=Integer, Format=MMDDYY, Unit=-, Description=Measurement date, Notes=MonthDayYear
- Column=3, Field=Time, Data Type=Integer, Format=hhmmss, Unit=-, Description=Measurement time, Notes=HourMinuteSecond
- Column=4, Field=Spectrum Basis Type, Data Type=Integer, Format=N, Unit=-, Description=Spectrum source, Notes/Enums=0=Pressure, 1=Velocity, 3=AST
- Column=5, Field=Start Frequency, Data Type=Float, Format=d.dd, Unit=Hz, Description=First frequency bin, Notes=0.00-9.99 Hz
- Column=6, Field=Step Frequency, Data Type=Float, Format=d.dd, Unit=Hz, Description=Frequency resolution, Notes=0.00-9.99 Hz
- Column=7, Field=Number of Frequencies, Data Type=Integer, Format=nnn, Unit=-, Description=Number of frequency bins, Notes=1-999
- Column=8, Field=Fourier Coefficient (frequency 1), Data Type=Float, Format=dddd.ddd, Unit=-, Description=Coefficient value at first frequency, Notes=-9999.999 to 9999.999
- Column=9, Field=Fourier Coefficient (frequency 2), Data Type=Float, Format=dddd.ddd, Unit=-, Description=Coefficient value at second frequency, Notes=-9999.999 to 9999.999
- ... (continues for N frequencies)
- Column=N+7, Field=Fourier Coefficient (frequency N), Data Type=Float, Format=dddd.ddd, Unit=-, Description=Coefficient value at last frequency, Notes=-9999.999 to 9999.999
- Column=N+8, Field=Checksum, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Enumerations
### Fourier Coefficient Flag
- A1: First cosine coefficient
- B1: First sine coefficient
- A2: Second cosine coefficient
- B2: Second sine coefficient

### Spectrum Basis Type
- 0: Pressure-based
- 1: Velocity-based
- 3: AST (Acoustic Surface Tracking)

## Examples (truncated)
```
$PNORF,A1,120720,093150,1,0.02,0.01,98,0.0348,0.0958,0.1372,0.1049,-0.0215,-0.0143,0.0358,0.0903,0.0350,0.0465,-0.0097,0.0549,-0.0507,-0.0071,-0.0737,0.0459,-0.0164,0.0275,-0.0190,-0.0327,-0.0324,-0.0364,-0.0255,-0.0140,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000*0D
```

## Interpretation
- Coefficient type: A1 (first cosine)
- Date: July 20, 2012 (120720)
- Time: 09:31:50 UTC (093150)
- Spectrum basis: Velocity-based (1)
- Start frequency: 0.02 Hz
- Step frequency: 0.01 Hz
- Number of frequencies: 98 bins
- Coefficients: Series of 98 values
- Invalid data: -9.0000 indicates missing/invalid
- Checksum: 0D

## Notes
- Used in Waves mode with DF=501
- Four separate sentences for A1, B1, A2, B2
- Used to reconstruct directional spectra
- Invalid data marked with -9.0000
- Fourier coefficients for directional analysis
- A1/B1: First harmonic (mean direction)
- A2/B2: Second harmonic (directional spread)
- Long sentences may be truncated in example
```

**PNORWD-DF501.md**
```markdown
# PNORWD - Wave Directional Spectra (DF=501)

## Description
NMEA-formatted wave directional spectra from Waves telemetry mode (Data Format 501). Contains mean direction and directional spread per frequency.

## Format
`$PNORWD,<dir_type>,<date>,<time>,<spectrum_basis>,<start_freq>,<step_freq>,<num_freq>,<value1>,<value2>,...,<valueN>*<checksum>`

## Data Fields
- Column=0, Field=Identifier, Data Type=String, Format="$PNORWD", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Direction Type, Data Type=String, Format="CC", Unit=-, Description=Parameter type, Notes/Enums=MD=Main Direction, DS=Directional Spread
- Column=2, Field=Date, Data Type=Integer, Format=MMDDYY, Unit=-, Description=Measurement date, Notes=MonthDayYear
- Column=3, Field=Time, Data Type=Integer, Format=hhmmss, Unit=-, Description=Measurement time, Notes=HourMinuteSecond
- Column=4, Field=Spectrum Basis Type, Data Type=Integer, Format=N, Unit=-, Description=Spectrum source, Notes/Enums=0=Pressure, 1=Velocity, 3=AST
- Column=5, Field=Start Frequency, Data Type=Float, Format=d.dd, Unit=Hz, Description=First frequency bin, Notes=0.00-9.99 Hz
- Column=6, Field=Step Frequency, Data Type=Float, Format=d.dd, Unit=Hz, Description=Frequency resolution, Notes=0.00-9.99 Hz
- Column=7, Field=Number of Frequencies, Data Type=Integer, Format=nnn, Unit=-, Description=Number of frequency bins, Notes=1-999
- Column=8, Field=Direction/Spread (frequency 1), Data Type=Float, Format=dddd.ddd, Unit=deg, Description=Value at first frequency, Notes=0.000-359.999° for MD, 0.000-180.000° for DS
- Column=9, Field=Direction/Spread (frequency 2), Data Type=Float, Format=dddd.ddd, Unit=deg, Description=Value at second frequency, Notes=0.000-359.999° for MD, 0.000-180.000° for DS
- ... (continues for N frequencies)
- Column=N+7, Field=Direction/Spread (frequency N), Data Type=Float, Format=dddd.ddd, Unit=deg, Description=Value at last frequency, Notes=0.000-359.999° for MD, 0.000-180.000° for DS
- Column=N+8, Field=Checksum, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Enumerations
### Direction Type
- MD: Main Direction (mean wave direction per frequency)
- DS: Directional Spread (angular spread per frequency)

### Spectrum Basis Type
- 0: Pressure-based
- 1: Velocity-based
- 3: AST (Acoustic Surface Tracking)

## Examples (truncated)
```
$PNORWD,MD,120720,093150,1,0.02,0.01,98,326.5016,335.7948,11.6072,8.1730,147.6098,107.1336,74.8001,55.4424,55.0203,50.8304,120.0490,52.4414,180.2204,113.3304,203.1034,55.0302,195.6657,52.9780,196.9988,145.2517,177.5576,168.0439,176.1304,163.7607,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000*05
```

## Interpretation (MD example)
- Direction type: MD (Main Direction)
- Date: July 20, 2012 (120720)
- Time: 09:31:50 UTC (093150)
- Spectrum basis: Velocity-based (1)
- Start frequency: 0.02 Hz
- Step frequency: 0.01 Hz
- Number of frequencies: 98 bins
- Directions: Series of 98 values (11.6072° to 326.5016°)
- Invalid data: -9.0000 indicates missing/invalid
- Checksum: 05

## Notes
- Used in Waves mode with DF=501
- Two separate sentences: MD and DS
- MD: Mean wave direction per frequency (0-360°)
- DS: Directional spread per frequency (0-180°)
- Invalid data marked with -9.0000
- Used for full directional analysis
- Complement to Fourier coefficients
- Provides frequency-dependent direction info
```

**PNORI1-BURST-DF101.md**
```markdown
# PNORI1 - Information Data Format 1 (Burst Mode, DF=101)

## Description
NMEA-formatted configuration information without tags from Burst telemetry mode (Data Format 101). Identical to Averaging mode PNORI1.

## Format
`$PNORI1,<instrument_type>,<head_id>,<num_beams>,<num_cells>,<blanking>,<cell_size>,<coord_system>*<checksum>`

## Data Fields
- Column=0, Field=Identifier, Tag=-, Data Type=String, Format="$PNORI1", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Instrument Type, Tag=IT, Data Type=Integer, Format=N, Unit=-, Description=Instrument model, Notes/Enums=0=Aquadopp, 2=Aquadopp Profiler, 4=Signature
- Column=2, Field=Head ID, Tag=SN, Data Type=Integer, Format=N, Unit=-, Description=Instrument serial number, Notes=Numeric only
- Column=3, Field=Number of Beams, Tag=NB, Data Type=Integer, Format=N, Unit=-, Description=Acoustic beams, Notes=3 or 4
- Column=4, Field=Number of Cells, Tag=NC, Data Type=Integer, Format=N, Unit=-, Description=Measurement cells, Notes=1-128
- Column=5, Field=Blanking Distance, Tag=BD, Data Type=Float, Format=dd.dd, Unit=m, Description=Distance to first cell, Notes=0.00-99.99 m
- Column=6, Field=Cell Size, Tag=CS, Data Type=Float, Format=dd.dd, Unit=m, Description=Size of each cell, Notes=0.00-99.99 m
- Column=7, Field=Coordinate System, Tag=CY, Data Type=String, Format=Text, Unit=-, Description=Velocity coordinates, Notes/Enums=ENU, XYZ, or BEAM
- Column=8, Field=Checksum, Tag=-, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Enumerations
### Instrument Type (IT)
- 0: Aquadopp
- 2: Aquadopp Profiler
- 4: Signature

### Coordinate System (CY)
- ENU: East-North-Up (geographic)
- XYZ: Instrument coordinates
- BEAM: Beam coordinates (radial)

## Example
```
$PNORI1,4,123456,4,30,1.00,5.00,BEAM*5B
```

## Interpretation
- Instrument: Signature (4)
- Serial: 123456
- Beams: 4-beam system
- Cells: 30 measurement cells
- Blanking: 1.00 m to first cell
- Cell size: 5.00 m each
- Coordinates: BEAM (beam coordinates)
- Checksum: 5B

## Notes
- Used in Burst mode with DF=101
- Identical to Averaging mode PNORI1
- No tags in data fields (tagless format)
- Head ID is numeric only
- Coordinate system as text (not numeric code)
- Part of Burst telemetry data stream
```

**PNORS1-BURST-DF101.md**
```markdown
# PNORS1 - Sensor Data Format 1 (Burst Mode, DF=101)

## Description
NMEA-formatted sensor data without tags from Burst telemetry mode (Data Format 101). Identical to Averaging mode PNORS1.

## Format
`$PNORS1,<date>,<time>,<error_code>,<status_code>,<battery>,<sound_speed>,<heading_stddev>,<heading>,<pitch>,<pitch_stddev>,<roll>,<roll_stddev>,<pressure>,<pressure_stddev>,<temperature>*<checksum>`

## Data Fields
- Column=0, Field=Identifier, Tag=-, Data Type=String, Format="$PNORS1", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Date, Tag=DATE, Data Type=Integer, Format=MMDDYY, Unit=-, Description=Measurement date, Notes=MonthDayYear
- Column=2, Field=Time, Tag=TIME, Data Type=Integer, Format=HHMMSS, Unit=-, Description=Measurement time, Notes=HourMinuteSecond
- Column=3, Field=Error Code, Tag=EC, Data Type=Integer, Format=N, Unit=-, Description=System error code, Notes=0=no error
- Column=4, Field=Status Code, Tag=SC, Data Type=Hex, Format=hhhhhhhh, Unit=-, Description=System status, Notes=8 hex digits
- Column=5, Field=Battery Voltage, Tag=BV, Data Type=Float, Format=dd.d, Unit=V, Description=Power supply, Notes=10.0-16.0V typical
- Column=6, Field=Sound Speed, Tag=SS, Data Type=Float, Format=dddd.d, Unit=m/s, Description=Measured sound speed, Notes=1400.0-1600.0 m/s
- Column=7, Field=Heading Std. Dev., Tag=HSD, Data Type=Float, Format=dd.dd, Unit=deg, Description=Heading uncertainty, Notes=0.00-99.99°
- Column=8, Field=Heading, Tag=H, Data Type=Float, Format=ddd.d, Unit=deg, Description=Compass heading, Notes=0.0-359.9°
- Column=9, Field=Pitch, Tag=PI, Data Type=Float, Format=dd.d, Unit=deg, Description=Instrument pitch, Notes=-90.0 to +90.0°
- Column=10, Field=Pitch Std. Dev., Tag=PISD, Data Type=Float, Format=dd.dd, Unit=deg, Description=Pitch uncertainty, Notes=0.00-99.99°
- Column=11, Field=Roll, Tag=R, Data Type=Float, Format=dd.d, Unit=deg, Description=Instrument roll, Notes=-90.0 to +90.0°
- Column=12, Field=Roll Std. Dev., Tag=RSD, Data Type=Float, Format=dd.dd, Unit=deg, Description=Roll uncertainty, Notes=0.00-99.99°
- Column=13, Field=Pressure, Tag=P, Data Type=Float, Format=ddd.ddd, Unit=dBar, Description=Water pressure, Notes=Depth equivalent
- Column=14, Field=Pressure Std. Dev., Tag=PSD, Data Type=Float, Format=dd.dd, Unit=dBar, Description=Pressure uncertainty, Notes=0.00-99.99 dBar
- Column=15, Field=Temperature, Tag=T, Data Type=Float, Format=dd.dd, Unit=°C, Description=Water temperature, Notes=-5.00 to +35.00°C
- Column=16, Field=Checksum, Tag=-, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Example
```
$PNORS1,083013,132455,0,34000034,22.9,1500.0,0.02,123.4,45.6,0.02,23.4,0.02,123.456,0.02,24.56*39
```

## Interpretation
- Date: August 30, 2013
- Time: 13:24:55 UTC
- Error: 0 (no errors)
- Status: 0x34000034
- Battery: 22.9 volts
- Sound speed: 1500.0 m/s
- Heading std dev: 0.02°
- Heading: 123.4°
- Pitch: 45.6°
- Pitch std dev: 0.02°
- Roll: 23.4°
- Roll std dev: 0.02°
- Pressure: 123.456 dBar
- Pressure std dev: 0.02 dBar
- Temperature: 24.56°C
- Checksum: 39

## Notes
- Used in Burst mode with DF=101
- Identical to Averaging mode PNORS1
- No tags in data fields (tagless format)
- Includes standard deviation measurements
- Error code as integer (not hex)
- Temperature with two decimal places
- Part of Burst telemetry data stream
```

**PNORC1-BURST-DF101.md**
```markdown
# PNORC1 - Averaged Current Data Format 1 (Burst Mode, DF=101)

## Description
NMEA-formatted averaged current data without tags from Burst telemetry mode (Data Format 101). Identical to Averaging mode PNORC1.

## Format
`$PNORC1,<date>,<time>,<cell_num>,<cell_pos>,<velocity_fields>,<amplitude_fields>,<correlation_fields>*<checksum>`

## Data Fields Logical Interpretation for Parser
- Column=0, Field=Identifier, Tag=-, Data Type=String, Format="$PNORC1", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Date, Tag=DATE, Data Type=Integer, Format=MMDDYY, Unit=-, Description=Measurement date, Notes=Always present
- Column=2, Field=Time, Tag=TIME, Data Type=Integer, Format=HHMMSS, Unit=-, Description=Measurement time, Notes=Always present
- Column=3, Field=Cell Number, Tag=CN, Data Type=Integer, Format=N, Unit=-, Description=Measurement cell index, Notes=Always present
- Column=4, Field=Cell Position, Tag=CP, Data Type=Float, Format=dd.d, Unit=m, Description=Distance from transducer, Notes=Always present
- Column=5, Field=Velocity 1, Tag=V1/VE/VX, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Velocity component 1, Notes=Meaning depends on CY
- Column=6, Field=Velocity 2, Tag=V2/VN/VY, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Velocity component 2, Notes=Meaning depends on CY
- Column=7, Field=Velocity 3, Tag=V3/VU/VZ, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Velocity component 3, Notes=Meaning depends on CY
- Column=8, Field=Velocity 4, Tag=V4/VU2/VZ2, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Velocity component 4, Notes=Meaning depends on CY
- Column=9, Field=Amplitude Beam 1, Tag=A1, Data Type=Float, Format=ddd.d, Unit=dB, Description=Echo amplitude beam 1, Notes=Always present
- Column=10, Field=Amplitude Beam 2, Tag=A2, Data Type=Float, Format=ddd.d, Unit=dB, Description=Echo amplitude beam 2, Notes=Always present
- Column=11, Field=Amplitude Beam 3, Tag=A3, Data Type=Float, Format=ddd.d, Unit=dB, Description=Echo amplitude beam 3, Notes=Always present
- Column=12, Field=Amplitude Beam 4, Tag=A4, Data Type=Float, Format=ddd.d, Unit=dB, Description=Echo amplitude beam 4, Notes=Always present
- Column=13, Field=Correlation Beam 1, Tag=C1, Data Type=Integer, Format=N, Unit=%, Description=Correlation beam 1, Notes=Always present
- Column=14, Field=Correlation Beam 2, Tag=C2, Data Type=Integer, Format=N, Unit=%, Description=Correlation beam 2, Notes=Always present
- Column=15, Field=Correlation Beam 3, Tag=C3, Data Type=Integer, Format=N, Unit=%, Description=Correlation beam 3, Notes=Always present
- Column=16, Field=Correlation Beam 4, Tag=C4, Data Type=Integer, Format=N, Unit=%, Description=Correlation beam 4, Notes=Always present
- Column=17, Field=Checksum, Tag=-, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present
## Data Fields Nortek Definition
- Column=0, Field=Identifier, Tag=-, Data Type=String, Format="$PNORC1", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Date, Tag=DATE, Data Type=Integer, Format=MMDDYY, Unit=-, Description=Measurement date, Notes=Always present
- Column=2, Field=Time, Tag=TIME, Data Type=Integer, Format=HHMMSS, Unit=-, Description=Measurement time, Notes=Always present
- Column=3, Field=Cell Number, Tag=CN, Data Type=Integer, Format=N, Unit=-, Description=Measurement cell index, Notes=Always present
- Column=4, Field=Cell Position, Tag=CP, Data Type=Float, Format=dd.d, Unit=m, Description=Distance from transducer, Notes=Always present
- Column=5, Field=Velocity East, Tag=VE, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=East velocity component, Notes=CY=ENU only
- Column=6, Field=Velocity North, Tag=VN, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=North velocity component, Notes=CY=ENU only
- Column=7, Field=Velocity Up, Tag=VU, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Up velocity component, Notes=CY=ENU only
- Column=8, Field=Velocity Up 2, Tag=VU2, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Second up velocity, Notes=CY=ENU only
- Column=9, Field=Velocity X, Tag=VX, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=X velocity component, Notes=CY=XYZ only
- Column=10, Field=Velocity Y, Tag=VY, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Y velocity component, Notes=CY=XYZ only
- Column=11, Field=Velocity Z, Tag=VZ, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Z velocity component, Notes=CY=XYZ only
- Column=12, Field=Velocity Z2, Tag=VZ2, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Second Z velocity, Notes=CY=XYZ only
- Column=13, Field=Velocity Beam 1, Tag=V1, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Beam 1 velocity, Notes=CY=BEAM only
- Column=14, Field=Velocity Beam 2, Tag=V2, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Beam 2 velocity, Notes=CY=BEAM only
- Column=15, Field=Velocity Beam 3, Tag=V3, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Beam 3 velocity, Notes=CY=BEAM only
- Column=16, Field=Velocity Beam 4, Tag=V4, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Beam 4 velocity, Notes=CY=BEAM only
- Column=17, Field=Amplitude Beam 1, Tag=A1, Data Type=Float, Format=ddd.d, Unit=dB, Description=Echo amplitude beam 1, Notes=Always present
- Column=18, Field=Amplitude Beam 2, Tag=A2, Data Type=Float, Format=ddd.d, Unit=dB, Description=Echo amplitude beam 2, Notes=Always present
- Column=19, Field=Amplitude Beam 3, Tag=A3, Data Type=Float, Format=ddd.d, Unit=dB, Description=Echo amplitude beam 3, Notes=Always present
- Column=20, Field=Amplitude Beam 4, Tag=A4, Data Type=Float, Format=ddd.d, Unit=dB, Description=Echo amplitude beam 4, Notes=Always present
- Column=21, Field=Correlation Beam 1, Tag=C1, Data Type=Integer, Format=N, Unit=%, Description=Correlation beam 1, Notes=Always present
- Column=22, Field=Correlation Beam 2, Tag=C2, Data Type=Integer, Format=N, Unit=%, Description=Correlation beam 2, Notes=Always present
- Column=23, Field=Correlation Beam 3, Tag=C3, Data Type=Integer, Format=N, Unit=%, Description=Correlation beam 3, Notes=Always present
- Column=24, Field=Correlation Beam 4, Tag=C4, Data Type=Integer, Format=N, Unit=%, Description=Correlation beam 4, Notes=Always present
- Column=25, Field=Checksum, Tag=-, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Coordinate System Dependencies
- CY=ENU: Velocity fields VE, VN, VU, VU2
- CY=XYZ: Velocity fields VX, VY, VZ, VZ2
- CY=BEAM: Velocity fields V1, V2, V3, V4

## Examples
**ENU Coordinate System:**
```
$PNORC1,083013,132455,3,11.0,0.332,0.332,0.332,0.332,78.9,78.9,78.9,78.9,78,78,78,78*46
```

**BEAM Coordinate System:**
```
$PNORC1,083013,132455,3,11.0,0.332,0.332,0.332,0.332,78.9,78.9,78.9,78.9,78,78,78,78*46
```

## Notes
- Used in Burst mode with DF=101
- Identical to Averaging mode PNORC1
- Velocity fields depend on coordinate system (CY parameter)
- Repeated for each measurement cell
- No tags in data fields (tagless format)
- Amplitudes in dB (not counts like DF=100)
- Three decimal places for velocities
- Cell position in meters from transducer
- Part of Burst telemetry data stream
```

**PNORI2-BURST-DF102.md**
```markdown
# PNORI2 - Information Data Format 2 (Burst Mode, DF=102)

## Description
NMEA-formatted configuration information with tags from Burst telemetry mode (Data Format 102). Identical to Averaging mode PNORI2.

## Format
`$PNORI2,IT=<instrument_type>,SN=<head_id>,NB=<num_beams>,NC=<num_cells>,BD=<blanking>,CS=<cell_size>,CY=<coord_system>*<checksum>`

## Data Fields
- Column=0, Field=Identifier, Tag=-, Data Type=String, Format="$PNORI2", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Instrument Type, Tag=IT, Data Type=Integer, Format=N, Unit=-, Description=Instrument model, Notes/Enums=0=Aquadopp, 2=Aquadopp Profiler, 4=Signature
- Column=2, Field=Head ID, Tag=SN, Data Type=Integer, Format=N, Unit=-, Description=Instrument serial number, Notes=Numeric only
- Column=3, Field=Number of Beams, Tag=NB, Data Type=Integer, Format=N, Unit=-, Description=Acoustic beams, Notes=3 or 4
- Column=4, Field=Number of Cells, Tag=NC, Data Type=Integer, Format=N, Unit=-, Description=Measurement cells, Notes=1-128
- Column=5, Field=Blanking Distance, Tag=BD, Data Type=Float, Format=dd.dd, Unit=m, Description=Distance to first cell, Notes=0.00-99.99 m
- Column=6, Field=Cell Size, Tag=CS, Data Type=Float, Format=dd.dd, Unit=m, Description=Size of each cell, Notes=0.00-99.99 m
- Column=7, Field=Coordinate System, Tag=CY, Data Type=String, Format=Text, Unit=-, Description=Velocity coordinates, Notes/Enums=ENU, XYZ, or BEAM
- Column=8, Field=Checksum, Tag=-, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Enumerations
### Instrument Type (IT)
- 0: Aquadopp
- 2: Aquadopp Profiler
- 4: Signature

### Coordinate System (CY)
- ENU: East-North-Up (geographic)
- XYZ: Instrument coordinates
- BEAM: Beam coordinates (radial)

## Example
```
$PNORI2,IT=4,SN=123456,NB=4,NC=30,BD=1.00,CS=5.00,CY=BEAM*68
```

## Interpretation
- Instrument: Signature (IT=4)
- Serial: 123456 (SN=123456)
- Beams: 4-beam system (NB=4)
- Cells: 30 measurement cells (NC=30)
- Blanking: 1.00 m to first cell (BD=1.00)
- Cell size: 5.00 m each (CS=5.00)
- Coordinates: BEAM (beam coordinates, CY=BEAM)
- Checksum: 68

## Notes
- Used in Burst mode with DF=102
- Identical to Averaging mode PNORI2
- All fields have tags (IT=, SN=, etc.)
- Self-describing format
- Easier parsing with tags
- Same data as PNORI1 but with tags
- Coordinate system as text
- Part of Burst telemetry data stream
```

**PNORS2-BURST-DF102.md**
```markdown
# PNORS2 - Sensor Data Format 2 (Burst Mode, DF=102)

## Description
NMEA-formatted sensor data with tags from Burst telemetry mode (Data Format 102). Identical to Averaging mode PNORS2.

## Format
`$PNORS2,DATE=<date>,TIME=<time>,EC=<error_code>,SC=<status_code>,BV=<battery>,SS=<sound_speed>,HSD=<heading_stddev>,H=<heading>,PI=<pitch>,PISD=<pitch_stddev>,R=<roll>,RSD=<roll_stddev>,P=<pressure>,PSD=<pressure_stddev>,T=<temperature>*<checksum>`

## Data Fields
- Column=0, Field=Identifier, Tag=-, Data Type=String, Format="$PNORS2", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Date, Tag=DATE, Data Type=Integer, Format=MMDDYY, Unit=-, Description=Measurement date, Notes=MonthDayYear
- Column=2, Field=Time, Tag=TIME, Data Type=Integer, Format=HHMMSS, Unit=-, Description=Measurement time, Notes=HourMinuteSecond
- Column=3, Field=Error Code, Tag=EC, Data Type=Integer, Format=N, Unit=-, Description=System error code, Notes=0=no error
- Column=4, Field=Status Code, Tag=SC, Data Type=Hex, Format=hhhhhhhh, Unit=-, Description=System status, Notes=8 hex digits
- Column=5, Field=Battery Voltage, Tag=BV, Data Type=Float, Format=dd.d, Unit=V, Description=Power supply, Notes=10.0-16.0V typical
- Column=6, Field=Sound Speed, Tag=SS, Data Type=Float, Format=dddd.d, Unit=m/s, Description=Measured sound speed, Notes=1400.0-1600.0 m/s
- Column=7, Field=Heading Std. Dev., Tag=HSD, Data Type=Float, Format=dd.dd, Unit=deg, Description=Heading uncertainty, Notes=0.00-99.99°
- Column=8, Field=Heading, Tag=H, Data Type=Float, Format=ddd.d, Unit=deg, Description=Compass heading, Notes=0.0-359.9°
- Column=9, Field=Pitch, Tag=PI, Data Type=Float, Format=dd.d, Unit=deg, Description=Instrument pitch, Notes=-90.0 to +90.0°
- Column=10, Field=Pitch Std. Dev., Tag=PISD, Data Type=Float, Format=dd.dd, Unit=deg, Description=Pitch uncertainty, Notes=0.00-99.99°
- Column=11, Field=Roll, Tag=R, Data Type=Float, Format=dd.d, Unit=deg, Description=Instrument roll, Notes=-90.0 to +90.0°
- Column=12, Field=Roll Std. Dev., Tag=RSD, Data Type=Float, Format=dd.dd, Unit=deg, Description=Roll uncertainty, Notes=0.00-99.99°
- Column=13, Field=Pressure, Tag=P, Data Type=Float, Format=ddd.ddd, Unit=dBar, Description=Water pressure, Notes=Depth equivalent
- Column=14, Field=Pressure Std. Dev., Tag=PSD, Data Type=Float, Format=dd.dd, Unit=dBar, Description=Pressure uncertainty, Notes=0.00-99.99 dBar
- Column=15, Field=Temperature, Tag=T, Data Type=Float, Format=dd.dd, Unit=°C, Description=Water temperature, Notes=-5.00 to +35.00°C
- Column=16, Field=Checksum, Tag=-, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Example
```
$PNORS2,DATE=083013,TIME=132455,EC=0,SC=34000034,BV=22.9,SS=1500.0,HSD=0.02,H=123.4,PI=45.6,PISD=0.02,R=23.4,RSD=0.02,P=123.456,PSD=0.02,T=24.56*3F
```

## Interpretation
- Date: August 30, 2013 (DATE=083013)
- Time: 13:24:55 UTC (TIME=132455)
- Error: 0 (EC=0)
- Status: 0x34000034 (SC=34000034)
- Battery: 22.9 volts (BV=22.9)
- Sound speed: 1500.0 m/s (SS=1500.0)
- Heading std dev: 0.02° (HSD=0.02)
- Heading: 123.4° (H=123.4)
- Pitch: 45.6° (PI=45.6)
- Pitch std dev: 0.02° (PISD=0.02)
- Roll: 23.4° (R=23.4)
- Roll std dev: 0.02° (RSD=0.02)
- Pressure: 123.456 dBar (P=123.456)
- Pressure std dev: 0.02 dBar (PSD=0.02)
- Temperature: 24.56°C (T=24.56)
- Checksum: 3F

## Notes
- Used in Burst mode with DF=102
- Identical to Averaging mode PNORS2
- All fields have tags (DATE=, TIME=, etc.)
- Self-describing format
- Easier parsing with tags
- Includes standard deviation measurements
- Same data as PNORS1 but with tags
- Part of Burst telemetry data stream
```

**PNORC2-BURST-DF102.md**
```markdown
# PNORC2 - Averaged Current Data Format 2 (Burst Mode, DF=102)

## Description
NMEA-formatted averaged current data with tags from Burst telemetry mode (Data Format 102). Identical to Averaging mode PNORC2.

## Format
`$PNORC2,DATE=<date>,TIME=<time>,CN=<cell_num>,CP=<cell_pos>,<velocity_tags>,<amplitude_tags>,<correlation_tags>*<checksum>`

## Data Fields Nortek Definition
- Column=0, Field=Identifier, Tag=-, Data Type=String, Format="$PNORC2", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Date, Tag=DATE, Data Type=Integer, Format=MMDDYY, Unit=-, Description=Measurement date, Notes=Always present
- Column=2, Field=Time, Tag=TIME, Data Type=Integer, Format=HHMMSS, Unit=-, Description=Measurement time, Notes=Always present
- Column=3, Field=Cell Number, Tag=CN, Data Type=Integer, Format=N, Unit=-, Description=Measurement cell index, Notes=Always present
- Column=4, Field=Cell Position, Tag=CP, Data Type=Float, Format=dd.d, Unit=m, Description=Distance from transducer, Notes=Always present
- Column=5, Field=Velocity East, Tag=VE, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=East velocity component, Notes=CY=ENU only
- Column=6, Field=Velocity North, Tag=VN, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=North velocity component, Notes=CY=ENU only
- Column=7, Field=Velocity Up, Tag=VU, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Up velocity component, Notes=CY=ENU only
- Column=8, Field=Velocity Up 2, Tag=VU2, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Second up velocity, Notes=CY=ENU only
- Column=9, Field=Velocity X, Tag=VX, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=X velocity component, Notes=CY=XYZ only
- Column=10, Field=Velocity Y, Tag=VY, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Y velocity component, Notes=CY=XYZ only
- Column=11, Field=Velocity Z, Tag=VZ, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Z velocity component, Notes=CY=XYZ only
- Column=12, Field=Velocity Z2, Tag=VZ2, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Second Z velocity, Notes=CY=XYZ only
- Column=13, Field=Velocity Beam 1, Tag=V1, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Beam 1 velocity, Notes=CY=BEAM only
- Column=14, Field=Velocity Beam 2, Tag=V2, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Beam 2 velocity, Notes=CY=BEAM only
- Column=15, Field=Velocity Beam 3, Tag=V3, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Beam 3 velocity, Notes=CY=BEAM only
- Column=16, Field=Velocity Beam 4, Tag=V4, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Beam 4 velocity, Notes=CY=BEAM only
- Column=17, Field=Amplitude Beam 1, Tag=A1, Data Type=Float, Format=ddd.d, Unit=dB, Description=Echo amplitude beam 1, Notes=Always present
- Column=18, Field=Amplitude Beam 2, Tag=A2, Data Type=Float, Format=ddd.d, Unit=dB, Description=Echo amplitude beam 2, Notes=Always present
- Column=19, Field=Amplitude Beam 3, Tag=A3, Data Type=Float, Format=ddd.d, Unit=dB, Description=Echo amplitude beam 3, Notes=Always present
- Column=20, Field=Amplitude Beam 4, Tag=A4, Data Type=Float, Format=ddd.d, Unit=dB, Description=Echo amplitude beam 4, Notes=Always present
- Column=21, Field=Correlation Beam 1, Tag=C1, Data Type=Integer, Format=N, Unit=%, Description=Correlation beam 1, Notes=Always present
- Column=22, Field=Correlation Beam 2, Tag=C2, Data Type=Integer, Format=N, Unit=%, Description=Correlation beam 2, Notes=Always present
- Column=23, Field=Correlation Beam 3, Tag=C3, Data Type=Integer, Format=N, Unit=%, Description=Correlation beam 3, Notes=Always present
- Column=24, Field=Correlation Beam 4, Tag=C4, Data Type=Integer, Format=N, Unit=%, Description=Correlation beam 4, Notes=Always present
- Column=25, Field=Checksum, Tag=-, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Data Fields Logical Interpretation for Parser
- Column=0, Field=Identifier, Tag=-, Data Type=String, Format="$PNORC2", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Date, Tag=DATE, Data Type=Integer, Format=MMDDYY, Unit=-, Description=Measurement date, Notes=Always present
- Column=2, Field=Time, Tag=TIME, Data Type=Integer, Format=HHMMSS, Unit=-, Description=Measurement time, Notes=Always present
- Column=3, Field=Cell Number, Tag=CN, Data Type=Integer, Format=N, Unit=-, Description=Measurement cell index, Notes=Always present
- Column=4, Field=Cell Position, Tag=CP, Data Type=Float, Format=dd.d, Unit=m, Description=Distance from transducer, Notes=Always present
- Column=5, Field=Velocity 1, Tag=V1/VE/VX, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Velocity component 1, Notes=Tag depends on CY (VE, VX, V1)
- Column=6, Field=Velocity 2, Tag=V2/VN/VY, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Velocity component 2, Notes=Tag depends on CY (VN, VY, V2)
- Column=7, Field=Velocity 3, Tag=V3/VU/VZ, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Velocity component 3, Notes=Tag depends on CY (VU, VZ, V3)
- Column=8, Field=Velocity 4, Tag=V4/VU2/VZ2, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Velocity component 4, Notes=Tag depends on CY (VU2, VZ2, V4)
- Column=9, Field=Amplitude Beam 1, Tag=A1, Data Type=Float, Format=ddd.d, Unit=dB, Description=Echo amplitude beam 1, Notes=Always present
- Column=10, Field=Amplitude Beam 2, Tag=A2, Data Type=Float, Format=ddd.d, Unit=dB, Description=Echo amplitude beam 2, Notes=Always present
- Column=11, Field=Amplitude Beam 3, Tag=A3, Data Type=Float, Format=ddd.d, Unit=dB, Description=Echo amplitude beam 3, Notes=Always present
- Column=12, Field=Amplitude Beam 4, Tag=A4, Data Type=Float, Format=ddd.d, Unit=dB, Description=Echo amplitude beam 4, Notes=Always present
- Column=13, Field=Correlation Beam 1, Tag=C1, Data Type=Integer, Format=N, Unit=%, Description=Correlation beam 1, Notes=Always present
- Column=14, Field=Correlation Beam 2, Tag=C2, Data Type=Integer, Format=N, Unit=%, Description=Correlation beam 2, Notes=Always present
- Column=15, Field=Correlation Beam 3, Tag=C3, Data Type=Integer, Format=N, Unit=%, Description=Correlation beam 3, Notes=Always present
- Column=16, Field=Correlation Beam 4, Tag=C4, Data Type=Integer, Format=N, Unit=%, Description=Correlation beam 4, Notes=Always present
- Column=17, Field=Checksum, Tag=-, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Coordinate System Dependencies
- CY=ENU: Velocity fields VE=, VN=, VU=, VU2=
- CY=XYZ: Velocity fields VX=, VY=, VZ=, VZ2=
- CY=BEAM: Velocity fields V1=, V2=, V3=, V4=

## Examples
**ENU Coordinate System:**
```
$PNORC2,DATE=083013,TIME=132455,CN=3,CP=11.0,VE=0.332,VN=0.332,VU=0.332,VU2=0.332,A1=78.9,A2=78.9,A3=78.9,A4=78.9,C1=78,C2=78,C3=78,C4=78*49
```

**BEAM Coordinate System:**
```
$PNORC2,DATE=083013,TIME=132455,CN=3,CP=11.0,V1=0.332,V2=0.332,V3=-0.332,V4=-0.332,A1=78.9,A2=78.9,A3=78.9,A4=78.9,C1=78,C2=78,C3=78,C4=78*49
```

## Notes
- Used in Burst mode with DF=102
- Identical to Averaging mode PNORC2
- All fields have tags (DATE=, TIME=, etc.)
- Velocity fields depend on coordinate system (CY parameter)
- Self-describing format
- Easier parsing with tags
- Repeated for each measurement cell
- Amplitudes in dB
- Three decimal places for velocities
- Part of Burst telemetry data stream
```

**PNORH3-BURST-DF103.md**
```markdown
# PNORH3 - Header Data Format 3 (Burst Mode, DF=103)

## Description
NMEA-formatted header data with tags from Burst telemetry mode (Data Format 103). Identical to Averaging mode PNORH3.

## Format
`$PNORH3,DATE=<date>,TIME=<time>,EC=<error_code>,SC=<status_code>*<checksum>`

## Data Fields
- Column=0, Field=Identifier, Tag=-, Data Type=String, Format="$PNORH3", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Date, Tag=DATE, Data Type=Integer, Format=YYMMDD, Unit=-, Description=Measurement date, Notes=YearMonthDay
- Column=2, Field=Time, Tag=TIME, Data Type=Integer, Format=HHMMSS, Unit=-, Description=Measurement time, Notes=HourMinuteSecond
- Column=3, Field=Error Code, Tag=EC, Data Type=Integer, Format=N, Unit=-, Description=System error code, Notes=0=no error
- Column=4, Field=Status Code, Tag=SC, Data Type=Hex, Format=hhhhhhhh, Unit=-, Description=System status, Notes=8 hex digits
- Column=5, Field=Checksum, Tag=-, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Example
```
$PNORH3,DATE=141112,TIME=081946,EC=0,SC=2A4C0000*5F
```

## Interpretation
- Date: November 14, 2012 (DATE=141112)
- Time: 08:19:46 UTC (TIME=081946)
- Error: 0 (EC=0)
- Status: 0x2A4C0000 (SC=2A4C0000)
- Checksum: 5F

## Notes
- Used in Burst mode with DF=103
- Identical to Averaging mode PNORH3
- Simplified header format
- Date format: YYMMDD (different from MMDDYY in DF=101/102)
- All fields have tags
- No instrument configuration data
- Status code as 8-character hex
- Part of Burst telemetry data stream
```

**PNORS3-BURST-DF103.md**
```markdown
# PNORS3 - Sensor Data Format 3 (Burst Mode, DF=103)

## Description
NMEA-formatted sensor data with tags from Burst telemetry mode (Data Format 103). Identical to Averaging mode PNORS3.

## Format
`$PNORS3,BV=<battery>,SS=<sound_speed>,H=<heading>,PI=<pitch>,R=<roll>,P=<pressure>,T=<temperature>*<checksum>`

## Data Fields
- Column=0, Field=Identifier, Tag=-, Data Type=String, Format="$PNORS3", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Battery Voltage, Tag=BV, Data Type=Float, Format=dd.d, Unit=V, Description=Power supply, Notes=10.0-16.0V typical
- Column=2, Field=Sound Speed, Tag=SS, Data Type=Float, Format=dddd.d, Unit=m/s, Description=Measured sound speed, Notes=1400.0-1600.0 m/s
- Column=3, Field=Heading, Tag=H, Data Type=Float, Format=ddd.d, Unit=deg, Description=Compass heading, Notes=0.0-359.9°
- Column=4, Field=Pitch, Tag=PI, Data Type=Float, Format=dd.d, Unit=deg, Description=Instrument pitch, Notes=-90.0 to +90.0°
- Column=5, Field=Roll, Tag=R, Data Type=Float, Format=dd.d, Unit=deg, Description=Instrument roll, Notes=-90.0 to +90.0°
- Column=6, Field=Pressure, Tag=P, Data Type=Float, Format=ddd.ddd, Unit=dBar, Description=Water pressure, Notes=Depth equivalent
- Column=7, Field=Temperature, Tag=T, Data Type=Float, Format=dd.dd, Unit=°C, Description=Water temperature, Notes=-5.00 to +35.00°C
- Column=8, Field=Checksum, Tag=-, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Example
```
$PNORS3,BV=22.9,SS=1546.1,H=151.1,PI=-12.0,R=-5.2,P=705.669,T=24.96*7A
```

## Interpretation
- Battery: 22.9 volts (BV=22.9)
- Sound speed: 1546.1 m/s (SS=1546.1)
- Heading: 151.1° (H=151.1)
- Pitch: -12.0° (PI=-12.0, tilted backward)
- Roll: -5.2° (R=-5.2, tilted left)
- Pressure: 705.669 dBar (P=705.669, ~700 m depth)
- Temperature: 24.96°C (T=24.96)
- Checksum: 7A

## Notes
- Used in Burst mode with DF=103
- Identical to Averaging mode PNORS3
- Simplified sensor data format
- No date/time (in header PNORH3)
- No error/status codes (in header PNORH3)
- No standard deviation measurements
- All fields have tags
- Temperature with two decimal places
- Part of Burst telemetry data stream
```

**PNORC3-BURST-DF103.md**
```markdown
# PNORC3 - Averaged Current Data Format 3 (Burst Mode, DF=103)

## Description
NMEA-formatted averaged current data with tags from Burst telemetry mode (Data Format 103). Identical to Averaging mode PNORC3.

## Format
`$PNORC3,CP=<cell_position>,SP=<speed>,DIR=<direction>,AC=<avg_correlation>,AA=<avg_amplitude>*<checksum>`

## Data Fields
- Column=0, Field=Identifier, Tag=-, Data Type=String, Format="$PNORC3", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Cell Position, Tag=CP, Data Type=Float, Format=dd.d, Unit=m, Description=Distance from transducer, Notes=Always present
- Column=2, Field=Speed, Tag=SP, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Current speed magnitude, Notes=0.000-99.999 m/s
- Column=3, Field=Direction, Tag=DIR, Data Type=Float, Format=ddd.d, Unit=deg, Description=Current direction, Notes=0.0-359.9°
- Column=4, Field=Averaged Correlation, Tag=AC, Data Type=Integer, Format=N, Unit=-, Description=Average correlation, Notes=0-100 typically
- Column=5, Field=Averaged Amplitude, Tag=AA, Data Type=Integer, Format=N, Unit=-, Description=Average amplitude, Notes=0-255 typically
- Column=6, Field=Checksum, Tag=-, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Example
```
$PNORC3,CP=4.5,SP=3.519,DIR=110.9,AC=6,AA=28*3B
```

## Interpretation
- Cell position: 4.5 m from transducer (CP=4.5)
- Speed: 3.519 m/s (SP=3.519)
- Direction: 110.9° (DIR=110.9, ESE)
- Average correlation: 6 (AC=6)
- Average amplitude: 28 (AA=28)
- Checksum: 3B

## Notes
- Used in Burst mode with DF=103
- Identical to Averaging mode PNORC3
- Simplified current data format
- No beam-specific velocities (only speed/direction)
- No individual beam amplitudes/correlations (only averages)
- All fields have tags
- Repeated for each measurement cell
- Direction follows oceanographic convention (coming from)
- Speed with three decimal places
- Part of Burst telemetry data stream
```

**PNORH4-BURST-DF104.md**
```markdown
# PNORH4 - Header Data Format 4 (Burst Mode, DF=104)

## Description
NMEA-formatted header data without tags from Burst telemetry mode (Data Format 104). Identical to Averaging mode PNORH4.

## Format
`$PNORH4,<date>,<time>,<error_code>,<status_code>*<checksum>`

## Data Fields
- Column=0, Field=Identifier, Tag=-, Data Type=String, Format="$PNORH4", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Date, Tag=DATE, Data Type=Integer, Format=YYMMDD, Unit=-, Description=Measurement date, Notes=YearMonthDay
- Column=2, Field=Time, Tag=TIME, Data Type=Integer, Format=HHMMSS, Unit=-, Description=Measurement time, Notes=HourMinuteSecond
- Column=3, Field=Error Code, Tag=EC, Data Type=Integer, Format=N, Unit=-, Description=System error code, Notes=0=no error
- Column=4, Field=Status Code, Tag=SC, Data Type=Hex, Format=hhhhhhhh, Unit=-, Description=System status, Notes=8 hex digits
- Column=5, Field=Checksum, Tag=-, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Example
```
$PNORH4,141112,083149,0,2A4C0000*4A68
```

## Interpretation
- Date: November 14, 2012 (141112)
- Time: 08:31:49 UTC (083149)
- Error: 0 (no error)
- Status: 0x2A4C0000 (2A4C0000)
- Checksum: 4A68

## Notes
- Used in Burst mode with DF=104
- Identical to Averaging mode PNORH4
- Simplified header format
- No tags in data fields
- Date format: YYMMDD (different from MMDDYY in DF=101/102)
- Same data as PNORH3 but without tags
- Checksum may include more characters
- Part of Burst telemetry data stream
```

**PNORS4-BURST-DF104.md**
```markdown
# PNORS4 - Sensor Data Format 4 (Burst Mode, DF=104)

## Description
NMEA-formatted sensor data without tags from Burst telemetry mode (Data Format 104). Identical to Averaging mode PNORS4.

## Format
`$PNORS4,<battery>,<sound_speed>,<heading>,<pitch>,<roll>,<pressure>,<temperature>*<checksum>`

## Data Fields
- Column=0, Field=Identifier, Tag=-, Data Type=String, Format="$PNORS4", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Battery Voltage, Tag=BV, Data Type=Float, Format=dd.d, Unit=V, Description=Power supply, Notes=10.0-16.0V typical
- Column=2, Field=Sound Speed, Tag=SS, Data Type=Float, Format=dddd.d, Unit=m/s, Description=Measured sound speed, Notes=1400.0-1600.0 m/s
- Column=3, Field=Heading, Tag=H, Data Type=Float, Format=ddd.d, Unit=deg, Description=Compass heading, Notes=0.0-359.9°
- Column=4, Field=Pitch, Tag=PI, Data Type=Float, Format=dd.d, Unit=deg, Description=Instrument pitch, Notes=-90.0 to +90.0°
- Column=5, Field=Roll, Tag=R, Data Type=Float, Format=dd.d, Unit=deg, Description=Instrument roll, Notes=-90.0 to +90.0°
- Column=6, Field=Pressure, Tag=P, Data Type=Float, Format=ddd.ddd, Unit=dBar, Description=Water pressure, Notes=Depth equivalent
- Column=7, Field=Temperature, Tag=T, Data Type=Float, Format=dd.dd, Unit=°C, Description=Water temperature, Notes=-5.00 to +35.00°C
- Column=8, Field=Checksum, Tag=-, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Example
```
$PNORS4,22.9,1546.1,151.2,-11.9,-5.3,705.658,24.95*5A
```

## Interpretation
- Battery: 22.9 volts
- Sound speed: 1546.1 m/s
- Heading: 151.2°
- Pitch: -11.9° (tilted backward)
- Roll: -5.3° (tilted left)
- Pressure: 705.658 dBar (~700 m depth)
- Temperature: 24.95°C
- Checksum: 5A

## Notes
- Used in Burst mode with DF=104
- Identical to Averaging mode PNORS4
- Simplified sensor data format
- No tags in data fields
- No date/time (in header PNORH4)
- No error/status codes (in header PNORH4)
- No standard deviation measurements
- Same data as PNORS3 but without tags
- Part of Burst telemetry data stream
```

**PNORC4-BURST-DF104.md**
```markdown
# PNORC4 - Averaged Current Data Format 4 (Burst Mode, DF=104)

## Description
NMEA-formatted averaged current data without tags from Burst telemetry mode (Data Format 104). Identical to Averaging mode PNORC4.

## Format
`$PNORC4,<cell_position>,<speed>,<direction>,<avg_correlation>,<avg_amplitude>*<checksum>`

## Data Fields
- Column=0, Field=Identifier, Tag=-, Data Type=String, Format="$PNORC4", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Cell Position, Tag=CP, Data Type=Float, Format=dd.d, Unit=m, Description=Distance from transducer, Notes=Always present
- Column=2, Field=Speed, Tag=SP, Data Type=Float, Format=dd.ddd, Unit=m/s, Description=Current speed magnitude, Notes=0.000-99.999 m/s
- Column=3, Field=Direction, Tag=DIR, Data Type=Float, Format=ddd.d, Unit=deg, Description=Current direction, Notes=0.0-359.9°
- Column=4, Field=Averaged Correlation, Tag=AC, Data Type=Integer, Format=N, Unit=-, Description=Average correlation, Notes=0-100 typically
- Column=5, Field=Averaged Amplitude, Tag=AA, Data Type=Integer, Format=N, Unit=-, Description=Average amplitude, Notes=0-255 typically
- Column=6, Field=Checksum, Tag=-, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

## Example
```
$PNORC4,27.5,1.815,322.6,4,28*70
```

## Interpretation
- Cell position: 27.5 m from transducer
- Speed: 1.815 m/s
- Direction: 322.6° (NW)
- Average correlation: 4
- Average amplitude: 28
- Checksum: 70

## Notes
- Used in Burst mode with DF=104
- Identical to Averaging mode PNORC4
- Simplified current data format
- No tags in data fields
- No beam-specific velocities (only speed/direction)
- No individual beam amplitudes/correlations (only averages)
- Same data as PNORC3 but without tags
- Repeated for each measurement cell
- Direction follows oceanographic convention (coming from)
- Part of Burst telemetry data stream
```

**README.md**
```markdown
# AD2CP NMEA Telemetry Data Formats Documentation

## Overview
This documentation provides comprehensive specifications for all NMEA telemetry data formats supported by Nortek AD2CP instruments. Each message type is documented in a separate file for easy reference and integration.

## Documentation Structure
- **Master Index**: Overview of all message types and their relationships
- **Individual Message Files**: Detailed specifications for each NMEA sentence type
- **Common Notes**: Shared information applicable across multiple formats

## Key Features
- Complete coverage of all NMEA telemetry formats (DF=100, 101, 102, 103, 104, 200, 201, 501)
- Clear field-by-field specifications without tables
- Examples from the official Nortek documentation
- Enumerations and valid value ranges
- Coordinate system dependencies
- Invalid data indicators
- Checksum calculation details

## How to Use This Documentation
1. Start with the Master Index to find the relevant message type
2. Navigate to the specific message file for detailed specifications
3. Refer to Common Notes for shared concepts and conventions
4. Use the examples to validate your parsing implementation

## Integration Notes
- All NMEA sentences start with `$` and end with `*<checksum>`
- Checksum is XOR of characters between `$` and `*`
- Invalid data typically marked with -9.00, -999, or empty fields
- Coordinate systems affect which velocity fields are included
- Date/time formats vary between message types

## Quick Start
For current measurements:
- DF=100: PNORI, PNORS, PNORC (legacy format)
- DF=101/102: PNORI1/2, PNORS1/2, PNORC1/2 (modern format without/with tags)
- DF=103/104: PNORH3/4, PNORS3/4, PNORC3/4 (simplified format without/with tags)

For altimeter measurements:
- DF=200: PNORA (without tags)
- DF=201: PNORA (with tags)

For wave measurements:
- DF=501: PNORW, PNORB, PNORE, PNORF, PNORWD


```
