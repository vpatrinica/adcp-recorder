"""PNORA family parser for altitude/range data messages.

Implements parser for:
- PNORA: Altitude/range measurements (distance to surface/bottom)
"""

from dataclasses import dataclass, field
from typing import Dict, Optional

from .utils import (
    validate_date_string,
    validate_time_string,
    validate_range,
)


@dataclass(frozen=True)
class PNORA:
    """PNORA altitude/range data message.
    Format: $PNORA,MMDDYY,HHMMSS,AltitudeMethod,Distance,Quality*CS
    """
    date: str
    time: str
    method: int
    distance: float
    quality: int
    checksum: Optional[str] = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_string(self.date)
        validate_time_string(self.time)
        validate_range(self.method, "Altitude method", 0, 2)
        validate_range(self.distance, "Distance", 0.0, 1000.0)
        validate_range(self.quality, "Quality", 0, 100)

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORA":
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()
        
        fields = [f.strip() for f in data_part.split(",")]
        if len(fields) != 6:
            raise ValueError(f"Expected 6 fields for PNORA, got {len(fields)}")
        if fields[0] != "$PNORA":
            raise ValueError(f"Invalid prefix: {fields[0]}")
            
        return cls(
            date=fields[1],
            time=fields[2],
            method=int(fields[3]),
            distance=float(fields[4]),
            quality=int(fields[5]),
            checksum=checksum
        )

    def to_dict(self) -> Dict:
        return {
            "sentence_type": "PNORA",
            "date": self.date,
            "time": self.time,
            "method": self.method,
            "distance": self.distance,
            "quality": self.quality,
            "checksum": self.checksum
        }
