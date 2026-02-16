"""Field-specific sentinel (invalid/no-data) value registry.

Nortek AD2CP instruments emit sentinel values to indicate invalid or
missing data.  The pattern is deterministic: every digit position in the
field format is filled with ``9`` (or ``-9``), preserving the decimal
precision of the field.  For example a field formatted as ``dd.d`` (2
integer digits, 1 decimal) produces sentinels ``-9.0`` **and** ``-9.9``
(and their positive counterparts ``9.0`` / ``9.9`` where appropriate).

This module maps every ``(parser_prefix, field_name)`` pair to the exact
tuple of raw-string sentinels that must be recognised for that field.
The mapping is consumed by :func:`~adcp_recorder.parsers.utils.parse_optional_float`
and :func:`~adcp_recorder.parsers.utils.parse_optional_int`.

Sources
-------
*  Nortek Integrators Guide AD2CP NMEA (N3015-007)
*  ``docs/specs/`` Markdown reference files
*  Production data from Signature-1000 deployments

"""

from typing import Final

# ── Format-derived sentinel tuples ──────────────────────────────────
# Named for the spec format notation  ``<int_digits>_<dec_digits>``.

_D1_1: Final = ("-9.0", "-9.9", "9.0", "9.9")
"""``d.d`` — 1 integer + 1 decimal digit."""

_D1_2: Final = ("-9.00", "-9.99", "9.00", "9.99")
"""``d.dd`` — 1 integer + 2 decimal digits."""

_D2_1: Final = ("-9.0", "-9.9", "-99.9", "9.0", "9.9", "99.9")
"""``dd.d`` — 2 integer + 1 decimal digit."""

_D2_2: Final = ("-9.00", "-9.99", "-99.99", "9.00", "9.99", "99.99")
"""``dd.dd`` — 2 integer + 2 decimal digits."""

_D2_3: Final = (
    "-9.000",
    "-9.999",
    "-99.999",
    "9.000",
    "9.999",
    "99.999",
)
"""``dd.ddd`` — 2 integer + 3 decimal digits."""

_D3_1: Final = (
    "-99.9",
    "-999.9",
    "99.9",
    "999.9",
)
"""``ddd.d`` — 3 integer + 1 decimal digit."""

_D3_2: Final = (
    "-99.99",
    "-999.99",
    "99.99",
    "999.99",
)
"""``ddd.dd`` — 3 integer + 2 decimal digits."""

_D3_3: Final = (
    "-99.999",
    "-999.999",
    "99.999",
    "999.999",
)
"""``ddd.ddd`` — 3 integer + 3 decimal digits."""

_D4_1: Final = (
    "-999.9",
    "-9999.9",
    "999.9",
    "9999.9",
)
"""``dddd.d`` — 4 integer + 1 decimal digit."""

_D4_3: Final = (
    "-999.999",
    "-9999.000",
    "-9999.999",
    "999.999",
    "9999.000",
    "9999.999",
)
"""``dddd.ddd`` — 4 integer + 3 decimal digits."""

_D4_4: Final = (
    "-999.9999",
    "-9999.9999",
    "999.9999",
    "9999.9999",
)
"""``dddd.dddd`` — 4 integer + 4 decimal digits (PNORF/PNORWD)."""

# ── Integer sentinels ───────────────────────────────────────────────

_INT_NONE: Final[tuple[str, ...]] = ()
"""No integer sentinels (default for most integer fields)."""

_INT_WAVE: Final = ("-9", "-99", "-999", "9", "99", "999")
"""Wave integer sentinel — PNORW/PNORE spec: -9, -999, etc."""

# ── Float sentinel registry ────────────────────────────────────────
# Key: (PARSER_PREFIX, field_name)
# Value: tuple of raw-string sentinels to match **exactly**

