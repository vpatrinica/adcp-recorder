"""PNORE echo intensity data message parser."""

from dataclasses import dataclass, field
from typing import Dict, Optional

from .utils import (
    validate_date_string,
    validate_time_string,
    validate_range,
)


@dataclass(frozen=True)
class PNORE:
    """PNORE echo intensity data message.
    Format: $PNORE,MMDDYY,HHMMSS,CellIndex,Echo1,Echo2,Echo3,Echo4*CS
    """
    date: str
    time: str
    cell_index: int
    echo1: int
    echo2: int
    echo3: int
    echo4: int
    checksum: Optional[str] = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_string(self.date)
        validate_time_string(self.time)
        validate_range(self.cell_index, "Cell index", 1, 1000)
        validate_range(self.echo1, "Echo 1", 0, 255)
        validate_range(self.echo2, "Echo 2", 0, 255)
        validate_range(self.echo3, "Echo 3", 0, 255)
        validate_range(self.echo4, "Echo 4", 0, 255)

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORE":
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()
        
        fields = [f.strip() for f in data_part.split(",")]
        if len(fields) != 8:
            raise ValueError(f"Expected 8 fields for PNORE, got {len(fields)}")
        if fields[0] != "$PNORE":
            raise ValueError(f"Invalid prefix: {fields[0]}")
            
        return cls(
            date=fields[1],
            time=fields[2],
            cell_index=int(fields[3]),
            echo1=int(fields[4]),
            echo2=int(fields[5]),
            echo3=int(fields[6]),
            echo4=int(fields[7]),
            checksum=checksum
        )

    def to_dict(self) -> Dict:
        return {
            "sentence_type": "PNORE",
            "date": self.date,
            "time": self.time,
            "cell_index": self.cell_index,
            "echo1": self.echo1,
            "echo2": self.echo2,
            "echo3": self.echo3,
            "echo4": self.echo4,
            "checksum": self.checksum
        }
