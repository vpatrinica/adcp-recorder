"""PNORC family parsers for current velocity data messages.

Implements parsers for:
- PNORC: Base current velocity (DF=100)
- PNORC1: Current velocity with correlation (DF=101)
- PNORC2: Tagged current velocity (DF=102)
- PNORC3: Tagged averaged current (DF=103)
- PNORC4: Positional averaged current (DF=104)
"""

from dataclasses import dataclass, field
from typing import Any

from .utils import (
    parse_nmea_sentence,
    parse_optional_float,
    parse_optional_int,
    parse_tagged_field,
    validate_date_mm_dd_yy,
    validate_range,
    validate_time_string,
)


def _validate_velocity(value: float | None, index: int) -> None:
    """Validate velocity component (-100 to +100 m/s, per dd.dd format)."""
    if value is not None:
        validate_range(value, f"Velocity {index}", -100.0, 100.0)


def _validate_correlation(value: int | None, index: int) -> None:
    """Validate correlation (0-100 counts/percent)."""
    if value is not None:
        validate_range(value, f"Correlation {index}", 0, 100)


def _validate_amplitude(value: float | None, index: int) -> None:
    """Validate amplitude (0-255 counts or dB)."""
    if value is not None:
        validate_range(value, f"Amplitude {index}", 0.0, 255.0)


def _validate_cell_index(value: int) -> None:
    """Validate cell index (1-1000)."""
    validate_range(value, "Cell index", 1, 1000)


def _validate_distance(value: float | None) -> None:
    """Validate distance (0-1000m)."""
    if value is not None:
        validate_range(value, "Distance", 0.0, 1000.0)


@dataclass(frozen=True)
class PNORC:
    """PNORC base current velocity message (DF=100).
    Format: $PNORC,MMDDYY,HHMMSS,Cell,Vel1,Vel2,Vel3,Vel4,Speed,Dir,
            AmpUnit,Amp1,Amp2,Amp3,Amp4,Corr1,Corr2,Corr3,Corr4*CS
    """

    date: str
    time: str
    cell_index: int
    vel1: float | None
    vel2: float | None
    vel3: float | None
    vel4: float | None
    speed: float | None
    direction: float | None
    amp_unit: str
    amp1: int | None
    amp2: int | None
    amp3: int | None
    amp4: int | None
    corr1: int | None
    corr2: int | None
    corr3: int | None
    corr4: int | None
    checksum: str | None = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_mm_dd_yy(self.date)
        validate_time_string(self.time)
        _validate_cell_index(self.cell_index)
        for i, v in enumerate([self.vel1, self.vel2, self.vel3, self.vel4], 1):
            _validate_velocity(v, i)
        if self.speed is not None:
            validate_range(self.speed, "Speed", 0.0, 100.0)
        if self.direction is not None:
            validate_range(self.direction, "Direction", 0.0, 360.0)
        if self.amp_unit not in {"C", "D"}:
            raise ValueError(f"Invalid amplitude unit: {self.amp_unit}")
        for i, a in enumerate([self.amp1, self.amp2, self.amp3, self.amp4], 1):
            _validate_amplitude(float(a) if a is not None else None, i)
        for i, c in enumerate([self.corr1, self.corr2, self.corr3, self.corr4], 1):
            _validate_correlation(c, i)

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORC":
        fields, checksum = parse_nmea_sentence(sentence)
        if len(fields) != 19:
            raise ValueError(f"Expected 19 fields for PNORC, got {len(fields)}")
        if fields[0] != "$PNORC":
            raise ValueError(f"Invalid prefix: {fields[0]}")

        _p = "PNORC"
        return cls(
            date=fields[1],
            time=fields[2],
            cell_index=int(fields[3]),
            vel1=parse_optional_float(fields[4]),
            vel2=parse_optional_float(fields[5]),
            vel3=parse_optional_float(fields[6]),
            vel4=parse_optional_float(fields[7]),
            speed=parse_optional_float(fields[8]),
            direction=parse_optional_float(fields[9]),
            amp_unit=fields[10],
            amp1=parse_optional_int(fields[11]),
            amp2=parse_optional_int(fields[12]),
            amp3=parse_optional_int(fields[13]),
            amp4=parse_optional_int(fields[14]),
            corr1=parse_optional_int(fields[15]),
            corr2=parse_optional_int(fields[16]),
            corr3=parse_optional_int(fields[17]),
            corr4=parse_optional_int(fields[18]),
            checksum=checksum,
        )

    def to_dict(self) -> dict:
        return {
            "sentence_type": "PNORC",
            "date": self.date,
            "time": self.time,
            "cell_index": self.cell_index,
            "vel1": self.vel1,
            "vel2": self.vel2,
            "vel3": self.vel3,
            "vel4": self.vel4,
            "speed": self.speed,
            "direction": self.direction,
            "amp_unit": self.amp_unit,
            "amp1": self.amp1,
            "amp2": self.amp2,
            "amp3": self.amp3,
            "amp4": self.amp4,
            "corr1": self.corr1,
            "corr2": self.corr2,
            "corr3": self.corr3,
            "corr4": self.corr4,
            "checksum": self.checksum,
        }