FLOAT_SENTINELS: Final[dict[tuple[str, str], tuple[str, ...]]] = {
    # ── PNORS family ────────────────────────────────────────────
    # Battery: dd.d
    ("PNORS", "battery"): _D2_1,
    ("PNORS1", "battery"): _D2_1,
    ("PNORS2", "battery"): _D2_1,
    ("PNORS3", "battery"): _D2_1,
    ("PNORS4", "battery"): _D2_1,
    # Sound speed: dddd.d
    ("PNORS", "sound_speed"): _D4_1,
    ("PNORS1", "sound_speed"): _D4_1,
    ("PNORS2", "sound_speed"): _D4_1,
    ("PNORS3", "sound_speed"): _D4_1,
    ("PNORS4", "sound_speed"): _D4_1,
    # Heading: ddd.d
    ("PNORS", "heading"): _D3_1,
    ("PNORS1", "heading"): _D3_1,
    ("PNORS2", "heading"): _D3_1,
    ("PNORS3", "heading"): _D3_1,
    ("PNORS4", "heading"): _D3_1,
    # Pitch: dd.d
    ("PNORS", "pitch"): _D2_1,
    ("PNORS1", "pitch"): _D2_1,
    ("PNORS2", "pitch"): _D2_1,
    ("PNORS3", "pitch"): _D2_1,
    ("PNORS4", "pitch"): _D2_1,
    # Roll: dd.d
    ("PNORS", "roll"): _D2_1,
    ("PNORS1", "roll"): _D2_1,
    ("PNORS2", "roll"): _D2_1,
    ("PNORS3", "roll"): _D2_1,
    ("PNORS4", "roll"): _D2_1,
    # Pressure: ddd.ddd
    ("PNORS", "pressure"): _D3_3,
    ("PNORS1", "pressure"): _D3_3,
    ("PNORS2", "pressure"): _D3_3,
    ("PNORS3", "pressure"): _D3_3,
    ("PNORS4", "pressure"): _D3_3,
    # Temperature: dd.dd
    ("PNORS", "temperature"): _D2_2,
    ("PNORS1", "temperature"): _D2_2,
    ("PNORS2", "temperature"): _D2_2,
    ("PNORS3", "temperature"): _D2_2,
    ("PNORS4", "temperature"): _D2_2,
    # Heading std dev: dd.dd
    ("PNORS1", "heading_std_dev"): _D2_2,
    ("PNORS2", "heading_std_dev"): _D2_2,
    # Pitch std dev: dd.dd
    ("PNORS1", "pitch_std_dev"): _D2_2,
    ("PNORS2", "pitch_std_dev"): _D2_2,
    # Roll std dev: dd.dd
    ("PNORS1", "roll_std_dev"): _D2_2,
    ("PNORS2", "roll_std_dev"): _D2_2,
    # Pressure std dev: dd.dd
    ("PNORS1", "pressure_std_dev"): _D2_2,
    ("PNORS2", "pressure_std_dev"): _D2_2,
    # ── PNORC family ────────────────────────────────────────────
    # Velocity (PNORC DF=100): dd.dd
    ("PNORC", "vel1"): _D2_2,
    ("PNORC", "vel2"): _D2_2,
    ("PNORC", "vel3"): _D2_2,
    ("PNORC", "vel4"): _D2_2,
    ("PNORC", "speed"): _D2_2,
    # Direction (PNORC DF=100): ddd.d
    ("PNORC", "direction"): _D3_1,
    # Velocity (PNORC1 DF=101): dd.ddd
    ("PNORC1", "vel1"): _D2_3,
    ("PNORC1", "vel2"): _D2_3,
    ("PNORC1", "vel3"): _D2_3,
    ("PNORC1", "vel4"): _D2_3,
    # Distance (PNORC1 DF=101): dd.d
    ("PNORC1", "distance"): _D2_1,
    # Amplitude (PNORC1 DF=101): ddd.d (float, dB)
    ("PNORC1", "amp1"): _D3_1,
    ("PNORC1", "amp2"): _D3_1,
    ("PNORC1", "amp3"): _D3_1,
    ("PNORC1", "amp4"): _D3_1,
    # Velocity (PNORC2 DF=102): dd.ddd
    ("PNORC2", "vel1"): _D2_3,
    ("PNORC2", "vel2"): _D2_3,
    ("PNORC2", "vel3"): _D2_3,
    ("PNORC2", "vel4"): _D2_3,
    # Distance (PNORC2 DF=102): dd.d
    ("PNORC2", "distance"): _D2_1,
    # Amplitude (PNORC2 DF=102): ddd.d (float, dB)
    ("PNORC2", "amp1"): _D3_1,
    ("PNORC2", "amp2"): _D3_1,
    ("PNORC2", "amp3"): _D3_1,
    ("PNORC2", "amp4"): _D3_1,
    # PNORC3 (DF=103): tagged averaged
    ("PNORC3", "distance"): _D2_1,
    ("PNORC3", "speed"): _D2_3,
    ("PNORC3", "direction"): _D3_1,
    # PNORC4 (DF=104): positional averaged
    ("PNORC4", "distance"): _D2_1,
    ("PNORC4", "speed"): _D2_3,
    ("PNORC4", "direction"): _D3_1,
    # ── PNORB (wave band parameters) ───────────────────────────
    ("PNORB", "freq_low"): _D1_2,
    ("PNORB", "freq_high"): _D1_2,
    ("PNORB", "hm0"): _D3_2,
    ("PNORB", "tm02"): _D3_2,
    ("PNORB", "tp"): _D3_2,
    ("PNORB", "dir_tp"): _D3_2,
    ("PNORB", "spr_tp"): _D3_2,
    ("PNORB", "main_dir"): _D3_2,
    # ── PNORW (wave bulk parameters) ───────────────────────────
    ("PNORW", "hm0"): _D3_2,
    ("PNORW", "h3"): _D3_2,
    ("PNORW", "h10"): _D3_2,
    ("PNORW", "hmax"): _D3_2,
    ("PNORW", "tm02"): _D3_2,
    ("PNORW", "tp"): _D3_2,
    ("PNORW", "tz"): _D3_2,
    ("PNORW", "dir_tp"): _D3_2,
    ("PNORW", "spr_tp"): _D3_2,
    ("PNORW", "main_dir"): _D3_2,
    ("PNORW", "uni_index"): _D3_2,
    ("PNORW", "mean_pressure"): _D3_2,
    ("PNORW", "near_surface_speed"): _D3_2,
    ("PNORW", "near_surface_dir"): _D3_2,
    # ── PNORE (energy density spectrum) ────────────────────────
    ("PNORE", "start_frequency"): _D1_2,
    ("PNORE", "step_frequency"): _D1_2,
    ("PNORE", "energy_density"): _D4_3,
    # ── PNORF (Fourier coefficient spectra) ────────────────────
    ("PNORF", "start_frequency"): _D1_2,
    ("PNORF", "step_frequency"): _D1_2,
    ("PNORF", "coefficient"): _D4_4,
    # ── PNORWD (wave directional spectra) ──────────────────────
    ("PNORWD", "start_frequency"): _D1_2,
    ("PNORWD", "step_frequency"): _D1_2,
    ("PNORWD", "value"): _D4_4,
    # ── PNORA (altitude/range) ─────────────────────────────────
    ("PNORA", "pressure"): _D3_3,
    ("PNORA", "distance"): _D3_3,
    ("PNORA", "pitch"): _D1_1,
    ("PNORA", "roll"): _D1_1,
    # ── PNORI family (instrument configuration) ────────────────
    # Format dd.dd — these are config values, sentinels are rare
    # but we include them for completeness.
    ("PNORI", "blanking_distance"): _D2_2,
    ("PNORI", "cell_size"): _D2_2,
    ("PNORI1", "blanking_distance"): _D2_2,
    ("PNORI1", "cell_size"): _D2_2,
    ("PNORI2", "blanking_distance"): _D2_2,
    ("PNORI2", "cell_size"): _D2_2,
}

