"""PNORS family parsers for sensor data messages.

Implements parsers for:
- PNORS: Base sensor data
- PNORS1: Sensor data with salinity
- PNORS2: Tagged sensor data
- PNORS3: Compact sensor data
- PNORS4: Minimal sensor data
"""

import re
from dataclasses import dataclass, field
from typing import Dict, Optional

from .utils import (
    validate_date_string,
    validate_time_string,
    validate_hex_string,
    validate_range,
)


def _validate_battery(battery: float) -> None:
    """Validate battery voltage (0-30V)."""
    validate_range(battery, "Battery", 0.0, 30.0)


def _validate_sound_speed(speed: float) -> None:
    """Validate speed of sound (1400-2000 m/s)."""
    validate_range(speed, "Sound speed", 1400.0, 2000.0)


def _validate_heading(heading: float) -> None:
    """Validate compass heading (0-360 degrees)."""
    # Heading is 0 <= h < 360, but validate_range is inclusive.
    # We use a custom check or adjust range.
    if not (0 <= heading < 360.0):
        raise ValueError(f"Heading out of range (0-360): {heading}")


def _validate_pitch_roll(value: float, field_name: str, range_min: float, range_max: float) -> None:
    """Validate pitch or roll values."""
    validate_range(value, field_name, range_min, range_max)


def _validate_pressure(pressure: float) -> None:
    """Validate water pressure (0-20000 dBar)."""
    validate_range(pressure, "Pressure", 0.0, 20000.0)


def _validate_temperature(temp: float) -> None:
    """Validate water temperature (-5 to +50 C)."""
    validate_range(temp, "Temperature", -5.0, 50.0)


def _validate_salinity(salinity: float) -> None:
    """Validate salinity (0-50 PSU)."""
    validate_range(salinity, "Salinity", 0.0, 50.0)


@dataclass(frozen=True)
class PNORS:
    """PNORS base sensor data message.
    Format: $PNORS,MMDDYY,HHMMSS,ErrorHex,StatusHex,Battery,SoundSpeed,Heading,Pitch,Roll,Pressure,Temperature,Analog1,Analog2*CS
    """
    date: str
    time: str
    error_code: str
    status_code: str
    battery: float
    sound_speed: float
    heading: float
    pitch: float
    roll: float
    pressure: float
    temperature: float
    analog1: int
    analog2: int
    checksum: Optional[str] = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_string(self.date)
        validate_time_string(self.time)
        validate_hex_string(self.error_code)
        validate_hex_string(self.status_code)
        _validate_battery(self.battery)
        _validate_sound_speed(self.sound_speed)
        _validate_heading(self.heading)
        _validate_pitch_roll(self.pitch, "Pitch", -90, 90)
        _validate_pitch_roll(self.roll, "Roll", -180, 180)
        _validate_pressure(self.pressure)
        _validate_temperature(self.temperature)

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORS":
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()
        
        fields = [f.strip() for f in data_part.split(",")]
        if len(fields) != 14:
            raise ValueError(f"Expected 14 fields for PNORS, got {len(fields)}")
        if fields[0] != "$PNORS":
            raise ValueError(f"Invalid prefix: {fields[0]}")
            
        return cls(
            date=fields[1],
            time=fields[2],
            error_code=fields[3],
            status_code=fields[4],
            battery=float(fields[5]),
            sound_speed=float(fields[6]),
            heading=float(fields[7]),
            pitch=float(fields[8]),
            roll=float(fields[9]),
            pressure=float(fields[10]),
            temperature=float(fields[11]),
            analog1=int(fields[12]),
            analog2=int(fields[13]),
            checksum=checksum
        )

    def to_dict(self) -> Dict:
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
            "checksum": self.checksum
        }


