"""PNORC family parsers for current velocity data messages.

Implements parsers for:
- PNORC: Base current velocity (DF=100)
- PNORC1: Current velocity with correlation (DF=101)
- PNORC2: Tagged current velocity (DF=102)
- PNORC3: Tagged averaged current (DF=103)
- PNORC4: Positional averaged current (DF=104)
"""

from dataclasses import dataclass, field

from .utils import (
    parse_tagged_field,
    validate_date_mm_dd_yy,
    validate_range,
    validate_time_string,
)


def _validate_velocity(value: float, index: int) -> None:
    """Validate velocity component (-10 to +10 m/s)."""
    validate_range(value, f"Velocity {index}", -10.0, 10.0)


def _validate_correlation(value: int, index: int) -> None:
    """Validate correlation (0-100 counts/percent)."""
    validate_range(value, f"Correlation {index}", 0, 100)


def _validate_amplitude(value: float, index: int) -> None:
    """Validate amplitude (0-255 counts or dB)."""
    validate_range(value, f"Amplitude {index}", 0.0, 255.0)


def _validate_cell_index(value: int) -> None:
    """Validate cell index (1-1000)."""
    validate_range(value, "Cell index", 1, 1000)


def _validate_distance(value: float) -> None:
    """Validate distance (0-1000m)."""
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
    vel1: float
    vel2: float
    vel3: float
    vel4: float
    speed: float
    direction: float
    amp_unit: str
    amp1: int
    amp2: int
    amp3: int
    amp4: int
    corr1: int
    corr2: int
    corr3: int
    corr4: int
    checksum: str | None = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_mm_dd_yy(self.date)
        validate_time_string(self.time)
        _validate_cell_index(self.cell_index)
        for i, v in enumerate([self.vel1, self.vel2, self.vel3, self.vel4], 1):
            _validate_velocity(v, i)
        validate_range(self.speed, "Speed", 0.0, 100.0)
        validate_range(self.direction, "Direction", 0.0, 360.0)
        if self.amp_unit not in {"C", "D"}:
            raise ValueError(f"Invalid amplitude unit: {self.amp_unit}")
        for i, a in enumerate([self.amp1, self.amp2, self.amp3, self.amp4], 1):
            _validate_amplitude(float(a), i)
        for i, c in enumerate([self.corr1, self.corr2, self.corr3, self.corr4], 1):
            _validate_correlation(c, i)

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORC":
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()

        fields = [f.strip() for f in data_part.split(",")]
        if len(fields) != 19:
            raise ValueError(f"Expected 19 fields for PNORC, got {len(fields)}")
        if fields[0] != "$PNORC":
            raise ValueError(f"Invalid prefix: {fields[0]}")

        return cls(
            date=fields[1],
            time=fields[2],
            cell_index=int(fields[3]),
            vel1=float(fields[4]),
            vel2=float(fields[5]),
            vel3=float(fields[6]),
            vel4=float(fields[7]),
            speed=float(fields[8]),
            direction=float(fields[9]),
            amp_unit=fields[10],
            amp1=int(fields[11]),
            amp2=int(fields[12]),
            amp3=int(fields[13]),
            amp4=int(fields[14]),
            corr1=int(fields[15]),
            corr2=int(fields[16]),
            corr3=int(fields[17]),
            corr4=int(fields[18]),
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
    distance: float
    vel1: float
    vel2: float
    vel3: float
    vel4: float
    amp1: float
    amp2: float
    amp3: float
    amp4: float
    corr1: int
    corr2: int
    corr3: int
    corr4: int
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
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()

        fields = [f.strip() for f in data_part.split(",")]
        if len(fields) != 17:
            raise ValueError(f"Expected 17 fields for PNORC1, got {len(fields)}")
        if fields[0] != "$PNORC1":
            raise ValueError(f"Invalid prefix: {fields[0]}")

        return cls(
            date=fields[1],
            time=fields[2],
            cell_index=int(fields[3]),
            distance=float(fields[4]),
            vel1=float(fields[5]),
            vel2=float(fields[6]),
            vel3=float(fields[7]),
            vel4=float(fields[8]),
            amp1=float(fields[9]),
            amp2=float(fields[10]),
            amp3=float(fields[11]),
            amp4=float(fields[12]),
            corr1=int(fields[13]),
            corr2=int(fields[14]),
            corr3=int(fields[15]),
            corr4=int(fields[16]),
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
    distance: float
    vel1: float
    vel2: float
    vel3: float
    vel4: float
    amp1: float
    amp2: float
    amp3: float
    amp4: float
    corr1: int
    corr2: int
    corr3: int
    corr4: int
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
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()

        fields = [f.strip() for f in data_part.split(",")]
        if fields[0] != "$PNORC2":
            raise ValueError(f"Invalid prefix: {fields[0]}")

        data = {}
        seen_tags = set()
        for field_str in fields[1:]:
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
                data["distance"] = float(val)
            elif tag in cls.TAG_GRP_VEL:
                data[f"vel{cls.TAG_GRP_VEL[tag]}"] = float(val)
            elif tag in cls.TAG_GRP_AMP:
                data[f"amp{cls.TAG_GRP_AMP[tag]}"] = float(val)
            elif tag in cls.TAG_GRP_CORR:
                data[f"corr{cls.TAG_GRP_CORR[tag]}"] = int(val)
            else:
                raise ValueError(f"Unknown tag in PNORC2: {tag}")

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
        if not all(k in data for k in required):
            missing = set(required) - set(data.keys())
            raise ValueError(f"Missing required tags in PNORC2: {missing}")

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

    distance: float
    speed: float
    direction: float
    avg_amplitude: int
    avg_correlation: int
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
        validate_range(self.speed, "Speed", 0.0, 100.0)
        validate_range(self.direction, "Direction", 0.0, 360.0)
        _validate_amplitude(float(self.avg_amplitude), 0)
        _validate_correlation(self.avg_correlation, 0)

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORC3":
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()

        fields = [f.strip() for f in data_part.split(",")]
        if fields[0] != "$PNORC3":
            raise ValueError(f"Invalid prefix: {fields[0]}")

        data = {}
        for field_str in fields[1:]:
            tag, val = parse_tagged_field(field_str)
            if tag not in cls.TAG_IDS:
                raise ValueError(f"Unknown tag in PNORC3: {tag}")
            field_name = cls.TAG_IDS[tag]
            if field_name in ["avg_amplitude", "avg_correlation"]:
                data[field_name] = int(val)
            else:
                data[field_name] = float(val)

        if not all(k in data for k in cls.TAG_IDS.values()):
            missing = set(cls.TAG_IDS.values()) - set(data.keys())
            raise ValueError(f"Missing required tags in PNORC3: {missing}")

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

    distance: float
    speed: float
    direction: float
    avg_correlation: int
    avg_amplitude: int
    checksum: str | None = field(default=None, repr=False)

    def __post_init__(self):
        _validate_distance(self.distance)
        validate_range(self.speed, "Speed", 0.0, 100.0)
        validate_range(self.direction, "Direction", 0.0, 360.0)
        _validate_amplitude(float(self.avg_amplitude), 0)
        _validate_correlation(self.avg_correlation, 0)

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORC4":
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()

        fields = [f.strip() for f in data_part.split(",")]
        if len(fields) != 6:
            raise ValueError(f"Expected 6 fields for PNORC4, got {len(fields)}")
        if fields[0] != "$PNORC4":
            raise ValueError(f"Invalid prefix: {fields[0]}")

        return cls(
            distance=float(fields[1]),
            speed=float(fields[2]),
            direction=float(fields[3]),
            avg_correlation=int(fields[4]),
            avg_amplitude=int(fields[5]),
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
