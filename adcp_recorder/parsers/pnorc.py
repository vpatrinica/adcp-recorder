"""PNORC family parsers for current velocity data messages.

Implements parsers for:
- PNORC: Base current velocity
- PNORC1: Current velocity with correlation
- PNORC2: Tagged current velocity
- PNORC3: Current velocity with amplitude
- PNORC4: Complete current velocity format
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Set

from .utils import (
    validate_date_string,
    validate_time_string,
    validate_range,
)


def _validate_velocity(value: float, index: int) -> None:
    """Validate velocity component (-10 to +10 m/s)."""
    validate_range(value, f"Velocity {index}", -10.0, 10.0)


def _validate_correlation(value: int, index: int) -> None:
    """Validate correlation (0-100%)."""
    validate_range(value, f"Correlation {index}", 0, 100)


def _validate_amplitude(value: int, index: int) -> None:
    """Validate amplitude (0-255 counts)."""
    validate_range(value, f"Amplitude {index}", 0, 255)


def _validate_cell_index(value: int) -> None:
    """Validate cell index (1-1000)."""
    validate_range(value, "Cell index", 1, 1000)


@dataclass(frozen=True)
class PNORC:
    """PNORC base current velocity message.
    Format: $PNORC,MMDDYY,HHMMSS,CellIndex,Vel1,Vel2,Vel3*CS
    """
    date: str
    time: str
    cell_index: int
    vel1: float
    vel2: float
    vel3: float
    checksum: Optional[str] = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_string(self.date)
        validate_time_string(self.time)
        _validate_cell_index(self.cell_index)
        _validate_velocity(self.vel1, 1)
        _validate_velocity(self.vel2, 2)
        _validate_velocity(self.vel3, 3)

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORC":
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()
        
        fields = [f.strip() for f in data_part.split(",")]
        if len(fields) != 7:
            raise ValueError(f"Expected 7 fields for PNORC, got {len(fields)}")
        if fields[0] != "$PNORC":
            raise ValueError(f"Invalid prefix: {fields[0]}")
            
        return cls(
            date=fields[1],
            time=fields[2],
            cell_index=int(fields[3]),
            vel1=float(fields[4]),
            vel2=float(fields[5]),
            vel3=float(fields[6]),
            checksum=checksum
        )

    def to_dict(self) -> Dict:
        return {
            "sentence_type": "PNORC",
            "date": self.date,
            "time": self.time,
            "cell_index": self.cell_index,
            "vel1": self.vel1,
            "vel2": self.vel2,
            "vel3": self.vel3,
            "checksum": self.checksum
        }


@dataclass(frozen=True)
class PNORC1:
    """PNORC1 current velocity with correlation.
    Format: $PNORC1,MMDDYY,HHMMSS,CellIndex,Vel1,Vel2,Vel3,Corr1,Corr2,Corr3*CS
    """
    date: str
    time: str
    cell_index: int
    vel1: float
    vel2: float
    vel3: float
    corr1: int
    corr2: int
    corr3: int
    checksum: Optional[str] = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_string(self.date)
        validate_time_string(self.time)
        _validate_cell_index(self.cell_index)
        _validate_velocity(self.vel1, 1)
        _validate_velocity(self.vel2, 2)
        _validate_velocity(self.vel3, 3)
        _validate_correlation(self.corr1, 1)
        _validate_correlation(self.corr2, 2)
        _validate_correlation(self.corr3, 3)

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORC1":
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()
        
        fields = [f.strip() for f in data_part.split(",")]
        if len(fields) != 10:
            raise ValueError(f"Expected 10 fields for PNORC1, got {len(fields)}")
        if fields[0] != "$PNORC1":
            raise ValueError(f"Invalid prefix: {fields[0]}")
            
        return cls(
            date=fields[1],
            time=fields[2],
            cell_index=int(fields[3]),
            vel1=float(fields[4]),
            vel2=float(fields[5]),
            vel3=float(fields[6]),
            corr1=int(fields[7]),
            corr2=int(fields[8]),
            corr3=int(fields[9]),
            checksum=checksum
        )

    def to_dict(self) -> Dict:
        return {
            "sentence_type": "PNORC1",
            "date": self.date,
            "time": self.time,
            "cell_index": self.cell_index,
            "vel1": self.vel1,
            "vel2": self.vel2,
            "vel3": self.vel3,
            "corr1": self.corr1,
            "corr2": self.corr2,
            "corr3": self.corr3,
            "checksum": self.checksum
        }


class PNORC2Tag:
    """Tags for PNORC2 (Tagged current velocity)."""
    DATE = "DT"
    TIME = "TM"
    CELL_INDEX = "CI"
    VEL1 = "VE"
    VEL2 = "VN"
    VEL3 = "VU"
    
    REQUIRED_TAGS = {DATE, TIME, CELL_INDEX, VEL1, VEL2, VEL3}

    @classmethod
    def parse_tagged_field(cls, field_str: str) -> tuple[str, str]:
        if "=" not in field_str:
            raise ValueError(f"Tagged field must contain '=': {field_str}")
        tag, value = field_str.split("=", 1)
        return tag.strip().upper(), value.strip()


@dataclass(frozen=True)
class PNORC2:
    """PNORC2 tagged current velocity message.
    Format: $PNORC2,DT=MMDDYY,TM=HHMMSS,CI=CellIndex,VE=Vel1,VN=Vel2,VU=Vel3*CS
    """
    date: str
    time: str
    cell_index: int
    vel1: float
    vel2: float
    vel3: float
    checksum: Optional[str] = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_string(self.date)
        validate_time_string(self.time)
        _validate_cell_index(self.cell_index)
        _validate_velocity(self.vel1, 1)
        _validate_velocity(self.vel2, 2)
        _validate_velocity(self.vel3, 3)

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORC2":
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()
        
        fields = [f.strip() for f in data_part.split(",")]
        if len(fields) < 7:
            raise ValueError(f"Expected at least 7 fields for PNORC2, got {len(fields)}")
        if fields[0] != "$PNORC2":
            raise ValueError(f"Invalid prefix: {fields[0]}")
            
        data = {}
        for field_str in fields[1:]:
            tag, val = PNORC2Tag.parse_tagged_field(field_str)
            if tag in data:
                raise ValueError(f"Duplicate tag in PNORC2: {tag}")
            data[tag] = val
            
        # Verify all required tags present
        if set(data.keys()) != PNORC2Tag.REQUIRED_TAGS:
            missing = PNORC2Tag.REQUIRED_TAGS - set(data.keys())
            extra = set(data.keys()) - PNORC2Tag.REQUIRED_TAGS
            if missing:
                raise ValueError(f"Missing required tags in PNORC2: {missing}")
            if extra:
                raise ValueError(f"Unknown tags in PNORC2: {extra}")
            
        return cls(
            date=data[PNORC2Tag.DATE],
            time=data[PNORC2Tag.TIME],
            cell_index=int(data[PNORC2Tag.CELL_INDEX]),
            vel1=float(data[PNORC2Tag.VEL1]),
            vel2=float(data[PNORC2Tag.VEL2]),
            vel3=float(data[PNORC2Tag.VEL3]),
            checksum=checksum
        )

    def to_dict(self) -> Dict:
        return {
            "sentence_type": "PNORC2",
            "date": self.date,
            "time": self.time,
            "cell_index": self.cell_index,
            "vel1": self.vel1,
            "vel2": self.vel2,
            "vel3": self.vel3,
            "checksum": self.checksum
        }


@dataclass(frozen=True)
class PNORC3:
    """PNORC3 current velocity with amplitude.
    Format: $PNORC3,MMDDYY,HHMMSS,CellIndex,Vel1,Vel2,Vel3,Amp1,Amp2,Amp3,Amp4*CS
    """
    date: str
    time: str
    cell_index: int
    vel1: float
    vel2: float
    vel3: float
    amp1: int
    amp2: int
    amp3: int
    amp4: int
    checksum: Optional[str] = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_string(self.date)
        validate_time_string(self.time)
        _validate_cell_index(self.cell_index)
        _validate_velocity(self.vel1, 1)
        _validate_velocity(self.vel2, 2)
        _validate_velocity(self.vel3, 3)
        _validate_amplitude(self.amp1, 1)
        _validate_amplitude(self.amp2, 2)
        _validate_amplitude(self.amp3, 3)
        _validate_amplitude(self.amp4, 4)

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORC3":
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()
        
        fields = [f.strip() for f in data_part.split(",")]
        if len(fields) != 11:
            raise ValueError(f"Expected 11 fields for PNORC3, got {len(fields)}")
        if fields[0] != "$PNORC3":
            raise ValueError(f"Invalid prefix: {fields[0]}")
            
        return cls(
            date=fields[1],
            time=fields[2],
            cell_index=int(fields[3]),
            vel1=float(fields[4]),
            vel2=float(fields[5]),
            vel3=float(fields[6]),
            amp1=int(fields[7]),
            amp2=int(fields[8]),
            amp3=int(fields[9]),
            amp4=int(fields[10]),
            checksum=checksum
        )


    def to_dict(self) -> Dict:
        return {
            "sentence_type": "PNORC3",
            "date": self.date,
            "time": self.time,
            "cell_index": self.cell_index,
            "vel1": self.vel1,
            "vel2": self.vel2,
            "vel3": self.vel3,
            "amp1": self.amp1,
            "amp2": self.amp2,
            "amp3": self.amp3,
            "amp4": self.amp4,
            "checksum": self.checksum
        }


@dataclass(frozen=True)
class PNORC4:
    """PNORC4 complete current velocity format.
    Format: $PNORC4,MMDDYY,HHMMSS,CellIndex,VelE,VelN,VelU,Corr1,Corr2,Corr3,Amp1,Amp2,Amp3,Amp4*CS
    """
    date: str
    time: str
    cell_index: int
    vel1: float
    vel2: float
    vel3: float
    corr1: int
    corr2: int
    corr3: int
    amp1: int
    amp2: int
    amp3: int
    amp4: int
    checksum: Optional[str] = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_string(self.date)
        validate_time_string(self.time)
        _validate_cell_index(self.cell_index)
        _validate_velocity(self.vel1, 1)
        _validate_velocity(self.vel2, 2)
        _validate_velocity(self.vel3, 3)
        _validate_correlation(self.corr1, 1)
        _validate_correlation(self.corr2, 2)
        _validate_correlation(self.corr3, 3)
        _validate_amplitude(self.amp1, 1)
        _validate_amplitude(self.amp2, 2)
        _validate_amplitude(self.amp3, 3)
        _validate_amplitude(self.amp4, 4)

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORC4":
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()
        
        fields = [f.strip() for f in data_part.split(",")]
        if len(fields) != 14:
            raise ValueError(f"Expected 14 fields for PNORC4, got {len(fields)}")
        if fields[0] != "$PNORC4":
            raise ValueError(f"Invalid prefix: {fields[0]}")
            
        return cls(
            date=fields[1],
            time=fields[2],
            cell_index=int(fields[3]),
            vel1=float(fields[4]),
            vel2=float(fields[5]),
            vel3=float(fields[6]),
            corr1=int(fields[7]),
            corr2=int(fields[8]),
            corr3=int(fields[9]),
            amp1=int(fields[10]),
            amp2=int(fields[11]),
            amp3=int(fields[12]),
            amp4=int(fields[13]),
            checksum=checksum
        )

    def to_dict(self) -> Dict:
        return {
            "sentence_type": "PNORC4",
            "date": self.date,
            "time": self.time,
            "cell_index": self.cell_index,
            "vel1": self.vel1,
            "vel2": self.vel2,
            "vel3": self.vel3,
            "corr1": self.corr1,
            "corr2": self.corr2,
            "corr3": self.corr3,
            "amp1": self.amp1,
            "amp2": self.amp2,
            "amp3": self.amp3,
            "amp4": self.amp4,
            "checksum": self.checksum
        }
