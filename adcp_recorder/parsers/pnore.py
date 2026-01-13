"""PNORE wave energy density spectrum message parser (DF=501)."""

from dataclasses import dataclass, field

from .utils import (
    parse_optional_float,
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
    spectrum_basis: int
    start_frequency: float
    step_frequency: float
    num_frequencies: int
    energy_densities: list[float | None]
    checksum: str | None = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_mm_dd_yy(self.date)
        validate_time_string(self.time)
        if self.spectrum_basis not in {0, 1, 3}:
            raise ValueError(f"Invalid spectrum basis: {self.spectrum_basis}")
        validate_range(self.start_frequency, "Start frequency", 0.0, 10.0)
        validate_range(self.step_frequency, "Step frequency", 0.0, 10.0)
        validate_range(self.num_frequencies, "Number of frequencies", 1, 99)

        if len(self.energy_densities) != self.num_frequencies:
            raise ValueError(
                f"Missing energy density values: expected {self.num_frequencies}, "
                f"got {len(self.energy_densities)}"
            )

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORE":
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()

        fields = [f.strip() for f in data_part.split(",")]
        if len(fields) < 8:
            raise ValueError(f"Expected at least 8 fields for PNORE, got {len(fields)}")
        if fields[0] != "$PNORE":
            raise ValueError(f"Invalid prefix: {fields[0]}")

        num_freq = int(fields[6])
        if len(fields) < 7 + num_freq:
            raise ValueError(
                f"Missing energy density values: expected {num_freq}, got {len(fields) - 7}"
            )

        energies = [parse_optional_float(fields[i]) for i in range(7, 7 + num_freq)]

        return cls(
            date=fields[1],
            time=fields[2],
            spectrum_basis=int(fields[3]),
            start_frequency=float(fields[4]),
            step_frequency=float(fields[5]),
            num_frequencies=num_freq,
            energy_densities=energies,
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
            "checksum": self.checksum,
        }
