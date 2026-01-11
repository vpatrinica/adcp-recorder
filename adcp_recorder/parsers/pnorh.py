"""PNORH family parsers for measurement configuration headers.

Implements parsers for:
- PNORH3: Tagged configuration header (DF=103)
- PNORH4: Positional configuration header (DF=104)
"""

from dataclasses import dataclass, field
from typing import Dict, Optional

from .utils import (
    validate_date_yy_mm_dd,
    validate_time_string,
    validate_range,
    parse_tagged_field,
)


def _validate_common_header(
    instrument_type: int,
    num_beams: int,
    num_cells: int,
    blanking: float,
    cell_size: float,
    coordinate_system: str
) -> None:
    """Validate common configuration fields."""
    validate_range(instrument_type, "Instrument type", 0, 100)
    validate_range(num_beams, "Number of beams", 1, 4)
    validate_range(num_cells, "Number of cells", 1, 1000)
    validate_range(blanking, "Blanking distance", 0.0, 100.0)
    validate_range(cell_size, "Cell size", 0.0, 100.0)
    if coordinate_system not in {"BEAM", "XYZ", "ENU"}:
        raise ValueError(f"Invalid coordinate system: {coordinate_system}")


@dataclass(frozen=True)
class PNORH3:
    """PNORH3 tagged configuration header (DF=103).
    Format: $PNORH3,ID=InstrumentID,TYPE=InstrumentType,SN=SerialNumber,FW=FirmwareVersion,DATE=YYMMDD,TIME=HHMMSS,MODE=RecordMode,LEN=BurstLength,INT=BurstInterval,SAMP=SampleRate,NBEAM=NumBeams,NCELL=NumCells,BLANK=BlankingDist,CELL=CellSize,COORD=CoordSystem*CS
    """
    instrument_id: str
    instrument_type: int
    serial_number: str
    firmware_version: str
    date: str
    time: str
    record_mode: int
    burst_length: int
    burst_interval: int
    sample_rate: float
    num_beams: int
    num_cells: int
    blanking: float
    cell_size: float
    coordinate_system: str
    checksum: Optional[str] = field(default=None, repr=False)

    TAG_IDS = {
        "ID": "instrument_id", "TYPE": "instrument_type", "SN": "serial_number",
        "FW": "firmware_version", "DATE": "date", "TIME": "time",
        "MODE": "record_mode", "LEN": "burst_length", "INT": "burst_interval",
        "SAMP": "sample_rate", "NBEAM": "num_beams", "NCELL": "num_cells",
        "BLANK": "blanking", "CELL": "cell_size", "COORD": "coordinate_system"
    }

    def __post_init__(self):
        validate_date_yy_mm_dd(self.date)
        validate_time_string(self.time)
        _validate_common_header(
            self.instrument_type, self.num_beams, self.num_cells,
            self.blanking, self.cell_size, self.coordinate_system
        )

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORH3":
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()
        
        fields = [f.strip() for f in data_part.split(",")]
        if fields[0] != "$PNORH3":
            raise ValueError(f"Invalid prefix: {fields[0]}")
            
        data = {}
        for field_str in fields[1:]:
            tag, val = parse_tagged_field(field_str)
            if tag not in cls.TAG_IDS:
                raise ValueError(f"Unknown tag in PNORH3: {tag}")
            
            field_name = cls.TAG_IDS[tag]
            if field_name in ["instrument_type", "record_mode", "burst_length", "burst_interval", "num_beams", "num_cells"]:
                data[field_name] = int(val)
            elif field_name in ["sample_rate", "blanking", "cell_size"]:
                data[field_name] = float(val)
            else:
                data[field_name] = val
            
        if not all(k in data for k in cls.TAG_IDS.values()):
             missing = set(cls.TAG_IDS.values()) - set(data.keys())
             raise ValueError(f"Missing required tags in PNORH3: {missing}")

        return cls(**data, checksum=checksum)

    def to_dict(self) -> Dict:
        return {
            "sentence_type": "PNORH3",
            "instrument_id": self.instrument_id,
            "instrument_type": self.instrument_type,
            "serial_number": self.serial_number,
            "firmware_version": self.firmware_version,
            "date": self.date,
            "time": self.time,
            "record_mode": self.record_mode,
            "burst_length": self.burst_length,
            "burst_interval": self.burst_interval,
            "sample_rate": self.sample_rate,
            "num_beams": self.num_beams,
            "num_cells": self.num_cells,
            "blanking": self.blanking,
            "cell_size": self.cell_size,
            "coordinate_system": self.coordinate_system,
            "checksum": self.checksum
        }


@dataclass(frozen=True)
class PNORH4:
    """PNORH4 positional configuration header (DF=104).
    Format: $PNORH4,ID,Type,SN,FW,YYMMDD,HHMMSS,Mode,Len,Int,Samp,NBeam,NCell,Blank,Cell,Coord*CS
    """
    instrument_id: str
    instrument_type: int
    serial_number: str
    firmware_version: str
    date: str
    time: str
    record_mode: int
    burst_length: int
    burst_interval: int
    sample_rate: float
    num_beams: int
    num_cells: int
    blanking: float
    cell_size: float
    coordinate_system: str
    checksum: Optional[str] = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_yy_mm_dd(self.date)
        validate_time_string(self.time)
        _validate_common_header(
            self.instrument_type, self.num_beams, self.num_cells,
            self.blanking, self.cell_size, self.coordinate_system
        )

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORH4":
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()
        
        fields = [f.strip() for f in data_part.split(",")]
        if len(fields) != 16:
            raise ValueError(f"Expected 16 fields for PNORH4, got {len(fields)}")
        if fields[0] != "$PNORH4":
            raise ValueError(f"Invalid prefix: {fields[0]}")
            
        return cls(
            instrument_id=fields[1],
            instrument_type=int(fields[2]),
            serial_number=fields[3],
            firmware_version=fields[4],
            date=fields[5],
            time=fields[6],
            record_mode=int(fields[7]),
            burst_length=int(fields[8]),
            burst_interval=int(fields[9]),
            sample_rate=float(fields[10]),
            num_beams=int(fields[11]),
            num_cells=int(fields[12]),
            blanking=float(fields[13]),
            cell_size=float(fields[14]),
            coordinate_system=fields[15],
            checksum=checksum
        )

    def to_dict(self) -> Dict:
        return {
            "sentence_type": "PNORH4",
            "instrument_id": self.instrument_id,
            "instrument_type": self.instrument_type,
            "serial_number": self.serial_number,
            "firmware_version": self.firmware_version,
            "date": self.date,
            "time": self.time,
            "record_mode": self.record_mode,
            "burst_length": self.burst_length,
            "burst_interval": self.burst_interval,
            "sample_rate": self.sample_rate,
            "num_beams": self.num_beams,
            "num_cells": self.num_cells,
            "blanking": self.blanking,
            "cell_size": self.cell_size,
            "coordinate_system": self.coordinate_system,
            "checksum": self.checksum
        }