@dataclass(frozen=True)
class PNORS1:
    """PNORS1 sensor data with salinity.
    Format: $PNORS1,MMDDYY,HHMMSS,ErrorHex,StatusHex,Battery,SoundSpeed,Heading,Pitch,Roll,Pressure,Temperature,Analog1,Analog2,Salinity*CS
    """
    date: str
    time: str
    error_code: str
    status_code: str
    battery: float
    sound_speed: float
    heading: float
    pitch: float
    roll: float
    pressure: float
    temperature: float
    analog1: int
    analog2: int
    salinity: float
    checksum: Optional[str] = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_string(self.date)
        validate_time_string(self.time)
        validate_hex_string(self.error_code)
        validate_hex_string(self.status_code)
        _validate_battery(self.battery)
        _validate_sound_speed(self.sound_speed)
        _validate_heading(self.heading)
        _validate_pitch_roll(self.pitch, "Pitch", -90, 90)
        _validate_pitch_roll(self.roll, "Roll", -180, 180)
        _validate_pressure(self.pressure)
        _validate_temperature(self.temperature)
        _validate_salinity(self.salinity)

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORS1":
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()
        
        fields = [f.strip() for f in data_part.split(",")]
        if len(fields) != 15:
            raise ValueError(f"Expected 15 fields for PNORS1, got {len(fields)}")
        if fields[0] != "$PNORS1":
            raise ValueError(f"Invalid prefix: {fields[0]}")
            
        return cls(
            date=fields[1],
            time=fields[2],
            error_code=fields[3],
            status_code=fields[4],
            battery=float(fields[5]),
            sound_speed=float(fields[6]),
            heading=float(fields[7]),
            pitch=float(fields[8]),
            roll=float(fields[9]),
            pressure=float(fields[10]),
            temperature=float(fields[11]),
            analog1=int(fields[12]),
            analog2=int(fields[13]),
            salinity=float(fields[14]),
            checksum=checksum
        )

    def to_dict(self) -> Dict:
        return {
            "sentence_type": "PNORS1",
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
            "salinity": self.salinity,
            "checksum": self.checksum
        }


class PNORS2Tag:
    """Tags for PNORS2 (Tagged sensor data)."""
    DATE = "DT"
    TIME = "TM"
    ERROR = "ER"
    STATUS = "ST"
    BATTERY = "BT"
    SOUND_SPEED = "SS"
    HEADING = "HD"
    PITCH = "PT"
    ROLL = "RL"
    PRESSURE = "PR"
    TEMPERATURE = "TP"
    ANALOG1 = "A1"
    ANALOG2 = "A2"
    
    REQUIRED_TAGS = {DATE, TIME, ERROR, STATUS, BATTERY, SOUND_SPEED, HEADING, PITCH, ROLL, PRESSURE, TEMPERATURE, ANALOG1, ANALOG2}

    @classmethod
    def parse_tagged_field(cls, field_str: str) -> tuple[str, str]:
        if "=" not in field_str:
            raise ValueError(f"Tagged field must contain '=': {field_str}")
        tag, value = field_str.split("=", 1)
        return tag.strip().upper(), value.strip()


@dataclass(frozen=True)
class PNORS2:
    """PNORS2 tagged sensor data message.
    Format: $PNORS2,DT=MMDDYY,TM=HHMMSS,ER=ErrorHex,ST=StatusHex,BT=Battery,SS=SoundSpeed,HD=Heading,PT=Pitch,RL=Roll,PR=Pressure,TP=Temperature,A1=Analog1,A2=Analog2*CS
    """
    date: str
    time: str
    error_code: str
    status_code: str
    battery: float
    sound_speed: float
    heading: float
    pitch: float
    roll: float
    pressure: float
    temperature: float
    analog1: int
    analog2: int
    checksum: Optional[str] = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_string(self.date)
        validate_time_string(self.time)
        validate_hex_string(self.error_code)
        validate_hex_string(self.status_code)
        _validate_battery(self.battery)
        _validate_sound_speed(self.sound_speed)
        _validate_heading(self.heading)
        _validate_pitch_roll(self.pitch, "Pitch", -90, 90)
        _validate_pitch_roll(self.roll, "Roll", -180, 180)
        _validate_pressure(self.pressure)
        _validate_temperature(self.temperature)

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORS2":
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()
        
        fields = [f.strip() for f in data_part.split(",")]
        if len(fields) < 14:
            raise ValueError(f"Expected at least 14 fields for PNORS2, got {len(fields)}")
        if fields[0] != "$PNORS2":
            raise ValueError(f"Invalid prefix: {fields[0]}")
            
        data = {}
        for field_str in fields[1:]:
            tag, val = PNORS2Tag.parse_tagged_field(field_str)
            if tag in data:
                raise ValueError(f"Duplicate tag in PNORS2: {tag}")
            data[tag] = val
            
        if set(data.keys()) != PNORS2Tag.REQUIRED_TAGS:
            missing = PNORS2Tag.REQUIRED_TAGS - set(data.keys())
            extra = set(data.keys()) - PNORS2Tag.REQUIRED_TAGS
            if missing:
                raise ValueError(f"Missing required tags in PNORS2: {missing}")
            if extra:
                raise ValueError(f"Unknown tags in PNORS2: {extra}")
            
        return cls(
            date=data[PNORS2Tag.DATE],
            time=data[PNORS2Tag.TIME],
            error_code=data[PNORS2Tag.ERROR],
            status_code=data[PNORS2Tag.STATUS],
            battery=float(data[PNORS2Tag.BATTERY]),
            sound_speed=float(data[PNORS2Tag.SOUND_SPEED]),
            heading=float(data[PNORS2Tag.HEADING]),
            pitch=float(data[PNORS2Tag.PITCH]),
            roll=float(data[PNORS2Tag.ROLL]),
            pressure=float(data[PNORS2Tag.PRESSURE]),
            temperature=float(data[PNORS2Tag.TEMPERATURE]),
            analog1=int(data[PNORS2Tag.ANALOG1]),
            analog2=int(data[PNORS2Tag.ANALOG2]),
            checksum=checksum
        )

    def to_dict(self) -> Dict:
        return {
            "sentence_type": "PNORS2",
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
            "checksum": self.checksum
        }