# ── Integer sentinel registry ──────────────────────────────────────
# Key: (PARSER_PREFIX, field_name)
# Value: tuple of raw-string sentinels to match **exactly**

INT_SENTINELS: Final[dict[tuple[str, str], tuple[str, ...]]] = {
    # PNORW wave integer fields (spec: -9, -999, etc.)
    ("PNORW", "num_no_detects"): _INT_WAVE,
    ("PNORW", "num_bad_detects"): _INT_WAVE,
    # PNORE
    ("PNORE", "num_frequencies"): _INT_WAVE,
}


def get_float_sentinels(
    parser: str,
    field_name: str,
) -> tuple[str, ...]:
    """Look up sentinel strings for a float field.

    Args:
        parser: Parser prefix, e.g. ``"PNORS"`` or ``"PNORC1"``.
        field_name: Dataclass field name, e.g. ``"battery"``.

    Returns:
        Tuple of raw-string sentinels.  Returns an empty tuple when
        the ``(parser, field_name)`` pair is not registered — callers
        should still handle NaN and empty strings independently.

    """
    return FLOAT_SENTINELS.get((parser, field_name), ())


def get_int_sentinels(
    parser: str,
    field_name: str,
) -> tuple[str, ...]:
    """Look up sentinel strings for an integer field.

    Args:
        parser: Parser prefix, e.g. ``"PNORW"``.
        field_name: Dataclass field name, e.g. ``"num_no_detects"``.

    Returns:
        Tuple of raw-string sentinels.  Returns an empty tuple when
        the ``(parser, field_name)`` pair is not registered.

    """
    return INT_SENTINELS.get((parser, field_name), ())
