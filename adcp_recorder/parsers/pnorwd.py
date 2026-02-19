"""PNORWD wave directional spectra message parser (DF=501)."""

from dataclasses import dataclass, field

from .utils import (
    parse_nmea_sentence,
    parse_optional_float,
    parse_optional_int,
    validate_date_mm_dd_yy,
    validate_range,
    validate_time_string,
)


@dataclass(frozen=True)
class PNORWD:
    """PNORWD wave directional spectra message (DF=501).
    Format: $PNORWD,DirType,Date,Time,Basis,Start,Step,Num,V1,V2,...,VN*CS
    """

    direction_type: str  # MD or DS
    date: str
    time: str
    spectrum_basis: int | None
    start_frequency: float | None
    step_frequency: float | None
    num_frequencies: int | None
    values: list[float | None]
    is_valid: bool = True
    checksum: str | None = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_mm_dd_yy(self.date)
        validate_time_string(self.time)
        if self.direction_type not in ("MD", "DS"):
            raise ValueError(f"Invalid direction type: {self.direction_type}")
        if self.spectrum_basis is not None:
            if self.spectrum_basis not in {0, 1, 3}:
                raise ValueError(f"Invalid spectrum basis: {self.spectrum_basis}")
        if self.start_frequency is not None:
            validate_range(self.start_frequency, "Start frequency", 0.0, 10.0)
        if self.step_frequency is not None:
            validate_range(self.step_frequency, "Step frequency", 0.0, 10.0)
        if self.num_frequencies is not None:
            validate_range(self.num_frequencies, "Number of frequencies", 1, 999)

        if self.num_frequencies is not None:
            if len(self.values) != self.num_frequencies:
                raise ValueError(
                    f"Value count mismatch: expected {self.num_frequencies}, got {len(self.values)}"
                )

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORWD":
        fields, checksum = parse_nmea_sentence(sentence)
        if len(fields) < 8:  # Basic header fields
            raise ValueError(f"Expected at least 8 fields for PNORWD, got {len(fields)}")
        if fields[0] != "$PNORWD":
            raise ValueError(f"Invalid prefix: {fields[0]}")

        _p = "PNORWD"
        num_freq = parse_optional_int(fields[7]) or 0

        # Values start from index 8
        vals: list[float | None] = []
        for i in range(8, len(fields)):
            vals.append(parse_optional_float(fields[i]))

        return cls(
            direction_type=fields[1],
            date=fields[2],
            time=fields[3],
            spectrum_basis=parse_optional_int(fields[4]),
            start_frequency=parse_optional_float(fields[5]),
            step_frequency=parse_optional_float(fields[6]),
            num_frequencies=num_freq if num_freq > 0 else None,
            values=vals,
            is_valid=True,
            checksum=checksum,
        )

    def to_dict(self) -> dict:
        return {
            "sentence_type": "PNORWD",
            "direction_type": self.direction_type,
            "date": self.date,
            "time": self.time,
            "spectrum_basis": self.spectrum_basis,
            "start_frequency": self.start_frequency,
            "step_frequency": self.step_frequency,
            "num_frequencies": self.num_frequencies,
            "values": self.values,
            "is_valid": self.is_valid,
            "checksum": self.checksum,
        }
