"""PNORF Fourier coefficient spectra message parser (DF=501)."""

from dataclasses import dataclass, field

from .utils import (
    parse_optional_float,
    validate_date_mm_dd_yy,
    validate_range,
    validate_time_string,
)


@dataclass(frozen=True)
class PNORF:
    """PNORF Fourier coefficient spectra message (DF=501).
    Format: $PNORF,Flag,Date,Time,Basis,Start,Step,Num,C1,C2,...,CN*CS
    """

    coefficient_flag: str  # A1, B1, A2, B2
    date: str
    time: str
    spectrum_basis: int
    start_frequency: float
    step_frequency: float
    num_frequencies: int
    coefficients: list[float | None]
    checksum: str | None = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_mm_dd_yy(self.date)
        validate_time_string(self.time)
        if self.coefficient_flag not in ("A1", "B1", "A2", "B2"):
            raise ValueError(f"Invalid coefficient flag: {self.coefficient_flag}")
        if self.spectrum_basis not in {0, 1, 3}:
            raise ValueError(f"Invalid spectrum basis: {self.spectrum_basis}")
        validate_range(self.start_frequency, "Start frequency", 0.0, 10.0)
        validate_range(self.step_frequency, "Step frequency", 0.0, 10.0)
        validate_range(self.num_frequencies, "Number of frequencies", 1, 999)

        if len(self.coefficients) != self.num_frequencies:
            raise ValueError(
                f"Coefficient count mismatch: expected {self.num_frequencies}, "
                f"got {len(self.coefficients)}"
            )

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORF":
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()

        fields = [f.strip() for f in data_part.split(",")]
        if len(fields) < 9:
            raise ValueError(f"Expected at least 9 fields for PNORF, got {len(fields)}")
        if fields[0] != "$PNORF":
            raise ValueError(f"Invalid prefix: {fields[0]}")

        num_freq = int(fields[7])
        if len(fields) < 8 + num_freq:
            raise ValueError(
                f"Missing coefficient values: expected {num_freq}, got {len(fields) - 8}"
            )

        coeffs = [parse_optional_float(fields[i]) for i in range(8, 8 + num_freq)]

        return cls(
            coefficient_flag=fields[1],
            date=fields[2],
            time=fields[3],
            spectrum_basis=int(fields[4]),
            start_frequency=float(fields[5]),
            step_frequency=float(fields[6]),
            num_frequencies=num_freq,
            coefficients=coeffs,
            checksum=checksum,
        )

    def to_dict(self) -> dict:
        return {
            "sentence_type": "PNORF",
            "coefficient_flag": self.coefficient_flag,
            "date": self.date,
            "time": self.time,
            "spectrum_basis": self.spectrum_basis,
            "start_frequency": self.start_frequency,
            "step_frequency": self.step_frequency,
            "num_frequencies": self.num_frequencies,
            "coefficients": self.coefficients,
            "checksum": self.checksum,
        }
