"""PNORH family parsers for measurement configuration headers.

Implements parsers for:
- PNORH3: Tagged configuration header (DF=103)
- PNORH4: Positional configuration header (DF=104)
"""

from dataclasses import dataclass, field

from .utils import (
    parse_tagged_field,
    validate_date_yy_mm_dd,
    validate_hex_string,
    validate_range,
    validate_time_string,
)


def _validate_common_header(
    instrument_type: int,
    num_beams: int,
    num_cells: int,
    blanking: float,
    cell_size: float,
    coordinate_system: str,
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
    Format: $PNORH3,DATE=YYMMDD,TIME=HHMMSS,EC=ErrorCode,SC=StatusCode*CS
    """

    date: str
    time: str
    error_code: int
    status_code: str
    checksum: str | None = field(default=None, repr=False)

    TAG_IDS = {"DATE": "date", "TIME": "time", "EC": "error_code", "SC": "status_code"}

    def __post_init__(self):
        validate_date_yy_mm_dd(self.date)
        validate_time_string(self.time)
        validate_hex_string(self.status_code, 8, 8)

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
            if field_name == "error_code":
                data[field_name] = int(val)
            else:
                data[field_name] = val

        if not all(k in data for k in cls.TAG_IDS.values()):
            missing = set(cls.TAG_IDS.values()) - set(data.keys())
            raise ValueError(f"Missing required tags in PNORH3: {missing}")

        return cls(**data, checksum=checksum)

    def to_dict(self) -> dict:
        return {
            "sentence_type": "PNORH3",
            "date": self.date,
            "time": self.time,
            "error_code": self.error_code,
            "status_code": self.status_code,
            "checksum": self.checksum,
        }


@dataclass(frozen=True)
class PNORH4:
    """PNORH4 positional configuration header (DF=104).
    Format: $PNORH4,YYMMDD,HHMMSS,ErrorCode,StatusCode*CS
    """

    date: str
    time: str
    error_code: int
    status_code: str
    checksum: str | None = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_yy_mm_dd(self.date)
        validate_time_string(self.time)
        validate_hex_string(self.status_code, 8, 8)

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORH4":
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()

        fields = [f.strip() for f in data_part.split(",")]
        if len(fields) != 5:
            raise ValueError(f"Expected 5 fields for PNORH4, got {len(fields)}")
        if fields[0] != "$PNORH4":
            raise ValueError(f"Invalid prefix: {fields[0]}")

        return cls(
            date=fields[1],
            time=fields[2],
            error_code=int(fields[3]),
            status_code=fields[4],
            checksum=checksum,
        )

    def to_dict(self) -> dict:
        return {
            "sentence_type": "PNORH4",
            "date": self.date,
            "time": self.time,
            "error_code": self.error_code,
            "status_code": self.status_code,
            "checksum": self.checksum,
        }
