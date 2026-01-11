"""Specialized NMEA parsers for wave data, bottom tracking, and diagnostics.

Implements parsers for:
- PNORW: Wave data (height, period, direction)
- PNORB: Bottom tracking data
- PNORE: Echo intensity data
- PNORF: Frequency and diagnostics
- PNORWD: Wave directional data
"""

from dataclasses import dataclass, field
from typing import Dict, Optional

from .utils import (
    validate_date_string,
    validate_time_string,
    validate_range,
)


@dataclass(frozen=True)
class PNORW:
    """PNORW wave data message.
    Format: $PNORW,MMDDYY,HHMMSS,SigWaveHeight,MaxWaveHeight,PeakPeriod,MeanDirection*CS
    """
    date: str
    time: str
    sig_wave_height: float
    max_wave_height: float
    peak_period: float
    mean_direction: float
    checksum: Optional[str] = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_string(self.date)
        validate_time_string(self.time)
        validate_range(self.sig_wave_height, "Significant wave height", 0.0, 30.0)
        validate_range(self.max_wave_height, "Max wave height", 0.0, 50.0)
        validate_range(self.peak_period, "Peak period", 0.0, 30.0)
        validate_range(self.mean_direction, "Mean direction", 0.0, 360.0)

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORW":
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()
        
        fields = [f.strip() for f in data_part.split(",")]
        if len(fields) != 7:
            raise ValueError(f"Expected 7 fields for PNORW, got {len(fields)}")
        if fields[0] != "$PNORW":
            raise ValueError(f"Invalid prefix: {fields[0]}")
            
        return cls(
            date=fields[1],
            time=fields[2],
            sig_wave_height=float(fields[3]),
            max_wave_height=float(fields[4]),
            peak_period=float(fields[5]),
            mean_direction=float(fields[6]),
            checksum=checksum
        )

    def to_dict(self) -> Dict:
        return {
            "sentence_type": "PNORW",
            "date": self.date,
            "time": self.time,
            "sig_wave_height": self.sig_wave_height,
            "max_wave_height": self.max_wave_height,
            "peak_period": self.peak_period,
            "mean_direction": self.mean_direction,
            "checksum": self.checksum
        }


