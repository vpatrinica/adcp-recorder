"""PNORB bottom tracking data message parser."""

from dataclasses import dataclass, field
from typing import Dict, Optional

from .utils import (
    validate_date_string,
    validate_time_string,
    validate_range,
)


@dataclass(frozen=True)
class PNORB:
    """PNORB bottom tracking data message.
    Format: $PNORB,MMDDYY,HHMMSS,VelEast,VelNorth,VelUp,BottomDist,Quality*CS
    """
    date: str
    time: str
    vel_east: float
    vel_north: float
    vel_up: float
    bottom_dist: float
    quality: int
    checksum: Optional[str] = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_string(self.date)
        validate_time_string(self.time)
        validate_range(self.vel_east, "Velocity East", -10.0, 10.0)
        validate_range(self.vel_north, "Velocity North", -10.0, 10.0)
        validate_range(self.vel_up, "Velocity Up", -10.0, 10.0)
        validate_range(self.bottom_dist, "Bottom distance", 0.0, 1000.0)
        validate_range(self.quality, "Quality", 0, 100)

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORB":
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()
        
        fields = [f.strip() for f in data_part.split(",")]
        if len(fields) != 8:
            raise ValueError(f"Expected 8 fields for PNORB, got {len(fields)}")
        if fields[0] != "$PNORB":
            raise ValueError(f"Invalid prefix: {fields[0]}")
            
        return cls(
            date=fields[1],
            time=fields[2],
            vel_east=float(fields[3]),
            vel_north=float(fields[4]),
            vel_up=float(fields[5]),
            bottom_dist=float(fields[6]),
            quality=int(fields[7]),
            checksum=checksum
        )

    def to_dict(self) -> Dict:
        return {
            "sentence_type": "PNORB",
            "date": self.date,
            "time": self.time,
            "vel_east": self.vel_east,
            "vel_north": self.vel_north,
            "vel_up": self.vel_up,
            "bottom_dist": self.bottom_dist,
            "quality": self.quality,
            "checksum": self.checksum
        }
