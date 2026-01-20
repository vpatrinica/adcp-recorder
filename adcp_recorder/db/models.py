"""ORM models for ADCP Recorder entities using SQLModel."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    CHAR,
    JSON,
    BigInteger,
    CheckConstraint,
    Column,
    Sequence,
    SmallInteger,
    Text,
)
from sqlmodel import Field, SQLModel


class ADCPBase(SQLModel):
    """Base class for all ADCP models."""

    pass


# ============================================================================
# CORE MODELS - Raw lines and parse errors
# ============================================================================


class RawLine(ADCPBase, table=True):
    __tablename__ = "raw_lines"

    line_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, Sequence("raw_lines_seq"), primary_key=True),
    )
    received_at: datetime = Field(default_factory=datetime.now)
    raw_sentence: str = Field(sa_column=Column(Text, nullable=False))
    parse_status: str = Field(
        sa_column=Column(Text, CheckConstraint("parse_status IN ('OK', 'FAIL', 'PENDING')"))
    )
    record_type: str | None = Field(default=None)
    checksum_valid: bool | None = Field(default=None)
    error_message: str | None = Field(default=None, sa_column=Column(Text))


class ParseError(ADCPBase, table=True):
    __tablename__ = "parse_errors"

    error_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, Sequence("parse_errors_seq"), primary_key=True),
    )
    received_at: datetime = Field(default_factory=datetime.now)
    raw_sentence: str = Field(sa_column=Column(Text, nullable=False))
    error_type: str = Field(max_length=50)
    error_message: str | None = Field(default=None, sa_column=Column(Text))
    attempted_prefix: str | None = Field(default=None, max_length=20)
    checksum_expected: str | None = Field(default=None, sa_column=Column(CHAR(2)))
    checksum_actual: str | None = Field(default=None, sa_column=Column(CHAR(2)))


# ============================================================================
# PNORI FAMILY - Instrument Configuration
# ============================================================================


class Pnori(ADCPBase, table=True):
    __tablename__ = "pnori"
    __table_args__ = (
        CheckConstraint("instrument_type_code IN (0, 2, 4)"),
        CheckConstraint("coord_system_name IN ('ENU', 'XYZ', 'BEAM')"),
        CheckConstraint("coord_system_code IN (0, 1, 2)"),
        CheckConstraint(
            "(coord_system_name = 'ENU' AND coord_system_code = 0) OR "
            "(coord_system_name = 'XYZ' AND coord_system_code = 1) OR "
            "(coord_system_name = 'BEAM' AND coord_system_code = 2)"
        ),
        CheckConstraint("instrument_type_code != 4 OR beam_count = 4"),
    )

    config_id: int | None = Field(
        default=None, sa_column=Column(BigInteger, Sequence("pnori_seq"), primary_key=True)
    )
    received_at: datetime = Field(default_factory=datetime.now)
    original_sentence: str = Field(sa_column=Column(Text, nullable=False))
    instrument_type_name: str = Field(max_length=20)
    instrument_type_code: int
    head_id: str = Field(max_length=30)
    beam_count: int
    cell_count: int
    blanking_distance: float
    cell_size: float
    coord_system_name: str = Field(max_length=10)
    coord_system_code: int
    checksum: str | None = Field(default=None, sa_column=Column(CHAR(2)))


class Pnori12(ADCPBase, table=True):
    __tablename__ = "pnori12"
    __table_args__ = (
        CheckConstraint("data_format IN (101, 102)"),
        CheckConstraint("instrument_type_code IN (0, 2, 4)"),
        CheckConstraint("coord_system_name IN ('ENU', 'XYZ', 'BEAM')"),
        CheckConstraint("coord_system_code IN (0, 1, 2)"),
        CheckConstraint(
            "(coord_system_name = 'ENU' AND coord_system_code = 0) OR "
            "(coord_system_name = 'XYZ' AND coord_system_code = 1) OR "
            "(coord_system_name = 'BEAM' AND coord_system_code = 2)"
        ),
        CheckConstraint("instrument_type_code != 4 OR beam_count = 4"),
    )

    config_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, Sequence("pnori12_seq"), primary_key=True),
    )
    received_at: datetime = Field(default_factory=datetime.now)
    data_format: int
    original_sentence: str = Field(sa_column=Column(Text, nullable=False))
    instrument_type_name: str = Field(max_length=20)
    instrument_type_code: int
    head_id: str = Field(max_length=30)
    beam_count: int
    cell_count: int
    blanking_distance: float
    cell_size: float
    coord_system_name: str = Field(max_length=10)
    coord_system_code: int
    checksum: str | None = Field(default=None, sa_column=Column(CHAR(2)))


# ============================================================================
# PNORS FAMILY - Sensor Data
# ============================================================================


class PnorsDf100(ADCPBase, table=True):
    __tablename__ = "pnors_df100"

    record_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, Sequence("pnors_df100_seq"), primary_key=True),
    )
    received_at: datetime = Field(default_factory=datetime.now)
    original_sentence: str = Field(sa_column=Column(Text, nullable=False))
    measurement_date: str = Field(sa_column=Column(CHAR(6), nullable=False))
    measurement_time: str = Field(sa_column=Column(CHAR(6), nullable=False))
    error_code: str | None = Field(default=None, sa_column=Column(CHAR(8)))
    status_code: str | None = Field(default=None, sa_column=Column(CHAR(8)))
    battery: float | None = None
    sound_speed: float | None = None
    heading: float | None = None
    pitch: float | None = None
    roll: float | None = None
    pressure: float | None = None
    temperature: float | None = None
    analog1: int | None = None
    analog2: int | None = None
    checksum: str | None = Field(default=None, sa_column=Column(CHAR(2)))


class Pnors12(ADCPBase, table=True):
    __tablename__ = "pnors12"
    __table_args__ = (CheckConstraint("data_format IN (101, 102)"),)

    record_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, Sequence("pnors12_seq"), primary_key=True),
    )
    received_at: datetime = Field(default_factory=datetime.now)
    data_format: int
    original_sentence: str = Field(sa_column=Column(Text, nullable=False))
    measurement_date: str = Field(sa_column=Column(CHAR(6), nullable=False))
    measurement_time: str = Field(sa_column=Column(CHAR(6), nullable=False))
    error_code: int | None = None
    status_code: str | None = Field(default=None, sa_column=Column(CHAR(8)))
    battery: float | None = None
    sound_speed: float | None = None
    heading_std_dev: float | None = None
    heading: float | None = None
    pitch: float | None = None
    pitch_std_dev: float | None = None
    roll: float | None = None
    roll_std_dev: float | None = None
    pressure: float | None = None
    pressure_std_dev: float | None = None
    temperature: float | None = None
    checksum: str | None = Field(default=None, sa_column=Column(CHAR(2)))


class Pnors34(ADCPBase, table=True):
    __tablename__ = "pnors34"
    __table_args__ = (CheckConstraint("data_format IN (103, 104)"),)

    record_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, Sequence("pnors34_seq"), primary_key=True),
    )
    received_at: datetime = Field(default_factory=datetime.now)
    data_format: int
    original_sentence: str = Field(sa_column=Column(Text, nullable=False))
    measurement_date: str = Field(sa_column=Column(CHAR(6), nullable=False))
    measurement_time: str = Field(sa_column=Column(CHAR(6), nullable=False))
    battery: float | None = None
    sound_speed: float | None = None
    heading: float | None = None
    pitch: float | None = None
    roll: float | None = None
    pressure: float | None = None
    temperature: float | None = None
    checksum: str | None = Field(default=None, sa_column=Column(CHAR(2)))


# ============================================================================
# PNORC FAMILY - Velocity Data
# ============================================================================


class PnorcDf100(ADCPBase, table=True):
    __tablename__ = "pnorc_df100"

    record_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, Sequence("pnorc_df100_seq"), primary_key=True),
    )
    received_at: datetime = Field(default_factory=datetime.now)
    original_sentence: str = Field(sa_column=Column(Text, nullable=False))
    measurement_date: str = Field(sa_column=Column(CHAR(6), nullable=False))
    measurement_time: str = Field(sa_column=Column(CHAR(6), nullable=False))
    cell_index: int = Field(sa_column=Column(SmallInteger, CheckConstraint("cell_index > 0")))
    vel1: float | None = None
    vel2: float | None = None
    vel3: float | None = None
    vel4: float | None = None
    speed: float | None = None
    direction: float | None = None
    amp_unit: str | None = Field(default=None, sa_column=Column(CHAR(1)))
    amp1: int | None = None
    amp2: int | None = None
    amp3: int | None = None
    amp4: int | None = None
    corr1: int | None = None
    corr2: int | None = None
    corr3: int | None = None
    corr4: int | None = None
    checksum: str | None = Field(default=None, sa_column=Column(CHAR(2)))


class Pnorc12(ADCPBase, table=True):
    __tablename__ = "pnorc12"
    __table_args__ = (CheckConstraint("data_format IN (101, 102)"),)

    record_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, Sequence("pnorc12_seq"), primary_key=True),
    )
    received_at: datetime = Field(default_factory=datetime.now)
    data_format: int
    original_sentence: str = Field(sa_column=Column(Text, nullable=False))
    measurement_date: str = Field(sa_column=Column(CHAR(6), nullable=False))
    measurement_time: str = Field(sa_column=Column(CHAR(6), nullable=False))
    cell_index: int
    cell_distance: float | None = None
    vel1: float | None = None
    vel2: float | None = None
    vel3: float | None = None
    vel4: float | None = None
    amp1: float | None = None
    amp2: float | None = None
    amp3: float | None = None
    amp4: float | None = None
    corr1: int | None = None
    corr2: int | None = None
    corr3: int | None = None
    corr4: int | None = None
    checksum: str | None = Field(default=None, sa_column=Column(CHAR(2)))


class Pnorc34(ADCPBase, table=True):
    __tablename__ = "pnorc34"
    __table_args__ = (CheckConstraint("data_format IN (103, 104)"),)

    record_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, Sequence("pnorc34_seq"), primary_key=True),
    )
    received_at: datetime = Field(default_factory=datetime.now)
    data_format: int
    original_sentence: str = Field(sa_column=Column(Text, nullable=False))
    measurement_date: str = Field(sa_column=Column(CHAR(6), nullable=False))
    measurement_time: str = Field(sa_column=Column(CHAR(6), nullable=False))
    cell_index: int
    cell_distance: float | None = None
    speed: float | None = None
    direction: float | None = None
    checksum: str | None = Field(default=None, sa_column=Column(CHAR(2)))


# ============================================================================
# PNORH - Header Data
# ============================================================================


class Pnorh(ADCPBase, table=True):
    __tablename__ = "pnorh"
    __table_args__ = (CheckConstraint("data_format IN (103, 104)"),)

    record_id: int | None = Field(
        default=None, sa_column=Column(BigInteger, Sequence("pnorh_seq"), primary_key=True)
    )
    received_at: datetime = Field(default_factory=datetime.now)
    data_format: int
    original_sentence: str = Field(sa_column=Column(Text, nullable=False))
    measurement_date: str = Field(sa_column=Column(CHAR(6), nullable=False))
    measurement_time: str = Field(sa_column=Column(CHAR(6), nullable=False))
    error_code: int | None = None
    status_code: str | None = Field(default=None, sa_column=Column(CHAR(8)))
    checksum: str | None = Field(default=None, sa_column=Column(CHAR(2)))


# ============================================================================
# WAVE DATA TABLES
# ============================================================================


class PnoreData(ADCPBase, table=True):
    __tablename__ = "pnore_data"
    __table_args__ = (
        CheckConstraint("sentence_type = 'PNORE'"),
        CheckConstraint("spectrum_basis IN (0, 1, 3)"),
    )

    record_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, Sequence("pnore_data_seq"), primary_key=True),
    )
    received_at: datetime = Field(default_factory=datetime.now)
    sentence_type: str = Field(max_length=10)
    original_sentence: str = Field(sa_column=Column(Text, nullable=False))
    measurement_date: str = Field(sa_column=Column(CHAR(6), nullable=False))
    measurement_time: str = Field(sa_column=Column(CHAR(6), nullable=False))
    spectrum_basis: int
    start_frequency: float | None = None
    step_frequency: float | None = None
    num_frequencies: int
    energy_densities: Any = Field(sa_column=Column(JSON, nullable=False))
    checksum: str | None = Field(default=None, sa_column=Column(CHAR(2)))


class PnorwData(ADCPBase, table=True):
    __tablename__ = "pnorw_data"
    __table_args__ = (CheckConstraint("sentence_type = 'PNORW'"),)

    record_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, Sequence("pnorw_data_seq"), primary_key=True),
    )
    received_at: datetime = Field(default_factory=datetime.now)
    sentence_type: str = Field(max_length=10)
    original_sentence: str = Field(sa_column=Column(Text, nullable=False))
    measurement_date: str = Field(sa_column=Column(CHAR(6), nullable=False))
    measurement_time: str = Field(sa_column=Column(CHAR(6), nullable=False))
    spectrum_basis: int | None = None
    processing_method: int | None = None
    hm0: float | None = None
    h3: float | None = None
    h10: float | None = None
    hmax: float | None = None
    tm02: float | None = None
    tp: float | None = None
    tz: float | None = None
    dir_tp: float | None = None
    spr_tp: float | None = None
    main_dir: float | None = None
    uni_index: float | None = None
    mean_pressure: float | None = None
    num_no_detects: int | None = None
    num_bad_detects: int | None = None
    near_surface_speed: float | None = None
    near_surface_dir: float | None = None
    wave_error_code: str | None = Field(default=None, sa_column=Column(CHAR(4)))
    checksum: str | None = Field(default=None, sa_column=Column(CHAR(2)))


class PnorbData(ADCPBase, table=True):
    __tablename__ = "pnorb_data"
    __table_args__ = (
        CheckConstraint("sentence_type = 'PNORB'"),
        CheckConstraint("spectrum_basis IN (0, 1, 3)"),
        CheckConstraint("processing_method IN (1, 2, 3, 4)"),
    )

    record_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, Sequence("pnorb_data_seq"), primary_key=True),
    )
    received_at: datetime = Field(default_factory=datetime.now)
    sentence_type: str = Field(max_length=10)
    original_sentence: str = Field(sa_column=Column(Text, nullable=False))
    measurement_date: str = Field(sa_column=Column(CHAR(6), nullable=False))
    measurement_time: str = Field(sa_column=Column(CHAR(6), nullable=False))
    spectrum_basis: int
    processing_method: int
    freq_low: float | None = None
    freq_high: float | None = None
    hmo: float | None = None
    tm02: float | None = None
    tp: float | None = None
    dirtp: float | None = None
    sprtp: float | None = None
    main_dir: float | None = None
    wave_error_code: str | None = Field(default=None, sa_column=Column(CHAR(4)))
    checksum: str | None = Field(default=None, sa_column=Column(CHAR(2)))


class PnorfData(ADCPBase, table=True):
    __tablename__ = "pnorf_data"
    __table_args__ = (
        CheckConstraint("sentence_type = 'PNORF'"),
        CheckConstraint("coefficient_flag IN ('A1', 'B1', 'A2', 'B2')"),
        CheckConstraint("spectrum_basis IN (0, 1, 3)"),
    )

    record_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, Sequence("pnorf_data_seq"), primary_key=True),
    )
    received_at: datetime = Field(default_factory=datetime.now)
    sentence_type: str = Field(max_length=10)
    original_sentence: str = Field(sa_column=Column(Text, nullable=False))
    coefficient_flag: str = Field(max_length=2)
    measurement_date: str = Field(sa_column=Column(CHAR(6), nullable=False))
    measurement_time: str = Field(sa_column=Column(CHAR(6), nullable=False))
    spectrum_basis: int
    start_frequency: float | None = None
    step_frequency: float | None = None
    num_frequencies: int
    coefficients: Any = Field(sa_column=Column(JSON, nullable=False))
    checksum: str | None = Field(default=None, sa_column=Column(CHAR(2)))


class PnorwdData(ADCPBase, table=True):
    __tablename__ = "pnorwd_data"
    __table_args__ = (
        CheckConstraint("sentence_type = 'PNORWD'"),
        CheckConstraint("direction_type IN ('MD', 'DS')"),
        CheckConstraint("spectrum_basis IN (0, 1, 3)"),
    )

    record_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, Sequence("pnorwd_data_seq"), primary_key=True),
    )
    received_at: datetime = Field(default_factory=datetime.now)
    sentence_type: str = Field(max_length=10)
    original_sentence: str = Field(sa_column=Column(Text, nullable=False))
    direction_type: str = Field(max_length=2)
    measurement_date: str = Field(sa_column=Column(CHAR(6), nullable=False))
    measurement_time: str = Field(sa_column=Column(CHAR(6), nullable=False))
    spectrum_basis: int
    start_frequency: float | None = None
    step_frequency: float | None = None
    num_frequencies: int
    values: Any = Field(sa_column=Column(JSON, nullable=False))
    checksum: str | None = Field(default=None, sa_column=Column(CHAR(2)))


# ============================================================================
# PNORA - Altimeter Data
# ============================================================================


class PnoraData(ADCPBase, table=True):
    __tablename__ = "pnora_data"
    __table_args__ = (CheckConstraint("sentence_type = 'PNORA'"),)

    record_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, Sequence("pnora_data_seq"), primary_key=True),
    )
    received_at: datetime = Field(default_factory=datetime.now)
    sentence_type: str = Field(max_length=10)
    original_sentence: str = Field(sa_column=Column(Text, nullable=False))
    measurement_date: str = Field(sa_column=Column(CHAR(6), nullable=False))
    measurement_time: str = Field(sa_column=Column(CHAR(6), nullable=False))
    pressure: float | None = None
    altimeter_distance: float | None = None
    quality: int | None = None
    status: str | None = Field(default=None, sa_column=Column(CHAR(2)))
    pitch: float | None = None
    roll: float | None = None
    checksum: str | None = Field(default=None, sa_column=Column(CHAR(2)))
