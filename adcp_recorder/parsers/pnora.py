"""PNORA family parser for altitude/range data messages.

Implements parser for:
- PNORA: Altitude/range measurements (DF=200, 201)
"""

from dataclasses import dataclass, field

from .utils import (
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
    pressure: float
    distance: float
    quality: int
    status: str
    pitch: float
    roll: float
    checksum: str | None = field(default=None, repr=False)

    def __post_init__(self):
        validate_date_yy_mm_dd(self.date)
        validate_time_string(self.time)
        validate_range(self.pressure, "Pressure", 0.0, 20000.0)
        validate_range(self.distance, "Distance", 0.0, 1000.0)
        validate_range(self.pitch, "Pitch", -90.0, 90.0)
        validate_range(self.roll, "Roll", -90.0, 90.0)
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

            # Helper to safely get and convert
            try:
                return cls(
                    date=data_map["DATE"],
                    time=data_map["TIME"],
                    pressure=float(data_map["P"]),
                    distance=float(data_map["A"]),
                    quality=int(data_map["Q"]),
                    status=data_map["ST"],
                    pitch=float(data_map["PI"]),
                    roll=float(data_map["R"]),
                    checksum=checksum,
                )
            except KeyError as e:
                raise ValueError(f"Missing required tag for PNORA DF=201: {e}")
            except ValueError as e:
                raise ValueError(f"Invalid data type in PNORA DF=201: {e}")

        # Fallback to standard positional format (DF=200)
        if len(fields) != 9:
            raise ValueError(f"Expected 9 fields for PNORA, got {len(fields)}")

        return cls(
            date=fields[1],
            time=fields[2],
            pressure=float(fields[3]),
            distance=float(fields[4]),
            quality=int(fields[5]),
            status=fields[6],
            pitch=float(fields[7]),
            roll=float(fields[8]),
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
