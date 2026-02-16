"""PNORI family parsers for instrument configuration messages.

Implements parsers for:
- PNORI: Positional fields with numeric coordinate system
- PNORI1: Positional fields with string coordinate system
- PNORI2: Tagged fields (TAG=VALUE) with string coordinate system
"""

import re
from dataclasses import dataclass, field
from typing import Any, ClassVar

from ..core.enums import CoordinateSystem, InstrumentType
from ..core.nmea import compute_checksum
from .utils import parse_nmea_sentence, parse_optional_float


# Shared validation functions
def _validate_head_id(head_id: str, max_length: int = 30, numeric_only: bool = False) -> None:
    """Validate head ID format and length."""
    if not head_id:
        raise ValueError("Head ID cannot be empty")
    if len(head_id) > max_length:
        raise ValueError(f"Head ID too long: {len(head_id)} > {max_length}")

    pattern = r"^\d+$" if numeric_only else r"^[A-Za-z0-9_]+$"
    if not re.match(pattern, head_id):
        raise ValueError(f"Head ID contains invalid characters: {head_id}")


def _validate_beam_count(instrument_type: InstrumentType, beam_count: int | None) -> None:
    """Validate beam count for instrument type."""
    if beam_count is None:
        return
    if beam_count < 1 or beam_count > 4:
        raise ValueError(f"Beam count must be 1-4, got {beam_count}")

    valid_counts = instrument_type.valid_beam_counts
    if beam_count not in valid_counts:
        raise ValueError(
            f"{instrument_type.name} requires beam count in {valid_counts}, got {beam_count}"
        )


def _validate_cell_count(cell_count: int | None) -> None:
    """Validate cell count range (spec limit 1000)."""
    if cell_count is None:
        return
    if cell_count < 1 or cell_count > 1000:
        raise ValueError(f"Cell count must be 1-1000, got {cell_count}")


def _validate_distance(value: float | None, field_name: str) -> None:
    """Validate distance is positive and reasonable."""
    if value is None:
        return
    if value <= 0:
        raise ValueError(f"{field_name} must be positive, got {value}")
    if value > 100.0:
        raise ValueError(f"{field_name} too large (>100m), got {value}")