@dataclass(frozen=True)
class PNORC1:
    """PNORC1 current velocity data (DF=101).
    Same fields as DF=100 but amplitudes are dB.
    Includes cell distance.
    """

    date: str
    time: str
    cell_index: int
    distance: float | None
    vel1: float | None
    vel2: float | None
    vel3: float | None
    vel4: float | None
    amp1: float | None
    amp2: float | None
    amp3: float | None
    amp4: float | None
    corr1: int | None
    corr2: int | None
    corr3: int | None
    corr4: int | None
    checksum: str | None = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_mm_dd_yy(self.date)
        validate_time_string(self.time)
        _validate_cell_index(self.cell_index)
        _validate_distance(self.distance)
        for i, v in enumerate([self.vel1, self.vel2, self.vel3, self.vel4], 1):
            _validate_velocity(v, i)
        for i, a in enumerate([self.amp1, self.amp2, self.amp3, self.amp4], 1):
            _validate_amplitude(a, i)
        for i, c in enumerate([self.corr1, self.corr2, self.corr3, self.corr4], 1):
            _validate_correlation(c, i)

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORC1":
        fields, checksum = parse_nmea_sentence(sentence)
        if len(fields) != 17:
            raise ValueError(f"Expected 17 fields for PNORC1, got {len(fields)}")
        if fields[0] != "$PNORC1":
            raise ValueError(f"Invalid prefix: {fields[0]}")

        _p = "PNORC1"
        return cls(
            date=fields[1],
            time=fields[2],
            cell_index=int(fields[3]),
            distance=parse_optional_float(fields[4]),
            vel1=parse_optional_float(fields[5]),
            vel2=parse_optional_float(fields[6]),
            vel3=parse_optional_float(fields[7]),
            vel4=parse_optional_float(fields[8]),
            amp1=parse_optional_float(fields[9]),
            amp2=parse_optional_float(fields[10]),
            amp3=parse_optional_float(fields[11]),
            amp4=parse_optional_float(fields[12]),
            corr1=parse_optional_int(fields[13]),
            corr2=parse_optional_int(fields[14]),
            corr3=parse_optional_int(fields[15]),
            corr4=parse_optional_int(fields[16]),
            checksum=checksum,
        )

    def to_dict(self) -> dict:
        return {
            "sentence_type": "PNORC1",
            "date": self.date,
            "time": self.time,
            "cell_index": self.cell_index,
            "distance": self.distance,
            "vel1": self.vel1,
            "vel2": self.vel2,
            "vel3": self.vel3,
            "vel4": self.vel4,
            "amp1": self.amp1,
            "amp2": self.amp2,
            "amp3": self.amp3,
            "amp4": self.amp4,
            "corr1": self.corr1,
            "corr2": self.corr2,
            "corr3": self.corr3,
            "corr4": self.corr4,
            "checksum": self.checksum,
        }


