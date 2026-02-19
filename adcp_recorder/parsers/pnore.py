"""PNORE wave energy density spectrum message parser (DF=501)."""

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
class PNORE:
    """PNORE wave energy density spectrum message (DF=501).
    Format: $PNORE,Date,Time,Basis,Start,Step,Num,E1,E2,...,EN*CS
    """

    date: str
    time: str
    spectrum_basis: int | None
    start_frequency: float | None
    step_frequency: float | None
    num_frequencies: int | None
    energy_densities: list[float | None]
    is_valid: bool = True
    checksum: str | None = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_mm_dd_yy(self.date)
        validate_time_string(self.time)
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
            if len(self.energy_densities) != self.num_frequencies:
                raise ValueError(
                    f"Missing energy density values: expected {self.num_frequencies}, "
                    f"got {len(self.energy_densities)}"
                )

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORE":
        fields, checksum = parse_nmea_sentence(sentence)
        if fields[0] != "$PNORE":
            raise ValueError(f"Invalid prefix: {fields[0]}")

        # Check for DF=101 or DF=100
        # Wait, PNORE only implements DF=101/100 as energy density
        # For DF=101, it includes spectral basis

        # Determine format based on number of fields
        # DF=100: $PNORE,YYMMDD,HHMMSS,E1,E2,...
        # DF=101: $PNORE,YYMMDD,HHMMSS,SpectrumBasis,StartFreq,StepFreq,NumFreq,E1,E2,...

        # Actually our implementation expects the DF=101 format:
        # fields: YYMMDD, HHMMSS, Basis, Start, Step, Num
        if len(fields) < 7:
            raise ValueError(f"Expected at least 7 fields for PNORE, got {len(fields)}")

        num_freq = parse_optional_int(fields[6]) or 0

        # Energy densities start from index 7
        energies = [parse_optional_float(fields[i]) for i in range(7, len(fields))]

        return cls(
            date=fields[1],
            time=fields[2],
            spectrum_basis=parse_optional_int(fields[3]),
            start_frequency=parse_optional_float(fields[4]),
            step_frequency=parse_optional_float(fields[5]),
            num_frequencies=num_freq if num_freq > 0 else None,
            energy_densities=energies,
            is_valid=True,
            checksum=checksum,
        )

    def to_dict(self) -> dict:
        return {
            "sentence_type": "PNORE",
            "date": self.date,
            "time": self.time,
            "spectrum_basis": self.spectrum_basis,
            "start_frequency": self.start_frequency,
            "step_frequency": self.step_frequency,
            "num_frequencies": self.num_frequencies,
            "energy_densities": self.energy_densities,
            "is_valid": self.is_valid,
            "checksum": self.checksum,
        }
