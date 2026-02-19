"""PNORS family parsers for sensor data messages.

Implements parsers for:
- PNORS: Base sensor data (DF=100)
- PNORS1: Sensor data with uncertainty (DF=101)
- PNORS2: Tagged sensor data with uncertainty (DF=102)
- PNORS3: Tagged sensor data (DF=103)
- PNORS4: Minimal sensor data (DF=104)
"""

from dataclasses import dataclass, field
from typing import Any

from .utils import (
    parse_nmea_sentence,
    parse_optional_float,
    parse_optional_int,
    parse_tagged_field,
    validate_date_mm_dd_yy,
    validate_hex_string,
    validate_range,
    validate_time_string,
)


def _validate_battery(battery: float | None) -> bool:
    """Validate battery voltage (0-30V). Returns True if valid."""
    if battery is not None:
        return validate_range(battery, "Battery", 0.0, 30.0)
    return True


def _validate_sound_speed(speed: float | None) -> bool:
    """Validate speed of sound (1400-2000 m/s). Returns True if valid."""
    if speed is not None:
        return validate_range(speed, "Sound speed", 1400.0, 2000.0)
    return True


def _validate_heading(heading: float | None) -> bool:
    """Validate compass heading (0-360 degrees). Returns True if valid."""
    if heading is not None:
        if not (0 <= heading < 360.0):
            if heading != 360.0:
                return False
    return True


def _validate_pitch_roll(value: float | None, field_name: str) -> bool:
    """Validate pitch or roll values. Returns True if valid."""
    if value is not None:
        return validate_range(value, field_name, -999.99, 999.99)
    return True


def _validate_pressure(pressure: float | None) -> bool:
    """Validate water pressure (0-20000 dBar). Returns True if valid."""
    if pressure is not None:
        return validate_range(pressure, "Pressure", 0.0, 20000.0)
    return True


def _validate_temperature(temp: float | None) -> bool:
    """Validate water temperature (-5 to +50 C). Returns True if valid."""
    if temp is not None:
        return validate_range(temp, "Temperature", -5.0, 50.0)
    return True


@dataclass(frozen=True)
class PNORS:
    """PNORS base sensor data message (DF=100).
    Format: $PNORS,MMDDYY,HHMMSS,Error,Status,Battery,SoundSpeed,Heading,
            Pitch,Roll,Pressure,Temperature,Analog1,Analog2*CS
    """

    date: str
    time: str
    error_code: str
    status_code: str
    battery: float | None
    sound_speed: float | None
    heading: float | None
    pitch: float | None
    roll: float | None
    pressure: float | None
    temperature: float | None
    analog1: int | None
    analog2: int | None
    is_valid: bool = True
    checksum: str | None = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_mm_dd_yy(self.date)
        validate_time_string(self.time)
        validate_hex_string(self.error_code, 1, 8)
        validate_hex_string(self.status_code, 8, 8)
        _validate_battery(self.battery)
        _validate_sound_speed(self.sound_speed)
        _validate_heading(self.heading)
        _validate_pitch_roll(self.pitch, "Pitch")
        _validate_pitch_roll(self.roll, "Roll")
        _validate_pressure(self.pressure)
        _validate_temperature(self.temperature)

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORS":
        fields, checksum = parse_nmea_sentence(sentence)
        if len(fields) != 14:
            raise ValueError(f"Expected 14 fields for PNORS, got {len(fields)}")
        if fields[0] != "$PNORS":
            raise ValueError(f"Invalid prefix: {fields[0]}")

        _p = "PNORS"
        return cls(
            date=fields[1],
            time=fields[2],
            error_code=fields[3],
            status_code=fields[4],
            battery=parse_optional_float(fields[5]),
            sound_speed=parse_optional_float(fields[6]),
            heading=parse_optional_float(fields[7]),
            pitch=parse_optional_float(fields[8]),
            roll=parse_optional_float(fields[9]),
            pressure=parse_optional_float(fields[10]),
            temperature=parse_optional_float(fields[11]),
            analog1=parse_optional_int(fields[12]),
            analog2=parse_optional_int(fields[13]),
            is_valid=True,
            checksum=checksum,
        )

    def to_dict(self) -> dict:
        return {
            "sentence_type": "PNORS",
            "date": self.date,
            "time": self.time,
            "error_code": self.error_code,
            "status_code": self.status_code,
            "battery": self.battery,
            "sound_speed": self.sound_speed,
            "heading": self.heading,
            "pitch": self.pitch,
            "roll": self.roll,
            "pressure": self.pressure,
            "temperature": self.temperature,
            "analog1": self.analog1,
            "analog2": self.analog2,
            "is_valid": self.is_valid,
            "checksum": self.checksum,
        }