@dataclass(frozen=True)
class PNORI:
    """PNORI configuration message parser.

    Format: $PNORI,InstrType,HeadID,BeamCnt,CellCnt,BlankDist,CellSize,CoordSys*CS

    Positional fields with numeric coordinate system (0=ENU, 1=XYZ, 2=BEAM).

    Example:
        >>> sentence = "$PNORI,4,Signature1000900001,4,20,0.20,1.00,0*2E"
        >>> config = PNORI.from_nmea(sentence)
        >>> config.instrument_type
        <InstrumentType.SIGNATURE: 4>
        >>> config.beam_count
        4

    """

    instrument_type: InstrumentType
    head_id: str
    beam_count: int | None
    cell_count: int | None
    blanking_distance: float | None
    cell_size: float | None
    coordinate_system: CoordinateSystem
    checksum: str | None = field(default=None, repr=False)

    HEAD_ID_PATTERN: ClassVar[re.Pattern] = re.compile(r"^[A-Za-z0-9_]{1,30}$")

    def __post_init__(self) -> None:
        """Validate all fields after initialization."""
        _validate_head_id(self.head_id, 30)
        if self.beam_count is not None:
            _validate_beam_count(self.instrument_type, self.beam_count)
        if self.cell_count is not None:
            _validate_cell_count(self.cell_count)
        _validate_distance(self.blanking_distance, "Blanking distance")
        _validate_distance(self.cell_size, "Cell size")

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORI":
        """Parse PNORI message from NMEA sentence.

        Args:
            sentence: NMEA sentence string (with or without checksum)

        Returns:
            Parsed PNORI configuration object

        Raises:
            ValueError: If sentence format is invalid or fields fail validation

        """
        fields, checksum = parse_nmea_sentence(sentence)
        if len(fields) != 8:
            raise ValueError(f"Expected 8 fields, got {len(fields)}")
        if fields[0] != "$PNORI":
            raise ValueError(f"Invalid prefix: expected $PNORI, got {fields[0]}")

        # Parse and validate
        return cls(
            instrument_type=InstrumentType.from_code(int(fields[1])),
            head_id=fields[2],
            beam_count=int(fields[3]) if fields[3] and fields[3].lower() != "nan" else None,
            cell_count=int(fields[4]) if fields[4] and fields[4].lower() != "nan" else None,
            blanking_distance=parse_optional_float(fields[5]),
            cell_size=parse_optional_float(fields[6]),
            coordinate_system=CoordinateSystem.from_code(int(fields[7])),
            checksum=checksum,
        )

    def to_nmea(self, include_checksum: bool = True) -> str:
        """Serialize to NMEA sentence format.

        Args:
            include_checksum: If True, compute and append checksum

        Returns:
            NMEA sentence string

        """
        sentence = (
            f"$PNORI,{self.instrument_type.value},{self.head_id},"
            f"{self.beam_count},{self.cell_count},"
            f"{self.blanking_distance:.2f},{self.cell_size:.2f},"
            f"{self.coordinate_system.to_numeric_code()}"
        )

        if include_checksum:
            checksum = compute_checksum(sentence)
            sentence = f"{sentence}*{checksum}"

        return sentence

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for database insertion.

        Returns:
            Dictionary with all fields mapped to database column names

        """
        return {
            "sentence_type": "PNORI",
            "instrument_type_name": self.instrument_type.name,
            "instrument_type_code": self.instrument_type.value,
            "head_id": self.head_id,
            "beam_count": self.beam_count,
            "cell_count": self.cell_count,
            "blanking_distance": float(self.blanking_distance)
            if self.blanking_distance is not None
            else None,
            "cell_size": float(self.cell_size) if self.cell_size is not None else None,
            "coord_system_name": self.coordinate_system.value,
            "coord_system_code": self.coordinate_system.to_numeric_code(),
            "checksum": self.checksum,
        }


@dataclass(frozen=True)
class PNORI1:
    """PNORI1 configuration message parser.

    Format: $PNORI1,InstrType,HeadID,BeamCnt,CellCnt,BlankDist,CellSize,CoordSys*CS

    Positional fields with string coordinate system (ENU/XYZ/BEAM).

    Example:
        >>> sentence = "$PNORI1,4,123456,4,30,1.00,5.00,BEAM*5B"
        >>> config = PNORI1.from_nmea(sentence)
        >>> config.coordinate_system
        <CoordinateSystem.BEAM: 'BEAM'>

    """

    instrument_type: InstrumentType
    head_id: str
    beam_count: int | None
    cell_count: int | None
    blanking_distance: float | None
    cell_size: float | None
    coordinate_system: CoordinateSystem
    checksum: str | None = field(default=None, repr=False)

    HEAD_ID_PATTERN: ClassVar[re.Pattern] = re.compile(r"^\d{1,20}$")

    def __post_init__(self) -> None:
        """Validate all fields after initialization."""
        _validate_head_id(self.head_id, 20, numeric_only=True)
        _validate_beam_count(self.instrument_type, self.beam_count)
        _validate_cell_count(self.cell_count)
        _validate_distance(self.blanking_distance, "Blanking distance")
        _validate_distance(self.cell_size, "Cell size")

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORI1":
        """Parse PNORI1 message from NMEA sentence.

        Args:
            sentence: NMEA sentence string (with or without checksum)

        Returns:
            Parsed PNORI1 configuration object

        Raises:
            ValueError: If sentence format is invalid or fields fail validation

        """
        fields, checksum = parse_nmea_sentence(sentence)
        if len(fields) != 8:
            raise ValueError(f"Expected 8 fields, got {len(fields)}")
        if fields[0] != "$PNORI1":
            raise ValueError(f"Invalid prefix: expected $PNORI1, got {fields[0]}")

        # Parse and validate (coordinate system is string)
        return cls(
            instrument_type=InstrumentType.from_code(int(fields[1])),
            head_id=fields[2],
            beam_count=int(fields[3]) if fields[3] and fields[3].lower() != "nan" else None,
            cell_count=int(fields[4]) if fields[4] and fields[4].lower() != "nan" else None,
            blanking_distance=parse_optional_float(fields[5]),
            cell_size=parse_optional_float(fields[6]),
            coordinate_system=CoordinateSystem.from_code(fields[7]),
            checksum=checksum,
        )

    def to_nmea(self, include_checksum: bool = True) -> str:
        """Serialize to NMEA sentence format.

        Args:
            include_checksum: If True, compute and append checksum

        Returns:
            NMEA sentence string

        """
        sentence = (
            f"$PNORI1,{self.instrument_type.value},{self.head_id},"
            f"{self.beam_count},{self.cell_count},"
            f"{self.blanking_distance:.2f},{self.cell_size:.2f},"
            f"{self.coordinate_system.value}"
        )

        if include_checksum:
            checksum = compute_checksum(sentence)
            sentence = f"{sentence}*{checksum}"

        return sentence

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for database insertion.

        Returns:
            Dictionary with all fields mapped to database column names

        """
        return {
            "sentence_type": "PNORI1",
            "instrument_type_name": self.instrument_type.name,
            "instrument_type_code": self.instrument_type.value,
            "head_id": self.head_id,
            "beam_count": self.beam_count,
            "cell_count": self.cell_count,
            "blanking_distance": float(self.blanking_distance)
            if self.blanking_distance is not None
            else None,
            "cell_size": float(self.cell_size) if self.cell_size is not None else None,
            "coord_system_name": self.coordinate_system.value,
            "coord_system_code": self.coordinate_system.to_numeric_code(),
            "checksum": self.checksum,
        }


