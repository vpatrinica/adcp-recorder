[🏠 Home](../README.md) > [NMEA Protocol](overview.md)

# Data Validation Rules

The ADCP Recorder enforces multiple levels of validation to ensure data quality and integrity.

## Invalid Data Markers

### -9 Variants

Data values containing `-9` variants indicate invalid or unavailable measurements:

- `-9`
- `-9.0`
- `-9.00`
- `-999`
- `-9999`

**Examples**:
```
$PNORS,102115,090715,00000000,2A480000,14.4,1523.0,-9.0,15.7,2.3,0.000,22.45,0,0*XX
                                                     └─ Invalid heading
```

### Handling Invalid Data

**Option 1: Store as NULL**
```python
def parse_float_or_null(value: str) -> Optional[float]:
    """Parse float, treating -9 variants as NULL."""
    try:
        f = float(value)
        if f <= -9:  # -9, -9.0, -999, etc.
            return None
        return f
    except ValueError:
        return None
```

**Option 2: Store with invalid flag**
```python
@dataclass
class SensorReading:
    value: float
    is_valid: bool
    
    @classmethod
    def parse(cls, value_str: str):
        value = float(value_str)
        is_valid = value > -9
        return cls(value, is_valid)
```

## Field Validation

### Range Constraints

Each field type has expected value ranges:

#### Temperature
```python
MIN_TEMP = -5.0   # degrees Celsius
MAX_TEMP = 50.0   # degrees Celsius

def validate_temperature(temp: float) -> bool:
    return MIN_TEMP <= temp <= MAX_TEMP
```

#### Pressure
```python
MIN_PRESSURE = 0.0      # decibars
MAX_PRESSURE = 20000.0  # decibars (~20,000m depth)

def validate_pressure(pressure: float) -> bool:
    return MIN_PRESSURE <= pressure <= MAX_PRESSURE
```

#### Heading (Compass Bearing)
```python
MIN_HEADING = 0.0    # degrees
MAX_HEADING = 360.0  # degrees (exclusive)

def validate_heading(heading: float) -> bool:
    return MIN_HEADING <= heading < MAX_HEADING
```

#### Pitch
```python
MIN_PITCH = -90.0   # degrees
MAX_PITCH = 90.0    # degrees

def validate_pitch(pitch: float) -> bool:
    return MIN_PITCH <= pitch <= MAX_PITCH
```

#### Roll
```python
MIN_ROLL = -180.0   # degrees
MAX_ROLL = 180.0    # degrees

def validate_roll(roll: float) -> bool:
    return MIN_ROLL <= roll <= MAX_ROLL
```

#### Battery Voltage
```python
MIN_BATTERY = 0.0    # volts
MAX_BATTERY = 30.0   # volts

def validate_battery(voltage: float) -> bool:
    return MIN_BATTERY <= voltage <= MAX_BATTERY
```

#### Sound Speed
```python
MIN_SOUND_SPEED = 1400.0  # m/s (fresh water)
MAX_SOUND_SPEED = 2000.0  # m/s (theoretical max)

def validate_sound_speed(speed: float) -> bool:
    return MIN_SOUND_SPEED <= speed <= MAX_SOUND_SPEED
```

### Type Validation

Ensure values match expected types:

```python
def validate_integer(value: str, min_val: int = None, max_val: int = None) -> bool:
    """Validate integer field."""
    try:
        i = int(value)
        if min_val is not None and i < min_val:
            return False
        if max_val is not None and i > max_val:
            return False
        return True
    except ValueError:
        return False

def validate_hex_code(value: str, length: int = 8) -> bool:
    """Validate hexadecimal code."""
    if len(value) != length:
        return False
    try:
        int(value, 16)
        return True
    except ValueError:
        return False
```

### Format Validation

Validate string formats:

```python
import re

# Date: MMDDYY
DATE_PATTERN = re.compile(r'^\d{6}$')

def validate_date(date_str: str) -> bool:
    """Validate MMDDYY format."""
    if not DATE_PATTERN.match(date_str):
        return False
    try:
        month = int(date_str[0:2])
        day = int(date_str[2:4])
        year = int(date_str[4:6])
        return 1 <= month <= 12 and 1 <= day <= 31
    except ValueError:
        return False

# Time: HHMMSS
TIME_PATTERN = re.compile(r'^\d{6}$')

def validate_time(time_str: str) -> bool:
    """Validate HHMMSS format."""
    if not TIME_PATTERN.match(time_str):
        return False
    try:
        hour = int(time_str[0:2])
        minute = int(time_str[2:4])
        second = int(time_str[4:6])
        return 0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59
    except ValueError:
        return False

# Serial number / Head ID
HEAD_ID_PATTERN = re.compile(r'^[A-Za-z0-9\s]{1,30}$')

def validate_head_id(head_id: str) -> bool:
    """Validate head ID format."""
    return HEAD_ID_PATTERN.match(head_id) is not None
```

## Cross-Field Validation

### Signature Beam Constraint

Signature instruments must have exactly 4 beams:

```python
def validate_signature_beams(instrument_type: int, beam_count: int) -> bool:
    """Validate Signature instruments have 4 beams."""
    if instrument_type == 4:  # Signature
        return beam_count == 4
    return True  # Other instruments: 1-3 beams allowed
```

### Cell and Blanking Distance

Blanking distance should be less than total cell range:

```python
def validate_blanking_cell_ratio(
    blanking_distance: float,
    cell_size: float,
    cell_count: int
) -> bool:
    """Validate blanking distance is reasonable relative to cells."""
    total_range = cell_size * cell_count
    return blanking_distance < total_range
```

### Coordinate System Consistency

Coordinate system code and name must match:

```python
def validate_coord_system(code: int, name: str) -> bool:
    """Validate coordinate system code and name match."""
    mapping = {
        0: "ENU",
        1: "XYZ",
        2: "BEAM"
    }
    return mapping.get(code) == name
```

## Validation Strategy

### Multi-Level Validation

```python
def validate_sentence(sentence: dict) -> tuple[bool, list[str]]:
    """
    Validate parsed sentence at multiple levels.
    
    Returns:
        (is_valid, errors) tuple
    """
    errors = []
    
    # Level 1: Required fields present
    required_fields = ['prefix', 'timestamp', 'temperature']
    for field in required_fields:
        if field not in sentence or sentence[field] is None:
            errors.append(f"Missing required field: {field}")
    
    # Level 2: Type validation
    if 'temperature' in sentence:
        if not isinstance(sentence['temperature'], (int, float)):
            errors.append("Temperature must be numeric")
    
    # Level 3: Range validation
    if 'temperature' in sentence:
        if not validate_temperature(sentence['temperature']):
            errors.append(f"Temperature out of range: {sentence['temperature']}")
    
    # Level 4: Cross-field validation
    if 'instrument_type' in sentence and 'beam_count' in sentence:
        if not validate_signature_beams(
            sentence['instrument_type'],
            sentence['beam_count']
        ):
            errors.append("Signature instrument must have 4 beams")
    
    return len(errors) == 0, errors
```

### Validation on Parse

```python
@dataclass(frozen=True)
class PNORS:
    temperature: float
    pressure: float
    heading: float
    # ... other fields
    
    def __post_init__(self):
        """Validate fields after initialization."""
        self._validate_temperature()
        self._validate_pressure()
        self._validate_heading()
    
    def _validate_temperature(self):
        if not validate_temperature(self.temperature):
            raise ValueError(f"Invalid temperature: {self.temperature}")
    
    def _validate_pressure(self):
        if not validate_pressure(self.pressure):
            raise ValueError(f"Invalid pressure: {self.pressure}")
    
    def _validate_heading(self):
        if not validate_heading(self.heading):
            raise ValueError(f"Invalid heading: {self.heading}")
```

## DuckDB Constraints

Validation can also be enforced at the database level:

```sql
CREATE TABLE pnors_sensor_data (
    -- ...
    temperature DECIMAL(5,2) NOT NULL
        CHECK (temperature >= -5.0 AND temperature <= 50.0),
    pressure DECIMAL(7,3) NOT NULL
        CHECK (pressure >= 0.0 AND pressure <= 20000.0),
    heading DECIMAL(5,1) NOT NULL
        CHECK (heading >= 0.0 AND heading < 360.0),
    pitch DECIMAL(4,1) NOT NULL
        CHECK (pitch >= -90.0 AND pitch <= 90.0),
    roll DECIMAL(5,1) NOT NULL
        CHECK (roll >= -180.0 AND roll <= 180.0),
    battery_voltage DECIMAL(4,1) NOT NULL
        CHECK (battery_voltage >= 0.0 AND battery_voltage <= 30.0),
    sound_speed DECIMAL(6,1) NOT NULL
        CHECK (sound_speed >= 1400.0 AND sound_speed <= 2000.0)
);
```

## Error Reporting

### Validation Error Structure

```python
@dataclass
class ValidationError:
    """Validation error details."""
    field_name: str
    field_value: Any
    error_type: str  # 'RANGE', 'TYPE', 'FORMAT', 'CROSS_FIELD'
    error_message: str
    severity: str  # 'WARNING', 'ERROR', 'Critical'
    
def log_validation_error(error: ValidationError, sentence: str):
    """Log validation error with context."""
    log_warning(
        f"{error.severity}: {error.error_message} "
        f"(field={error.field_name}, value={error.field_value}) "
        f"in sentence: {sentence}"
    )
```

### Error Handling Strategies

**Strict Mode**: Reject sentence on any validation error
```python
if not is_valid:
    record_to_error_table(sentence, errors)
    return None
```

**Lenient Mode**: Accept sentence but flag invalid fields
```python
if not is_valid:
    log_warnings(errors)
    sentence['validation_errors'] = errors
    sentence['is_fully_valid'] = False
return sentence
```

## Related Documents

- [NMEA Overview](overview.md)
- [Checksum Calculation](checksum.md)
- [Python Validation Implementation](../implementation/python/validation.md)
- [DuckDB Constraints](../implementation/duckdb/constraints.md)

---

[⬆️ Back to NMEA Protocol](overview.md) | [🏠 Home](../README.md)