@dataclass(frozen=True)
class PNORS1:
    """PNORS1 sensor data with uncertainty (DF=101).
    Format: $PNORS1,Date,Time,ErrorCode,StatusCode,Battery,SoundSpeed,
            HeadingSD,Heading,Pitch,PitchSD,Roll,RollSD,Pressure,
            PressureSD,Temperature*CS
    """

    date: str
    time: str
    error_code: int | None  # EC is integer in DF=101
    status_code: str  # SC is hex in DF=101
    battery: float | None
    sound_speed: float | None
    heading_std_dev: float | None
    heading: float | None
    pitch: float | None
    pitch_std_dev: float | None
    roll: float | None
    roll_std_dev: float | None
    pressure: float | None
    pressure_std_dev: float | None
    temperature: float | None
    is_valid: bool = True
    checksum: str | None = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_mm_dd_yy(self.date)
        validate_time_string(self.time)
        validate_hex_string(self.status_code, 8, 8)
        _validate_battery(self.battery)
        _validate_sound_speed(self.sound_speed)
        _validate_heading(self.heading)
        _validate_pitch_roll(self.pitch, "Pitch")
        _validate_pitch_roll(self.roll, "Roll")
        _validate_pressure(self.pressure)
        _validate_temperature(self.temperature)

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORS1":
        fields, checksum = parse_nmea_sentence(sentence)
        if len(fields) != 16:
            raise ValueError(f"Expected 16 fields for PNORS1, got {len(fields)}")
        if fields[0] != "$PNORS1":
            raise ValueError(f"Invalid prefix: {fields[0]}")

        _p = "PNORS1"
        return cls(
            date=fields[1],
            time=fields[2],
            error_code=parse_optional_int(fields[3]),
            status_code=fields[4],
            battery=parse_optional_float(fields[5]),
            sound_speed=parse_optional_float(fields[6]),
            heading_std_dev=parse_optional_float(fields[7]),
            heading=parse_optional_float(fields[8]),
            pitch=parse_optional_float(fields[9]),
            pitch_std_dev=parse_optional_float(fields[10]),
            roll=parse_optional_float(fields[11]),
            roll_std_dev=parse_optional_float(fields[12]),
            pressure=parse_optional_float(fields[13]),
            pressure_std_dev=parse_optional_float(fields[14]),
            temperature=parse_optional_float(fields[15]),
            is_valid=True,
            checksum=checksum,
        )

    def to_dict(self) -> dict:
        return {
            "sentence_type": "PNORS1",
            "date": self.date,
            "time": self.time,
            "error_code": self.error_code,
            "status_code": self.status_code,
            "battery": self.battery,
            "sound_speed": self.sound_speed,
            "heading_std_dev": self.heading_std_dev,
            "heading": self.heading,
            "pitch": self.pitch,
            "pitch_std_dev": self.pitch_std_dev,
            "roll": self.roll,
            "roll_std_dev": self.roll_std_dev,
            "pressure": self.pressure,
            "pressure_std_dev": self.pressure_std_dev,
            "temperature": self.temperature,
            "is_valid": self.is_valid,
            "checksum": self.checksum,
        }