@dataclass(frozen=True)
class PNORC2:
    """PNORC2 tagged current velocity message (DF=102).
    Format: $PNORC2,DATE=MMDDYY,TIME=HHMMSS,CN=Cell,CP=Dist,VE=Vel1,
            VN=Vel2,VU=Vel3,VU2=Vel4,A1=Amp1,A2=Amp2,A3=Amp3,A4=Amp4,
            C1=Corr1,C2=Corr2,C3=Corr3,C4=Corr4*CS
    Supports flexible velocity tags (VE/VN/VU/VU2, VX/VY/VZ/VZ2, V1/V2/V3/V4).
    """

    date: str
    time: str
    cell_index: int
    distance: float | None
    vel1: float | None
    vel2: float | None
    vel3: float | None
    vel4: float | None
    amp1: float | None
    amp2: float | None
    amp3: float | None
    amp4: float | None
    corr1: int | None
    corr2: int | None
    corr3: int | None
    corr4: int | None
    checksum: str | None = field(default=None, repr=False)

    TAG_GRP_VEL = {
        "VE": 1,
        "VN": 2,
        "VU": 3,
        "VU2": 4,
        "VX": 1,
        "VY": 2,
        "VZ": 3,
        "VZ2": 4,
        "V1": 1,
        "V2": 2,
        "V3": 3,
        "V4": 4,
    }
    TAG_GRP_AMP = {"A1": 1, "A2": 2, "A3": 3, "A4": 4}
    TAG_GRP_CORR = {"C1": 1, "C2": 2, "C3": 3, "C4": 4}

    def __post_init__(self):
        validate_date_mm_dd_yy(self.date)
        validate_time_string(self.time)
        _validate_cell_index(self.cell_index)
        _validate_distance(self.distance)
        for i, v in enumerate([self.vel1, self.vel2, self.vel3, self.vel4], 1):
            _validate_velocity(v, i)
        for i, a in enumerate([self.amp1, self.amp2, self.amp3, self.amp4], 1):
            _validate_amplitude(a, i)
        for i, c in enumerate([self.corr1, self.corr2, self.corr3, self.corr4], 1):
            _validate_correlation(c, i)

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORC2":
        fields, checksum = parse_nmea_sentence(sentence)
        if fields[0] != "$PNORC2":
            raise ValueError(f"Invalid prefix: {fields[0]}")

        _p = "PNORC2"
        data: dict[str, Any] = {}
        seen_tags = set()
        for i in range(1, len(fields)):
            field_str = fields[i]
            tag, val = parse_tagged_field(field_str)
            if tag in seen_tags:
                raise ValueError(f"Duplicate tag: {tag}")
            seen_tags.add(tag)

            if tag == "DATE":
                data["date"] = val
            elif tag == "TIME":
                data["time"] = val
            elif tag == "CN":
                data["cell_index"] = int(val)
            elif tag == "CP":
                data["distance"] = parse_optional_float(val)
            elif tag in cls.TAG_GRP_VEL:
                idx = cls.TAG_GRP_VEL[tag]
                data[f"vel{idx}"] = parse_optional_float(val)
            elif tag in cls.TAG_GRP_AMP:
                idx = cls.TAG_GRP_AMP[tag]
                data[f"amp{idx}"] = parse_optional_float(val)
            elif tag in cls.TAG_GRP_CORR:
                data[f"corr{cls.TAG_GRP_CORR[tag]}"] = parse_optional_int(val)
            else:
                raise ValueError(f"Unknown tags in PNORC2: {tag}")

        required = [
            "date",
            "time",
            "cell_index",
            "distance",
            "vel1",
            "vel2",
            "vel3",
            "vel4",
            "amp1",
            "amp2",
            "amp3",
            "amp4",
            "corr1",
            "corr2",
            "corr3",
            "corr4",
        ]
        # Allow missing optional fields as None
        for k in required:
            if k not in data:
                data[k] = None

        if data["date"] is None or data["time"] is None or data["cell_index"] is None:
            raise ValueError("Missing mandatory tags in PNORC2: DATE, TIME, or CN")

        return cls(**data, checksum=checksum)

    def to_dict(self) -> dict:
        return {
            "sentence_type": "PNORC2",
            "date": self.date,
            "time": self.time,
            "cell_index": self.cell_index,
            "distance": self.distance,
            "vel1": self.vel1,
            "vel2": self.vel2,
            "vel3": self.vel3,
            "vel4": self.vel4,
            "amp1": self.amp1,
            "amp2": self.amp2,
            "amp3": self.amp3,
            "amp4": self.amp4,
            "corr1": self.corr1,
            "corr2": self.corr2,
            "corr3": self.corr3,
            "corr4": self.corr4,
            "checksum": self.checksum,
        }


