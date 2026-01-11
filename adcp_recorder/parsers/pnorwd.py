"""PNORWD wave directional data message parser."""

from dataclasses import dataclass, field
from typing import Dict, Optional

from .utils import (
    validate_date_string,
    validate_time_string,
    validate_range,
)


@dataclass(frozen=True)
class PNORWD:
    """PNORWD wave directional data message.
    Format: $PNORWD,MMDDYY,HHMMSS,FreqBin,Direction,SpreadAngle,Energy*CS
    """
    date: str
    time: str
    freq_bin: int
    direction: float
    spread_angle: float
    energy: float
    checksum: Optional[str] = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_string(self.date)
        validate_time_string(self.time)
        validate_range(self.freq_bin, "Frequency bin", 1, 100)
        validate_range(self.direction, "Direction", 0.0, 360.0)
        validate_range(self.spread_angle, "Spread angle", 0.0, 180.0)
        validate_range(self.energy, "Energy", 0.0, 100.0)

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORWD":
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()
        
        fields = [f.strip() for f in data_part.split(",")]
        if len(fields) != 7:
            raise ValueError(f"Expected 7 fields for PNORWD, got {len(fields)}")
        if fields[0] != "$PNORWD":
            raise ValueError(f"Invalid prefix: {fields[0]}")
            
        return cls(
            date=fields[1],
            time=fields[2],
            freq_bin=int(fields[3]),
            direction=float(fields[4]),
            spread_angle=float(fields[5]),
            energy=float(fields[6]),
            checksum=checksum
        )

    def to_dict(self) -> Dict:
        return {
            "sentence_type": "PNORWD",
            "date": self.date,
            "time": self.time,
            "freq_bin": self.freq_bin,
            "direction": self.direction,
            "spread_angle": self.spread_angle,
            "energy": self.energy,
            "checksum": self.checksum
        }
