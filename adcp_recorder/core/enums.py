"""Shared enumerations for NMEA message types."""

from enum import Enum, IntEnum


class InstrumentType(IntEnum):
    """Nortek instrument types as per PNORI specification.

    Values:
        AQUADOPP: Standard Aquadopp (code 0)
        AQUADOPP_PROFILER: Aquadopp Profiler (code 2)
        SIGNATURE: Signature series (code 4)
    """

    AQUADOPP = 0
    AQUADOPP_PROFILER = 2
    SIGNATURE = 4

    @classmethod
    def from_code(cls, code: int) -> "InstrumentType":
        """Create instrument type from numeric code.

        Args:
            code: Numeric instrument type code (0, 2, or 4)

        Returns:
            InstrumentType enum value

        Raises:
            ValueError: If code is not valid
        """
        try:
            return cls(code)
        except ValueError:
            raise ValueError(
                f"Invalid instrument type code: {code}. "
                f"Valid codes: 0 (Aquadopp), 2 (Aquadopp Profiler), 4 (Signature)"
            )

    @property
    def valid_beam_counts(self) -> tuple[int, ...]:
        """Valid beam counts for this instrument type.

        Returns:
            Tuple of valid beam counts

        Note:
            Signature instruments must have exactly 4 beams.
            Other instruments can have 1-3 beams.
        """
        if self == InstrumentType.SIGNATURE:
            return (4,)
        return (1, 2, 3)


class CoordinateSystem(Enum):
    """Coordinate systems for velocity data.

    Values:
        ENU: East-North-Up coordinates
        XYZ: Instrument XYZ coordinates
        BEAM: Raw beam coordinates
    """

    ENU = "ENU"
    XYZ = "XYZ"
    BEAM = "BEAM"

    @classmethod
    def from_code(cls, code: int | str) -> "CoordinateSystem":
        """Create coordinate system from code.

        Args:
            code: Numeric code (0, 1, 2) or string ("ENU", "XYZ", "BEAM")

        Returns:
            CoordinateSystem enum value

        Raises:
            ValueError: If code is not valid
        """
        if isinstance(code, int):
            mapping = {0: cls.ENU, 1: cls.XYZ, 2: cls.BEAM}
            if code not in mapping:
                raise ValueError(
                    f"Invalid coordinate system code: {code}. "
                    f"Valid codes: 0 (ENU), 1 (XYZ), 2 (BEAM)"
                )
            return mapping[code]
        else:
            # String code
            code_upper = str(code).upper()
            try:
                return cls(code_upper)
            except ValueError:
                raise ValueError(f"Invalid coordinate system: {code}. Valid values: ENU, XYZ, BEAM")

    def to_numeric_code(self) -> int:
        """Convert to numeric code for backward compatibility.

        Returns:
            Numeric code: 0 (ENU), 1 (XYZ), 2 (BEAM)
        """
        mapping = {self.ENU: 0, self.XYZ: 1, self.BEAM: 2}
        return mapping[self]