@dataclass(frozen=True)
class PNORC3:
    """PNORC3 tagged averaged current (DF=103).
    Format: $PNORC3,CP=Dist,SP=Speed,DIR=Dir,AA=AvgAmp,AC=AvgCorr*CS
    """

    distance: float | None
    speed: float | None
    direction: float | None
    avg_amplitude: int | None
    avg_correlation: int | None
    checksum: str | None = field(default=None, repr=False)

    TAG_IDS = {
        "CP": "distance",
        "SP": "speed",
        "DIR": "direction",
        "AA": "avg_amplitude",
        "AC": "avg_correlation",
    }

    def __post_init__(self):
        _validate_distance(self.distance)
        if self.speed is not None:
            validate_range(self.speed, "Speed", 0.0, 100.0)
        if self.direction is not None:
            validate_range(self.direction, "Direction", 0.0, 360.0)
        _validate_amplitude(
            float(self.avg_amplitude) if self.avg_amplitude is not None else None, 0
        )
        _validate_correlation(self.avg_correlation, 0)

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORC3":
        fields, checksum = parse_nmea_sentence(sentence)
        if fields[0] != "$PNORC3":
            raise ValueError(f"Invalid prefix: {fields[0]}")

        _p = "PNORC3"
        data: dict[str, Any] = {}
        for i in range(1, len(fields)):
            field_str = fields[i]
            tag, val = parse_tagged_field(field_str)
            if tag not in cls.TAG_IDS:
                raise ValueError(f"Unknown tags in PNORC3: {tag}")
            field_name = cls.TAG_IDS[tag]
            if field_name in ["avg_amplitude", "avg_correlation"]:
                data[field_name] = parse_optional_int(val)
            else:
                data[field_name] = parse_optional_float(val)

        # Allow missing fields as None
        for k in cls.TAG_IDS.values():
            if k not in data:
                data[k] = None

        return cls(**data, checksum=checksum)

    def to_dict(self) -> dict:
        return {
            "sentence_type": "PNORC3",
            "distance": self.distance,
            "speed": self.speed,
            "direction": self.direction,
            "avg_amplitude": self.avg_amplitude,
            "avg_correlation": self.avg_correlation,
            "checksum": self.checksum,
        }


@dataclass(frozen=True)
class PNORC4:
    """PNORC4 positional averaged current (DF=104).
    Format: $PNORC4,Dist,Speed,Dir,AC,AA*CS
    """

    distance: float | None
    speed: float | None
    direction: float | None
    avg_correlation: int | None
    avg_amplitude: int | None
    checksum: str | None = field(default=None, repr=False)

    def __post_init__(self):
        _validate_distance(self.distance)
        if self.speed is not None:
            validate_range(self.speed, "Speed", 0.0, 100.0)
        if self.direction is not None:
            validate_range(self.direction, "Direction", 0.0, 360.0)
        _validate_amplitude(
            float(self.avg_amplitude) if self.avg_amplitude is not None else None, 0
        )
        _validate_correlation(self.avg_correlation, 0)

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORC4":
        fields, checksum = parse_nmea_sentence(sentence)
        if len(fields) != 6:
            raise ValueError(f"Expected 6 fields for PNORC4, got {len(fields)}")
        if fields[0] != "$PNORC4":
            raise ValueError(f"Invalid prefix: {fields[0]}")

        _p = "PNORC4"
        return cls(
            distance=parse_optional_float(fields[1]),
            speed=parse_optional_float(fields[2]),
            direction=parse_optional_float(fields[3]),
            avg_correlation=parse_optional_int(fields[4]),
            avg_amplitude=parse_optional_int(fields[5]),
            checksum=checksum,
        )

    def to_dict(self) -> dict:
        return {
            "sentence_type": "PNORC4",
            "distance": self.distance,
            "speed": self.speed,
            "direction": self.direction,
            "avg_amplitude": self.avg_amplitude,
            "avg_correlation": self.avg_correlation,
            "checksum": self.checksum,
        }
