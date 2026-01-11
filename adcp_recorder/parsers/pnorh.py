"""PNORH family parsers for measurement headers.

Implements parsers for:
- PNORH3: Base header for current velocity series
- PNORH4: Extended header with coordinate system and interval
"""

from dataclasses import dataclass, field
from typing import Dict, Optional

from .utils import (
    validate_date_string,
    validate_time_string,
    validate_range,
)


def _validate_cell_range(num_cells: int, first_cell: int) -> None:
    """Validate number of cells and first cell index."""
    validate_range(num_cells, "Number of cells", 1, 1000)
    validate_range(first_cell, "First cell", 1, num_cells)


def _validate_ping_count(count: int) -> None:
    """Validate ping count (>= 1)."""
    if count < 1:
        raise ValueError(f"Ping count must be at least 1, got {count}")


def _validate_coord_system(coord_sys: str) -> None:
    """Validate coordinate system string."""
    if coord_sys not in {"ENU", "XYZ", "BEAM"}:
        raise ValueError(f"Invalid coordinate system for header: {coord_sys}")


@dataclass(frozen=True)
class PNORH3:
    """PNORH3 header for current velocity measurement series.
    Format: $PNORH3,MMDDYY,HHMMSS,NumCells,FirstCell,PingCount*CS
    """
    date: str
    time: str
    num_cells: int
    first_cell: int
    ping_count: int
    checksum: Optional[str] = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_string(self.date)
        validate_time_string(self.time)
        _validate_cell_range(self.num_cells, self.first_cell)
        _validate_ping_count(self.ping_count)

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORH3":
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()
        
        fields = [f.strip() for f in data_part.split(",")]
        if len(fields) != 6:
            raise ValueError(f"Expected 6 fields for PNORH3, got {len(fields)}")
        if fields[0] != "$PNORH3":
            raise ValueError(f"Invalid prefix: {fields[0]}")
            
        return cls(
            date=fields[1],
            time=fields[2],
            num_cells=int(fields[3]),
            first_cell=int(fields[4]),
            ping_count=int(fields[5]),
            checksum=checksum
        )

    def to_dict(self) -> Dict:
        return {
            "sentence_type": "PNORH3",
            "date": self.date,
            "time": self.time,
            "num_cells": self.num_cells,
            "first_cell": self.first_cell,
            "ping_count": self.ping_count,
            "checksum": self.checksum
        }


@dataclass(frozen=True)
class PNORH4:
    """PNORH4 extended header for current velocity measurement series.
    Format: $PNORH4,MMDDYY,HHMMSS,NumCells,FirstCell,PingCount,CoordSystem,ProfileInterval*CS
    """
    date: str
    time: str
    num_cells: int
    first_cell: int
    ping_count: int
    coordinate_system: str
    profile_interval: float
    checksum: Optional[str] = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_string(self.date)
        validate_time_string(self.time)
        _validate_cell_range(self.num_cells, self.first_cell)
        _validate_ping_count(self.ping_count)
        _validate_coord_system(self.coordinate_system)
        if self.profile_interval <= 0:
            raise ValueError(f"Profile interval must be positive, got {self.profile_interval}")

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORH4":
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()
        
        fields = [f.strip() for f in data_part.split(",")]
        if len(fields) != 8:
            raise ValueError(f"Expected 8 fields for PNORH4, got {len(fields)}")
        if fields[0] != "$PNORH4":
            raise ValueError(f"Invalid prefix: {fields[0]}")
            
        return cls(
            date=fields[1],
            time=fields[2],
            num_cells=int(fields[3]),
            first_cell=int(fields[4]),
            ping_count=int(fields[5]),
            coordinate_system=fields[6],
            profile_interval=float(fields[7]),
            checksum=checksum
        )

    def to_dict(self) -> Dict:
        return {
            "sentence_type": "PNORH4",
            "date": self.date,
            "time": self.time,
            "num_cells": self.num_cells,
            "first_cell": self.first_cell,
            "ping_count": self.ping_count,
            "coordinate_system": self.coordinate_system,
            "profile_interval": self.profile_interval,
            "checksum": self.checksum
        }
