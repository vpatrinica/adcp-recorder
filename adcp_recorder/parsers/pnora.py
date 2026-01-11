"""PNORA family parser for altitude/range data messages.

Implements parser for:
- PNORA: Altitude/range measurements (DF=200, 201)
"""

from dataclasses import dataclass, field
from typing import Dict, Optional

from .utils import (
    validate_date_yy_mm_dd,
    validate_time_string,
    validate_range,
)


@dataclass(frozen=True)
class PNORA:
    """PNORA altitude/range data message (DF=200, 201).
    Format: $PNORA,Date,Time,Method,Distance,Status,Pitch,Roll,Pressure*CS
    """
    date: str
    time: str
    method: int
    distance: float
    status: int
    pitch: float
    roll: float
    pressure: float
    checksum: Optional[str] = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_yy_mm_dd(self.date)
        validate_time_string(self.time)
        validate_range(self.method, "Altitude method", 0, 2)
        validate_range(self.distance, "Distance", 0.0, 1000.0)
        validate_range(self.pitch, "Pitch", -90.0, 90.0)
        validate_range(self.roll, "Roll", -90.0, 90.0)
        validate_range(self.pressure, "Pressure", 0.0, 20000.0)

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORA":
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()
        
        fields = [f.strip() for f in data_part.split(",")]
        if len(fields) != 9:
            raise ValueError(f"Expected 9 fields for PNORA, got {len(fields)}")
        if fields[0] != "$PNORA":
            raise ValueError(f"Invalid prefix: {fields[0]}")
            
        return cls(
            date=fields[1],
            time=fields[2],
            method=int(fields[3]),
            distance=float(fields[4]),
            status=int(fields[5]),
            pitch=float(fields[6]),
            roll=float(fields[7]),
            pressure=float(fields[8]),
            checksum=checksum
        )

    def to_dict(self) -> Dict:
        return {
            "sentence_type": "PNORA",
            "date": self.date,
            "time": self.time,
            "method": self.method,
            "distance": self.distance,
            "status": self.status,
            "pitch": self.pitch,
            "roll": self.roll,
            "pressure": self.pressure,
            "checksum": self.checksum
        }
