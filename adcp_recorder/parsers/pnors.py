"""PNORS family parsers for sensor data messages.

Implements parsers for:
- PNORS: Base sensor data (DF=100)
- PNORS1: Sensor data with uncertainty (DF=101)
- PNORS2: Tagged sensor data with uncertainty (DF=102)
- PNORS3: Tagged sensor data (DF=103)
- PNORS4: Minimal sensor data (DF=104)
"""

from dataclasses import dataclass, field

from .utils import (
    parse_tagged_field,
    validate_date_mm_dd_yy,
    validate_hex_string,
    validate_range,
    validate_time_string,
)


def _validate_battery(battery: float) -> None:
    """Validate battery voltage (0-30V)."""
    validate_range(battery, "Battery", 0.0, 30.0)


def _validate_sound_speed(speed: float) -> None:
    """Validate speed of sound (1400-2000 m/s)."""
    validate_range(speed, "Sound speed", 1400.0, 2000.0)


def _validate_heading(heading: float) -> None:
    """Validate compass heading (0-360 degrees)."""
    if not (0 <= heading < 360.0):
        # Allow 360.0 temporarily if it rounds, but generally it's [0, 360)
        if heading != 360.0:
            raise ValueError(f"Heading out of range [0, 360): {heading}")


def _validate_pitch_roll(value: float, field_name: str) -> None:
    """Validate pitch or roll values (-90 to +90)."""
    validate_range(value, field_name, -90.0, 90.0)


def _validate_pressure(pressure: float) -> None:
    """Validate water pressure (0-20000 dBar)."""
    validate_range(pressure, "Pressure", 0.0, 20000.0)


def _validate_temperature(temp: float) -> None:
    """Validate water temperature (-5 to +50 C)."""
    validate_range(temp, "Temperature", -5.0, 50.0)


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
    battery: float
    sound_speed: float
    heading: float
    pitch: float
    roll: float
    pressure: float
    temperature: float
    analog1: int
    analog2: int
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
    error_code: int  # EC is integer in DF=101
    status_code: str  # SC is hex in DF=101
    battery: float
    sound_speed: float
    heading_std_dev: float
    heading: float
    pitch: float
    pitch_std_dev: float
    roll: float
    roll_std_dev: float
    pressure: float
    pressure_std_dev: float
    temperature: float
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
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()

        fields = [f.strip() for f in data_part.split(",")]
        if len(fields) != 16:
            raise ValueError(f"Expected 16 fields for PNORS1, got {len(fields)}")
        if fields[0] != "$PNORS1":
            raise ValueError(f"Invalid prefix: {fields[0]}")

        return cls(
            date=fields[1],
            time=fields[2],
            error_code=int(fields[3]),
            status_code=fields[4],
            battery=float(fields[5]),
            sound_speed=float(fields[6]),
            heading_std_dev=float(fields[7]),
            heading=float(fields[8]),
            pitch=float(fields[9]),
            pitch_std_dev=float(fields[10]),
            roll=float(fields[11]),
            roll_std_dev=float(fields[12]),
            pressure=float(fields[13]),
            pressure_std_dev=float(fields[14]),
            temperature=float(fields[15]),
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
    error_code: int
    status_code: str
    battery: float
    sound_speed: float
    heading_std_dev: float
    heading: float
    pitch: float
    pitch_std_dev: float
    roll: float
    roll_std_dev: float
    pressure: float
    pressure_std_dev: float
    temperature: float
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
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()

        fields = [f.strip() for f in data_part.split(",")]
        if fields[0] != "$PNORS2":
            raise ValueError(f"Invalid prefix: {fields[0]}")

        data = {}
        for field_str in fields[1:]:
            tag, val = parse_tagged_field(field_str)
            if tag not in cls.TAG_IDS:
                raise ValueError(f"Unknown tag in PNORS2: {tag}")
            data[cls.TAG_IDS[tag]] = val

        required = set(cls.TAG_IDS.values())
        if not all(k in data for k in required):
            missing = required - set(data.keys())
            raise ValueError(f"Missing required tags in PNORS2: {missing}")

        return cls(
            date=data["date"],
            time=data["time"],
            error_code=int(data["error_code"]),
            status_code=data["status_code"],
            battery=float(data["battery"]),
            sound_speed=float(data["sound_speed"]),
            heading_std_dev=float(data["heading_std_dev"]),
            heading=float(data["heading"]),
            pitch=float(data["pitch"]),
            pitch_std_dev=float(data["pitch_std_dev"]),
            roll=float(data["roll"]),
            roll_std_dev=float(data["roll_std_dev"]),
            pressure=float(data["pressure"]),
            pressure_std_dev=float(data["pressure_std_dev"]),
            temperature=float(data["temperature"]),
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
            "checksum": self.checksum,
        }


@dataclass(frozen=True)
class PNORS3:
    """PNORS3 tagged sensor data (DF=103).
    Format: $PNORS3,BV=Battery,SS=SoundSpeed,H=Heading,PI=Pitch,R=Roll,P=Pressure,T=Temperature*CS
    """

    battery: float
    sound_speed: float
    heading: float
    pitch: float
    roll: float
    pressure: float
    temperature: float
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
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()

        fields = [f.strip() for f in data_part.split(",")]
        if fields[0] != "$PNORS3":
            raise ValueError(f"Invalid prefix: {fields[0]}")

        data = {}
        for field_str in fields[1:]:
            tag, val = parse_tagged_field(field_str)
            if tag not in cls.TAG_IDS:
                raise ValueError(f"Unknown tag in PNORS3: {tag}")
            data[cls.TAG_IDS[tag]] = float(val)

        if not all(k in data for k in cls.TAG_IDS.values()):
            missing = set(cls.TAG_IDS.values()) - set(data.keys())
            raise ValueError(f"Missing required tags in PNORS3: {missing}")

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
            "checksum": self.checksum,
        }


@dataclass(frozen=True)
class PNORS4:
    """PNORS4 minimal sensor data (DF=104).
    Format: $PNORS4,Battery,SoundSpeed,Heading,Pitch,Roll,Pressure,Temperature*CS
    """

    battery: float
    sound_speed: float
    heading: float
    pitch: float
    roll: float
    pressure: float
    temperature: float
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
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()

        fields = [f.strip() for f in data_part.split(",")]
        if len(fields) != 8:
            raise ValueError(f"Expected 8 fields for PNORS4, got {len(fields)}")
        if fields[0] != "$PNORS4":
            raise ValueError(f"Invalid prefix: {fields[0]}")

        return cls(
            battery=float(fields[1]),
            sound_speed=float(fields[2]),
            heading=float(fields[3]),
            pitch=float(fields[4]),
            roll=float(fields[5]),
            pressure=float(fields[6]),
            temperature=float(fields[7]),
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
            "checksum": self.checksum,
        }
