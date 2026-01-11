"""PNORE wave energy density spectrum message parser."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .utils import (
    validate_date_string,
    validate_time_string,
    validate_range,
)


@dataclass(frozen=True)
class PNORE:
    """PNORE wave energy density spectrum message.
    
    Format: $PNORE,<date>,<time>,<spectrum_basis>,<start_freq>,
            <step_freq>,<num_freq>,<energy1>,<energy2>,...,<energyN>*CS
    
    Used in Waves mode (DF=501) to transmit spectral energy density values.
    """
    date: str
    time: str
    spectrum_basis: int  # 0=Pressure, 1=Velocity, 3=AST
    start_frequency: float  # Hz
    step_frequency: float  # Hz
    num_frequencies: int
    energy_densities: List[float]  # Variable length array (cm²/Hz)
    checksum: Optional[str] = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_string(self.date)
        validate_time_string(self.time)
        
        # Validate spectrum basis
        if self.spectrum_basis not in (0, 1, 3):
            raise ValueError(
                f"Invalid spectrum basis: {self.spectrum_basis}. "
                f"Must be 0 (Pressure), 1 (Velocity), or 3 (AST)"
            )
        
        validate_range(self.start_frequency, "Start frequency", 0.0, 10.0)
        validate_range(self.step_frequency, "Step frequency", 0.0, 10.0)
        validate_range(self.num_frequencies, "Number of frequencies", 1, 99)
        
        # Validate energy array length matches num_frequencies
        if len(self.energy_densities) != self.num_frequencies:
            raise ValueError(
                f"Energy density count mismatch: expected {self.num_frequencies}, "
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
        
        # Minimum: $PNORE + 6 header fields + at least 1 energy value
        if len(fields) < 8:
            raise ValueError(
                f"Expected at least 8 fields for PNORE, got {len(fields)}"
            )
        
        if fields[0] != "$PNORE":
            raise ValueError(f"Invalid prefix: {fields[0]}")
        
        # Parse header fields
        date = fields[1]
        time = fields[2]
        spectrum_basis = int(fields[3])
        start_frequency = float(fields[4])
        step_frequency = float(fields[5])
        num_frequencies = int(fields[6])
        
        # Parse energy density array (fields 7 onwards)
        energy_densities = []
        for i in range(7, 7 + num_frequencies):
            if i >= len(fields):
                raise ValueError(
                    f"Missing energy density at index {i-7}: "
                    f"expected {num_frequencies} values, "
                    f"but sentence only has {len(fields)-7} data fields"
                )
            energy_densities.append(float(fields[i]))
        
        return cls(
            date=date,
            time=time,
            spectrum_basis=spectrum_basis,
            start_frequency=start_frequency,
            step_frequency=step_frequency,
            num_frequencies=num_frequencies,
            energy_densities=energy_densities,
            checksum=checksum
        )

    def to_dict(self) -> Dict:
        return {
            "sentence_type": "PNORE",
            "date": self.date,
            "time": self.time,
            "spectrum_basis": self.spectrum_basis,
            "start_frequency": self.start_frequency,
            "step_frequency": self.step_frequency,
            "num_frequencies": self.num_frequencies,
            "energy_densities": self.energy_densities,
            "checksum": self.checksum
        }
