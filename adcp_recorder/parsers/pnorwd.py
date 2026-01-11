"""PNORWD wave directional spectra message parser."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .utils import (
    validate_date_string,
    validate_time_string,
    validate_range,
)


@dataclass(frozen=True)
class PNORWD:
    """PNORWD wave directional spectra message.
    
    Format: $PNORWD,<dir_type>,<date>,<time>,<spectrum_basis>,<start_freq>,
            <step_freq>,<num_freq>,<value1>,<value2>,...,<valueN>*CS
    
    Used in Waves mode (DF=501) to transmit directional information.
    Two separate sentences: MD (Main Direction) and DS (Directional Spread).
    """
    direction_type: str  # MD or DS
    date: str
    time: str
    spectrum_basis: int  # 0=Pressure, 1=Velocity, 3=AST
    start_frequency: float  # Hz
    step_frequency: float  # Hz
    num_frequencies: int
    values: List[float]  # Variable length array (degrees)
    checksum: Optional[str] = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_string(self.date)
        validate_time_string(self.time)
        
        # Validate direction type
        if self.direction_type not in ('MD', 'DS'):
            raise ValueError(
                f"Invalid direction type: {self.direction_type}. "
                f"Must be MD (Main Direction) or DS (Directional Spread)"
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
        
        # Validate values array length matches num_frequencies
        if len(self.values) != self.num_frequencies:
            raise ValueError(
                f"Value count mismatch: expected {self.num_frequencies}, "
                f"got {len(self.values)}"
            )

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORWD":
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()
        
        fields = [f.strip() for f in data_part.split(",")]
        
        # Minimum: $PNORWD + 7 header fields + at least 1 value
        if len(fields) < 9:
            raise ValueError(
                f"Expected at least 9 fields for PNORWD, got {len(fields)}"
            )
        
        if fields[0] != "$PNORWD":
            raise ValueError(f"Invalid prefix: {fields[0]}")
        
        # Parse header fields
        direction_type = fields[1]
        date = fields[2]
        time = fields[3]
        spectrum_basis = int(fields[4])
        start_frequency = float(fields[5])
        step_frequency = float(fields[6])
        num_frequencies = int(fields[7])
        
        # Parse values array (fields 8 onwards)
        values = []
        for i in range(8, 8 + num_frequencies):
            if i >= len(fields):
                raise ValueError(
                    f"Missing value at index {i-8}: "
                    f"expected {num_frequencies} values, "
                    f"but sentence only has {len(fields)-8} data fields"
                )
            values.append(float(fields[i]))
        
        return cls(
            direction_type=direction_type,
            date=date,
            time=time,
            spectrum_basis=spectrum_basis,
            start_frequency=start_frequency,
            step_frequency=step_frequency,
            num_frequencies=num_frequencies,
            values=values,
            checksum=checksum
        )

    def to_dict(self) -> Dict:
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
            "checksum": self.checksum
        }