class PNORITag:
    """Tag definitions for PNORI2 format."""

    INSTRUMENT_TYPE = "IT"
    SERIAL_NUMBER = "SN"
    NUM_BEAMS = "NB"
    NUM_CELLS = "NC"
    BLANKING_DISTANCE = "BD"
    CELL_SIZE = "CS"
    COORDINATE_SYSTEM = "CY"

    VALID_TAGS = {
        INSTRUMENT_TYPE,
        SERIAL_NUMBER,
        NUM_BEAMS,
        NUM_CELLS,
        BLANKING_DISTANCE,
        CELL_SIZE,
        COORDINATE_SYSTEM,
    }

    @classmethod
    def parse_tagged_field(cls, field_str: str) -> tuple[str, str]:
        """Parse a TAG=VALUE field.

        Args:
            field_str: Tagged field string (e.g., "IT=4")

        Returns:
            Tuple of (tag, value)

        Raises:
            ValueError: If field format is invalid

        """
        if "=" not in field_str:
            raise ValueError(f"Tagged field must contain '=': {field_str}")

        tag, value = field_str.split("=", 1)
        return tag.strip().upper(), value.strip()


@dataclass(frozen=True)
class PNORI2:
    """PNORI2 configuration message parser.

    Format: $PNORI2,IT=InstrType,SN=HeadID,NB=BeamCnt,NC=CellCnt,
            BD=BlankDist,CS=CellSize,CY=CoordSys*CS

    Tagged fields (order-independent) with string coordinate system.

    Example:
        >>> sentence = "$PNORI2,IT=4,SN=123456,NB=4,NC=30,BD=1.00,CS=5.00,CY=BEAM*68"
        >>> config = PNORI2.from_nmea(sentence)
        >>> config.head_id
        '123456'

    """

    instrument_type: InstrumentType
    head_id: str
    beam_count: int | None
    cell_count: int | None
    blanking_distance: float | None
    cell_size: float | None
    coordinate_system: CoordinateSystem
    checksum: str | None = field(default=None, repr=False)

    HEAD_ID_PATTERN: ClassVar[re.Pattern] = re.compile(r"^\d{1,20}$")

    def __post_init__(self) -> None:
        """Validate all fields after initialization."""
        _validate_head_id(self.head_id, 20, numeric_only=True)
        _validate_beam_count(self.instrument_type, self.beam_count)
        _validate_cell_count(self.cell_count)
        _validate_distance(self.blanking_distance, "Blanking distance")
        _validate_distance(self.cell_size, "Cell size")

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORI2":
        """Parse from NMEA sentence.

        Args:
            sentence: NMEA sentence string

        Returns:
            PNORI2 object

        Raises:
            ValueError: If sentence format is invalid or fields fail validation

        """
        fields, checksum = parse_nmea_sentence(sentence)
        if len(fields) < 8:
            raise ValueError(f"Expected at least 8 fields, got {len(fields)}")
        if fields[0] != "$PNORI2":
            raise ValueError(f"Invalid prefix: {fields[0]}")

        # Parse tagged fields
        data: dict[str, Any] = {}
        for i in range(1, len(fields)):
            field_str = fields[i]
            tag, value = PNORITag.parse_tagged_field(field_str)
            if tag not in PNORITag.VALID_TAGS:
                raise ValueError(f"Unknown tag in PNORI2: {tag}")
            if tag in data:
                raise ValueError(f"Duplicate tag: {tag}")
            data[tag] = value

        # Parse and validate
        return cls(
            instrument_type=InstrumentType.from_code(int(data[PNORITag.INSTRUMENT_TYPE])),
            head_id=data[PNORITag.SERIAL_NUMBER],
            beam_count=int(data[PNORITag.NUM_BEAMS])
            if data[PNORITag.NUM_BEAMS] and data[PNORITag.NUM_BEAMS].lower() != "nan"
            else None,
            cell_count=int(data[PNORITag.NUM_CELLS])
            if data[PNORITag.NUM_CELLS] and data[PNORITag.NUM_CELLS].lower() != "nan"
            else None,
            blanking_distance=parse_optional_float(data[PNORITag.BLANKING_DISTANCE]),
            cell_size=parse_optional_float(data[PNORITag.CELL_SIZE]),
            coordinate_system=CoordinateSystem.from_code(data[PNORITag.COORDINATE_SYSTEM]),
            checksum=checksum,
        )

    def to_nmea(self, include_checksum: bool = True) -> str:
        """Serialize to NMEA sentence format.

        Args:
            include_checksum: If True, compute and append checksum

        Returns:
            NMEA sentence string with tags in canonical order

        """
        sentence = (
            f"$PNORI2,IT={self.instrument_type.value},SN={self.head_id},"
            f"NB={self.beam_count},NC={self.cell_count},"
            f"BD={self.blanking_distance:.2f},CS={self.cell_size:.2f},"
            f"CY={self.coordinate_system.value}"
        )

        if include_checksum:
            checksum = compute_checksum(sentence)
            sentence = f"{sentence}*{checksum}"

        return sentence

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for database insertion.

        Returns:
            Dictionary with all fields mapped to database column names

        """
        return {
            "sentence_type": "PNORI2",
            "instrument_type_name": self.instrument_type.name,
            "instrument_type_code": self.instrument_type.value,
            "head_id": self.head_id,
            "beam_count": self.beam_count,
            "cell_count": self.cell_count,
            "blanking_distance": float(self.blanking_distance)
            if self.blanking_distance is not None
            else None,
            "cell_size": float(self.cell_size) if self.cell_size is not None else None,
            "coord_system_name": self.coordinate_system.value,
            "coord_system_code": self.coordinate_system.to_numeric_code(),
            "checksum": self.checksum,
        }
