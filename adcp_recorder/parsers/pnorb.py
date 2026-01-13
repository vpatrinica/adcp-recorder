"""PNORB wave band parameters message parser (DF=501)."""

from dataclasses import dataclass, field

from .utils import (
    parse_optional_float,
    validate_date_mm_dd_yy,
    validate_range,
    validate_time_string,
)


@dataclass(frozen=True)
class PNORB:
    """PNORB wave band parameters message (DF=501).
    Format: $PNORB,Date,Time,Basis,Method,FreqLow,FreqHigh,Hm0,Tm02,Tp,
            DirTp,SprTp,MainDir,ErrorCode*CS
    """

    date: str
    time: str
    spectrum_basis: int
    processing_method: int
    freq_low: float
    freq_high: float
    hm0: float | None
    tm02: float | None
    tp: float | None
    dir_tp: float | None
    spr_tp: float | None
    main_dir: float | None
    wave_error_code: str  # 4 hex digits
    checksum: str | None = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_mm_dd_yy(self.date)
        validate_time_string(self.time)
        validate_range(self.spectrum_basis, "Spectrum basis", 0, 3)
        validate_range(self.processing_method, "Processing method", 1, 4)
        validate_range(self.freq_low, "Frequency low", 0.0, 10.0)
        validate_range(self.freq_high, "Frequency high", 0.0, 10.0)
        if self.hm0 is not None:
            validate_range(self.hm0, "Hm0", 0.0, 100.0)
        if self.tm02 is not None:
            validate_range(self.tm02, "Tm02", 0.0, 100.0)
        if self.tp is not None:
            validate_range(self.tp, "Tp", 0.0, 100.0)

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
            hm0=parse_optional_float(fields[7]),
            tm02=parse_optional_float(fields[8]),
            tp=parse_optional_float(fields[9]),
            dir_tp=parse_optional_float(fields[10]),
            spr_tp=parse_optional_float(fields[11]),
            main_dir=parse_optional_float(fields[12]),
            wave_error_code=fields[13],
            checksum=checksum,
        )

    def to_dict(self) -> dict:
        return {
            "sentence_type": "PNORB",
            "date": self.date,
            "time": self.time,
            "spectrum_basis": self.spectrum_basis,
            "processing_method": self.processing_method,
            "freq_low": self.freq_low,
            "freq_high": self.freq_high,
            "hm0": self.hm0,
            "tm02": self.tm02,
            "tp": self.tp,
            "dir_tp": self.dir_tp,
            "spr_tp": self.spr_tp,
            "main_dir": self.main_dir,
            "wave_error_code": self.wave_error_code,
            "checksum": self.checksum,
        }
