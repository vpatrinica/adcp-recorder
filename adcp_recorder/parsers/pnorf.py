"""PNORF Fourier coefficient spectra message parser."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .utils import (
    validate_date_string,
    validate_time_string,
    validate_range,
)


@dataclass(frozen=True)
class PNORF:
    """PNORF Fourier coefficient spectra message.
    
    Format: $PNORF,<coeff_flag>,<date>,<time>,<spectrum_basis>,<start_freq>,
            <step_freq>,<num_freq>,<coeff1>,<coeff2>,...,<coeffN>*CS
    
    Used in Waves mode (DF=501) to transmit directional Fourier coefficients.
    Four separate sentences are sent for A1, B1, A2, B2 coefficients.
    """
    coefficient_flag: str  # A1, B1, A2, B2
    date: str
    time: str
    spectrum_basis: int  # 0=Pressure, 1=Velocity, 3=AST
    start_frequency: float  # Hz
    step_frequency: float  # Hz
    num_frequencies: int
    coefficients: List[float]  # Variable length array
    checksum: Optional[str] = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_string(self.date)
        validate_time_string(self.time)
        
        # Validate coefficient flag
        if self.coefficient_flag not in ('A1', 'B1', 'A2', 'B2'):
            raise ValueError(
                f"Invalid coefficient flag: {self.coefficient_flag}. "
                f"Must be A1, B1, A2, or B2"
            )
        
        # Validate spectrum basis
        if self.spectrum_basis not in (0, 1, 3):
            raise ValueError(
                f"Invalid spectrum basis: {self.spectrum_basis}. "
                f"Must be 0 (Pressure), 1 (Velocity), or 3 (AST)"
            )
        
        validate_range(self.start_frequency, "Start frequency", 0.0, 10.0)
        validate_range(self.step_frequency, "Step frequency", 0.0, 10.0)
        validate_range(self.num_frequencies, "Number of frequencies", 1, 999)
        
        # Validate coefficient array length matches num_frequencies
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
        
        # Minimum: $PNORF + 7 header fields + at least 1 coefficient
        if len(fields) < 9:
            raise ValueError(
                f"Expected at least 9 fields for PNORF, got {len(fields)}"
            )
        
        if fields[0] != "$PNORF":
            raise ValueError(f"Invalid prefix: {fields[0]}")
        
        # Parse header fields
        coefficient_flag = fields[1]
        date = fields[2]
        time = fields[3]
        spectrum_basis = int(fields[4])
        start_frequency = float(fields[5])
        step_frequency = float(fields[6])
        num_frequencies = int(fields[7])
        
        # Parse coefficient array (fields 8 onwards)
        coefficients = []
        for i in range(8, 8 + num_frequencies):
            if i >= len(fields):
                raise ValueError(
                    f"Missing coefficient at index {i-8}: "
                    f"expected {num_frequencies} coefficients, "
                    f"but sentence only has {len(fields)-8} data fields"
                )
            coefficients.append(float(fields[i]))
        
        return cls(
            coefficient_flag=coefficient_flag,
            date=date,
            time=time,
            spectrum_basis=spectrum_basis,
            start_frequency=start_frequency,
            step_frequency=step_frequency,
            num_frequencies=num_frequencies,
            coefficients=coefficients,
            checksum=checksum
        )

    def to_dict(self) -> Dict:
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
            "checksum": self.checksum
        }