@dataclass(frozen=True)
class PNORS2:
    """PNORS2 tagged sensor data with uncertainty (DF=102).
    Format: $PNORS2,DATE=MMDDYY,TIME=HHMMSS,EC=Error,SC=Status,BV=Battery,
            SS=SoundSpeed,HSD=HeadingSD,H=Heading,PI=Pitch,PISD=PitchSD,
            R=Roll,RSD=RollSD,P=Pressure,PSD=PressureSD,T=Temperature*CS
    """

    date: str
    time: str
    error_code: int | None
    status_code: str
    battery: float | None
    sound_speed: float | None
    heading_std_dev: float | None
    heading: float | None
    pitch: float | None
    pitch_std_dev: float | None
    roll: float | None
    roll_std_dev: float | None
    pressure: float | None
    pressure_std_dev: float | None
    temperature: float | None
    is_valid: bool = True
    checksum: str | None = field(default=None, repr=False)

    TAG_IDS = {
        "DATE": "date",
        "TIME": "time",
        "EC": "error_code",
        "SC": "status_code",
        "BV": "battery",
        "SS": "sound_speed",
        "HSD": "heading_std_dev",
        "H": "heading",
        "PI": "pitch",
        "PISD": "pitch_std_dev",
        "R": "roll",
        "RSD": "roll_std_dev",
        "P": "pressure",
        "PSD": "pressure_std_dev",
        "T": "temperature",
    }

    def __post_init__(self):
        validate_date_mm_dd_yy(self.date)
        validate_time_string(self.time)
        validate_hex_string(self.status_code, 8, 8)
        _validate_battery(self.battery)
        _validate_sound_speed(self.sound_speed)
        _validate_heading(self.heading)
        _validate_pitch_roll(self.pitch, "Pitch")
        _validate_pitch_roll(self.roll, "Roll")
        _validate_pressure(self.pressure)
        _validate_temperature(self.temperature)

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORS2":
        fields, checksum = parse_nmea_sentence(sentence)
        if fields[0] != "$PNORS2":
            raise ValueError(f"Invalid prefix: {fields[0]}")

        data: dict[str, Any] = {}
        for i in range(1, len(fields)):
            field_str = fields[i]
            tag, val = parse_tagged_field(field_str)
            if tag not in cls.TAG_IDS:
                raise ValueError(f"Unknown tag in PNORS2: {tag}")
            data[cls.TAG_IDS[tag]] = val

        # Check for absolutely mandatory stuff
        if "date" not in data or "time" not in data or "status_code" not in data:
            raise ValueError("Missing mandatory tags in PNORS2: DATE, TIME, or SC")

        # Fill missing optional fields with None
        optional_fields = {
            "error_code",
            "battery",
            "sound_speed",
            "heading_std_dev",
            "heading",
            "pitch",
            "pitch_std_dev",
            "roll",
            "roll_std_dev",
            "pressure",
            "pressure_std_dev",
            "temperature",
        }
        for k in optional_fields:
            if k not in data:
                data[k] = None

        _p = "PNORS2"
        return cls(
            date=data["date"],
            time=data["time"],
            error_code=parse_optional_int(data["error_code"]),
            status_code=data["status_code"],
            battery=parse_optional_float(data["battery"]),
            sound_speed=parse_optional_float(data["sound_speed"]),
            heading_std_dev=parse_optional_float(data["heading_std_dev"]),
            heading=parse_optional_float(data["heading"]),
            pitch=parse_optional_float(data["pitch"]),
            pitch_std_dev=parse_optional_float(data["pitch_std_dev"]),
            roll=parse_optional_float(data["roll"]),
            roll_std_dev=parse_optional_float(data["roll_std_dev"]),
            pressure=parse_optional_float(data["pressure"]),
            pressure_std_dev=parse_optional_float(data["pressure_std_dev"]),
            temperature=parse_optional_float(data["temperature"]),
            is_valid=True,
            checksum=checksum,
        )

    def to_dict(self) -> dict:
        return {
            "sentence_type": "PNORS2",
            "date": self.date,
            "time": self.time,
            "error_code": self.error_code,
            "status_code": self.status_code,
            "battery": self.battery,
            "sound_speed": self.sound_speed,
            "heading_std_dev": self.heading_std_dev,
            "heading": self.heading,
            "pitch": self.pitch,
            "pitch_std_dev": self.pitch_std_dev,
            "roll": self.roll,
            "roll_std_dev": self.roll_std_dev,
            "pressure": self.pressure,
            "pressure_std_dev": self.pressure_std_dev,
            "temperature": self.temperature,
            "is_valid": self.is_valid,
            "checksum": self.checksum,
        }


