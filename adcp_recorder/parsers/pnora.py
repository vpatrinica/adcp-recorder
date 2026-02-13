"""PNORA family parser for altitude/range data messages.

Implements parser for:
- PNORA: Altitude/range measurements (DF=200, 201)
"""

from dataclasses import dataclass, field

from .utils import (
    parse_optional_float,
    validate_date_yy_mm_dd,
    validate_hex_string,
    validate_range,
    validate_time_string,
)


@dataclass(frozen=True)
class PNORA:
    """PNORA altitude/range data message (DF=200, 201).
    Format: $PNORA,Date,Time,Pressure,Distance,Quality,Status,Pitch,Roll*CS
    """

    date: str
    time: str
    pressure: float | None
    distance: float | None
    quality: int | None
    status: str
    pitch: float | None
    roll: float | None
    checksum: str | None = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_yy_mm_dd(self.date)
        validate_time_string(self.time)
        if self.pressure is not None:
            validate_range(self.pressure, "Pressure", 0.0, 999.999)
        if self.distance is not None:
            validate_range(self.distance, "Distance", 0.0, 999.999)
        if self.pitch is not None:
            validate_range(self.pitch, "Pitch", -9.9, 9.9)
        if self.roll is not None:
            validate_range(self.roll, "Roll", -9.9, 9.9)
        validate_hex_string(self.status, 2, 2)

    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORA":
        sentence = sentence.strip()
        data_part, checksum = sentence, None
        if "*" in sentence:
            data_part, checksum = sentence.rsplit("*", 1)
            checksum = checksum.strip().upper()

        fields = [f.strip() for f in data_part.split(",")]
        if fields[0] != "$PNORA":
            raise ValueError(f"Invalid prefix: {fields[0]}")

        # Check for tagged format (DF=201) usage by looking for '=' in fields
        if any("=" in f for f in fields[1:]):
            data_map = {}
            for f in fields[1:]:
                if "=" in f:
                    key, value = f.split("=", 1)
                    data_map[key] = value

            # Check mandatory tags: DATE, TIME, ST are core. Others are optional in the dataclass
            required_tags = {"DATE", "TIME", "ST"}
            if not all(tag in data_map for tag in required_tags):
                missing = required_tags - set(data_map.keys())
                raise ValueError(f"Missing mandatory tags for PNORA DF=201: {missing}")

            try:
                return cls(
                    date=data_map["DATE"],
                    time=data_map["TIME"],
                    pressure=parse_optional_float(data_map.get("P", "")),
                    distance=parse_optional_float(data_map.get("A", "")),
                    quality=int(data_map["Q"]) if "Q" in data_map and data_map["Q"] else None,
                    status=data_map.get("ST", ""),
                    pitch=parse_optional_float(data_map.get("PI", "")),
                    roll=parse_optional_float(data_map.get("R", "")),
                    checksum=checksum,
                )
            except ValueError as e:
                raise ValueError(f"Invalid data type in PNORA DF=201: {e}")

        # Fallback to standard positional format (DF=200)
        if len(fields) != 9:
            raise ValueError(f"Expected 9 fields for PNORA, got {len(fields)}")

        return cls(
            date=fields[1],
            time=fields[2],
            pressure=parse_optional_float(fields[3]),
            distance=parse_optional_float(fields[4]),
            quality=int(fields[5]) if fields[5] else None,
            status=fields[6],
            pitch=parse_optional_float(fields[7]),
            roll=parse_optional_float(fields[8]),
            checksum=checksum,
        )

    def to_dict(self) -> dict:
        return {
            "sentence_type": "PNORA",
            "date": self.date,
            "time": self.time,
            "pressure": self.pressure,
            "distance": self.distance,
            "quality": self.quality,
            "status": self.status,
            "pitch": self.pitch,
            "roll": self.roll,
            "checksum": self.checksum,
        }
