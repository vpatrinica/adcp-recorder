"""PNORW wave bulk parameters message parser (DF=501)."""

from dataclasses import dataclass, field

from .sentinels import get_float_sentinels as _fs
from .sentinels import get_int_sentinels as _is
from .utils import (
    parse_nmea_sentence,
    parse_optional_float,
    parse_optional_int,
    validate_date_mm_dd_yy,
    validate_range,
    validate_time_string,
)


@dataclass(frozen=True)
class PNORW:
    """PNORW wave parameters message (DF=501).
    Format: $PNORW,Date,Time,Basis,Method,Hm0,H3,H10,Hmax,Tm02,Tp,Tz,
            DirTp,SprTp,MainDir,UI,MeanPress,NoDetect,BadDetect,
            NSurfSpeed,NSurfDir,ErrorCode*CS
    """

    date: str
    time: str
    spectrum_basis: int | None
    processing_method: int | None
    hm0: float | None
    h3: float | None
    h10: float | None
    hmax: float | None
    tm02: float | None
    tp: float | None
    tz: float | None
    dir_tp: float | None
    spr_tp: float | None
    main_dir: float | None
    uni_index: float | None
    mean_pressure: float | None
    num_no_detects: int | None
    num_bad_detects: int | None
    near_surface_speed: float | None
    near_surface_dir: float | None
    wave_error_code: str  # 4 hex digits
    checksum: str | None = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_mm_dd_yy(self.date)
        validate_time_string(self.time)
        if self.spectrum_basis is not None:
            validate_range(self.spectrum_basis, "Spectrum basis", 0, 3)
        if self.processing_method is not None:
            validate_range(self.processing_method, "Processing method", 1, 4)
        if self.hm0 is not None:
            validate_range(self.hm0, "Hm0", 0.0, 999.99)
        if self.tm02 is not None:
            validate_range(self.tm02, "Tm02", 0.0, 999.99)
        if self.tp is not None:
            validate_range(self.tp, "Tp", 0.0, 999.99)
        if self.dir_tp is not None:
            validate_range(self.dir_tp, "DirTp", 0.0, 360.0)
        if self.spr_tp is not None:
            validate_range(self.spr_tp, "SprTp", 0.0, 360.0)
        if self.main_dir is not None:
            validate_range(self.main_dir, "MainDir", 0.0, 360.0)

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORW":
        fields, checksum = parse_nmea_sentence(sentence)
        if len(fields) != 22:
            raise ValueError(f"Expected 22 fields for PNORW, got {len(fields)}")
        if fields[0] != "$PNORW":
            raise ValueError(f"Invalid prefix: {fields[0]}")

        _p = "PNORW"
        return cls(
            date=fields[1],
            time=fields[2],
            spectrum_basis=parse_optional_int(fields[3]),
            processing_method=parse_optional_int(fields[4]),
            hm0=parse_optional_float(fields[5], _fs(_p, "hm0")),
            h3=parse_optional_float(fields[6], _fs(_p, "h3")),
            h10=parse_optional_float(fields[7], _fs(_p, "h10")),
            hmax=parse_optional_float(fields[8], _fs(_p, "hmax")),
            tm02=parse_optional_float(fields[9], _fs(_p, "tm02")),
            tp=parse_optional_float(fields[10], _fs(_p, "tp")),
            tz=parse_optional_float(fields[11], _fs(_p, "tz")),
            dir_tp=parse_optional_float(fields[12], _fs(_p, "dir_tp")),
            spr_tp=parse_optional_float(fields[13], _fs(_p, "spr_tp")),
            main_dir=parse_optional_float(fields[14], _fs(_p, "main_dir")),
            uni_index=parse_optional_float(fields[15], _fs(_p, "uni_index")),
            mean_pressure=parse_optional_float(fields[16], _fs(_p, "mean_pressure")),
            num_no_detects=parse_optional_int(fields[17], _is(_p, "num_no_detects")),
            num_bad_detects=parse_optional_int(fields[18], _is(_p, "num_bad_detects")),
            near_surface_speed=parse_optional_float(fields[19], _fs(_p, "near_surface_speed")),
            near_surface_dir=parse_optional_float(fields[20], _fs(_p, "near_surface_dir")),
            wave_error_code=fields[21],
            checksum=checksum,
        )

    def to_dict(self) -> dict:
        return {
            "sentence_type": "PNORW",
            "date": self.date,
            "time": self.time,
            "spectrum_basis": self.spectrum_basis,
            "processing_method": self.processing_method,
            "hm0": self.hm0,
            "h3": self.h3,
            "h10": self.h10,
            "hmax": self.hmax,
            "tm02": self.tm02,
            "tp": self.tp,
            "tz": self.tz,
            "dir_tp": self.dir_tp,
            "spr_tp": self.spr_tp,
            "main_dir": self.main_dir,
            "uni_index": self.uni_index,
            "mean_pressure": self.mean_pressure,
            "num_no_detects": self.num_no_detects,
            "num_bad_detects": self.num_bad_detects,
            "near_surface_speed": self.near_surface_speed,
            "near_surface_dir": self.near_surface_dir,
            "wave_error_code": self.wave_error_code,
            "checksum": self.checksum,
        }
