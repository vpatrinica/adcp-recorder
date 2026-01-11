"""PNORB wave band parameters message parser (DF=501)."""

from dataclasses import dataclass, field
from typing import Dict, Optional

from .utils import (
    validate_date_string,
    validate_time_string,
    validate_range,
)


@dataclass(frozen=True)
class PNORB:
    """PNORB wave band parameters message (DF=501).
    Format: $PNORB,<date>,<time>,<spectrum_basis>,<processing_method>,<freq_low>,<freq_high>,
            <hmo>,<tm02>,<tp>,<dirtp>,<sprtp>,<main_dir>,<wave_error_code>*CS
    """
    date: str
    time: str
    spectrum_basis: int  # 0=pressure, 1=velocity, 3=AST
    processing_method: int  # Processing method code
    freq_low: float  # Lower frequency limit (Hz)
    freq_high: float  # Upper frequency limit (Hz)
    hmo: float  # Significant wave height (m)
    tm02: float  # Mean zero-crossing period (s)
    tp: float  # Peak period (s)
    dirtp: float  # Direction at peak period (degrees)
    sprtp: float  # Spreading at peak period (degrees)
    main_dir: float  # Main direction (degrees)
    wave_error_code: str  # 4-digit error code
    checksum: Optional[str] = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_string(self.date)
        validate_time_string(self.time)
        validate_range(self.spectrum_basis, "Spectrum basis", 0, 3)
        validate_range(self.freq_low, "Frequency low", 0.0, 10.0)
        validate_range(self.freq_high, "Frequency high", 0.0, 10.0)
        validate_range(self.hmo, "Significant wave height", 0.0, 100.0)
        validate_range(self.tm02, "Mean period", 0.0, 100.0)
        validate_range(self.tp, "Peak period", 0.0, 100.0)
        validate_range(self.dirtp, "Direction at peak", 0.0, 360.0)
        validate_range(self.sprtp, "Spreading at peak", 0.0, 360.0)
        validate_range(self.main_dir, "Main direction", 0.0, 360.0)

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORB":
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()
        
        fields = [f.strip() for f in data_part.split(",")]
        if len(fields) != 14:
            raise ValueError(f"Expected 14 fields for PNORB, got {len(fields)}")
        if fields[0] != "$PNORB":
            raise ValueError(f"Invalid prefix: {fields[0]}")
            
        return cls(
            date=fields[1],
            time=fields[2],
            spectrum_basis=int(fields[3]),
            processing_method=int(fields[4]),
            freq_low=float(fields[5]),
            freq_high=float(fields[6]),
            hmo=float(fields[7]),
            tm02=float(fields[8]),
            tp=float(fields[9]),
            dirtp=float(fields[10]),
            sprtp=float(fields[11]),
            main_dir=float(fields[12]),
            wave_error_code=fields[13],
            checksum=checksum
        )

    def to_dict(self) -> Dict:
        return {
            "sentence_type": "PNORB",
            "date": self.date,
            "time": self.time,
            "spectrum_basis": self.spectrum_basis,
            "processing_method": self.processing_method,
            "freq_low": self.freq_low,
            "freq_high": self.freq_high,
            "hmo": self.hmo,
            "tm02": self.tm02,
            "tp": self.tp,
            "dirtp": self.dirtp,
            "sprtp": self.sprtp,
            "main_dir": self.main_dir,
            "wave_error_code": self.wave_error_code,
            "checksum": self.checksum
        }