@dataclass(frozen=True)
class PNORS3:
    """PNORS3 compact sensor data.
    Format: $PNORS3,MMDDYY,HHMMSS,Battery,Heading,Pitch,Roll,Pressure,Temperature*CS
    """
    date: str
    time: str
    battery: float
    heading: float
    pitch: float
    roll: float
    pressure: float
    temperature: float
    checksum: Optional[str] = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_string(self.date)
        validate_time_string(self.time)
        _validate_battery(self.battery)
        _validate_heading(self.heading)
        _validate_pitch_roll(self.pitch, "Pitch", -90, 90)
        _validate_pitch_roll(self.roll, "Roll", -180, 180)
        _validate_pressure(self.pressure)
        _validate_temperature(self.temperature)

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORS3":
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()
        
        fields = [f.strip() for f in data_part.split(",")]
        if len(fields) != 9:
            raise ValueError(f"Expected 9 fields for PNORS3, got {len(fields)}")
        if fields[0] != "$PNORS3":
            raise ValueError(f"Invalid prefix: {fields[0]}")
            
        return cls(
            date=fields[1],
            time=fields[2],
            battery=float(fields[3]),
            heading=float(fields[4]),
            pitch=float(fields[5]),
            roll=float(fields[6]),
            pressure=float(fields[7]),
            temperature=float(fields[8]),
            checksum=checksum
        )

    def to_dict(self) -> Dict:
        return {
            "sentence_type": "PNORS3",
            "date": self.date,
            "time": self.time,
            "battery": self.battery,
            "heading": self.heading,
            "pitch": self.pitch,
            "roll": self.roll,
            "pressure": self.pressure,
            "temperature": self.temperature,
            "checksum": self.checksum
        }


@dataclass(frozen=True)
class PNORS4:
    """PNORS4 minimal sensor data.
    Format: $PNORS4,MMDDYY,HHMMSS,Heading,Pressure,Temperature*CS
    """
    date: str
    time: str
    heading: float
    pressure: float
    temperature: float
    checksum: Optional[str] = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_string(self.date)
        validate_time_string(self.time)
        _validate_heading(self.heading)
        _validate_pressure(self.pressure)
        _validate_temperature(self.temperature)

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORS4":
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()
        
        fields = [f.strip() for f in data_part.split(",")]
        if len(fields) != 6:
            raise ValueError(f"Expected 6 fields for PNORS4, got {len(fields)}")
        if fields[0] != "$PNORS4":
            raise ValueError(f"Invalid prefix: {fields[0]}")
            
        return cls(
            date=fields[1],
            time=fields[2],
            heading=float(fields[3]),
            pressure=float(fields[4]),
            temperature=float(fields[5]),
            checksum=checksum
        )

    def to_dict(self) -> Dict:
        return {
            "sentence_type": "PNORS4",
            "date": self.date,
            "time": self.time,
            "heading": self.heading,
            "pressure": self.pressure,
            "temperature": self.temperature,
            "checksum": self.checksum
        }
