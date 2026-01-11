"""PNORF frequency data message parser."""

from dataclasses import dataclass, field
from typing import Dict, Optional

from .utils import (
    validate_date_string,
    validate_time_string,
    validate_range,
)


@dataclass(frozen=True)
class PNORF:
    """PNORF frequency data message.
    Format: $PNORF,MMDDYY,HHMMSS,Frequency,Bandwidth,TransmitPower*CS
    """
    date: str
    time: str
    frequency: float
    bandwidth: float
    transmit_power: float
    checksum: Optional[str] = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_string(self.date)
        validate_time_string(self.time)
        validate_range(self.frequency, "Frequency", 50.0, 2000.0)
        validate_range(self.bandwidth, "Bandwidth", 1.0, 100.0)
        validate_range(self.transmit_power, "Transmit power", 0.0, 100.0)

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORF":
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()
        
        fields = [f.strip() for f in data_part.split(",")]
        if len(fields) != 6:
            raise ValueError(f"Expected 6 fields for PNORF, got {len(fields)}")
        if fields[0] != "$PNORF":
            raise ValueError(f"Invalid prefix: {fields[0]}")
            
        return cls(
            date=fields[1],
            time=fields[2],
            frequency=float(fields[3]),
            bandwidth=float(fields[4]),
            transmit_power=float(fields[5]),
            checksum=checksum
        )

    def to_dict(self) -> Dict:
        return {
            "sentence_type": "PNORF",
            "date": self.date,
            "time": self.time,
            "frequency": self.frequency,
            "bandwidth": self.bandwidth,
            "transmit_power": self.transmit_power,
            "checksum": self.checksum
        }