@dataclass(frozen=True)
class PNORS3:
    """PNORS3 tagged sensor data (DF=103).
    Format: $PNORS3,BV=Battery,SS=SoundSpeed,H=Heading,PI=Pitch,R=Roll,P=Pressure,T=Temperature*CS
    """

    battery: float | None
    sound_speed: float | None
    heading: float | None
    pitch: float | None
    roll: float | None
    pressure: float | None
    temperature: float | None
    is_valid: bool = True
    checksum: str | None = field(default=None, repr=False)

    TAG_IDS = {
        "BV": "battery",
        "SS": "sound_speed",
        "H": "heading",
        "PI": "pitch",
        "R": "roll",
        "P": "pressure",
        "T": "temperature",
    }

    def __post_init__(self):
        _validate_battery(self.battery)
        _validate_sound_speed(self.sound_speed)
        _validate_heading(self.heading)
        _validate_pitch_roll(self.pitch, "Pitch")
        _validate_pitch_roll(self.roll, "Roll")
        _validate_pressure(self.pressure)
        _validate_temperature(self.temperature)

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORS3":
        fields, checksum = parse_nmea_sentence(sentence)
        if fields[0] != "$PNORS3":
            raise ValueError(f"Invalid prefix: {fields[0]}")

        _p = "PNORS3"
        data: dict[str, Any] = {}
        for i in range(1, len(fields)):
            field_str = fields[i]
            tag, val = parse_tagged_field(field_str)
            if tag not in cls.TAG_IDS:
                raise ValueError(f"Unknown tag in PNORS3: {tag}")
            field_name = cls.TAG_IDS[tag]
            data[field_name] = parse_optional_float(val)

        # Fill missing with None
        for k in cls.TAG_IDS.values():
            if k not in data:
                data[k] = None

        data["is_valid"] = True
        return cls(**data, checksum=checksum)

    def to_dict(self) -> dict:
        return {
            "sentence_type": "PNORS3",
            "battery": self.battery,
            "sound_speed": self.sound_speed,
            "heading": self.heading,
            "pitch": self.pitch,
            "roll": self.roll,
            "pressure": self.pressure,
            "temperature": self.temperature,
            "is_valid": self.is_valid,
            "checksum": self.checksum,
        }


@dataclass(frozen=True)
class PNORS4:
    """PNORS4 minimal sensor data (DF=104).
    Format: $PNORS4,Battery,SoundSpeed,Heading,Pitch,Roll,Pressure,Temperature*CS
    """

    battery: float | None
    sound_speed: float | None
    heading: float | None
    pitch: float | None
    roll: float | None
    pressure: float | None
    temperature: float | None
    is_valid: bool = True
    checksum: str | None = field(default=None, repr=False)

    def __post_init__(self):
        _validate_battery(self.battery)
        _validate_sound_speed(self.sound_speed)
        _validate_heading(self.heading)
        _validate_pitch_roll(self.pitch, "Pitch")
        _validate_pitch_roll(self.roll, "Roll")
        _validate_pressure(self.pressure)
        _validate_temperature(self.temperature)

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORS4":
        fields, checksum = parse_nmea_sentence(sentence)
        if len(fields) != 8:
            raise ValueError(f"Expected 8 fields for PNORS4, got {len(fields)}")
        if fields[0] != "$PNORS4":
            raise ValueError(f"Invalid prefix: {fields[0]}")

        _p = "PNORS4"
        return cls(
            battery=parse_optional_float(fields[1]),
            sound_speed=parse_optional_float(fields[2]),
            heading=parse_optional_float(fields[3]),
            pitch=parse_optional_float(fields[4]),
            roll=parse_optional_float(fields[5]),
            pressure=parse_optional_float(fields[6]),
            temperature=parse_optional_float(fields[7]),
            is_valid=True,
            checksum=checksum,
        )

    def to_dict(self) -> dict:
        return {
            "sentence_type": "PNORS4",
            "battery": self.battery,
            "sound_speed": self.sound_speed,
            "heading": self.heading,
            "pitch": self.pitch,
            "roll": self.roll,
            "pressure": self.pressure,
            "temperature": self.temperature,
            "is_valid": self.is_valid,
            "checksum": self.checksum,
        }
