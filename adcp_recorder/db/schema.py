"""SQL schema definitions for DuckDB tables - REVISED with separate tables per data format.

Defines table schemas for raw NMEA sentence storage, error tracking, and parsed data.
Each data format (DF=100, 101, 102, 103, 104) gets its own table for type safety.
"""

# Raw lines table - stores all received NMEA sentences before parsing
RAW_LINES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS raw_lines (
    line_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    raw_sentence TEXT NOT NULL,
    parse_status VARCHAR(10) CHECK (parse_status IN ('OK', 'FAIL', 'PENDING')),
    record_type VARCHAR(20),
    checksum_valid BOOLEAN,
    error_message TEXT
);
"""

RAW_LINES_SEQUENCE_SQL = """
CREATE SEQUENCE IF NOT EXISTS raw_lines_seq START 1;
"""

RAW_LINES_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_raw_lines_received_at ON raw_lines(received_at);",
    "CREATE INDEX IF NOT EXISTS idx_raw_lines_record_type ON raw_lines(record_type);",
    "CREATE INDEX IF NOT EXISTS idx_raw_lines_parse_status ON raw_lines(parse_status);",
]

# Parse errors table
PARSE_ERRORS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS parse_errors (
    error_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    raw_sentence TEXT NOT NULL,
    error_type VARCHAR(50) NOT NULL,
    error_message TEXT,
    attempted_prefix VARCHAR(20),
    checksum_expected VARCHAR(2),
    checksum_actual VARCHAR(2)
);
"""

PARSE_ERRORS_SEQUENCE_SQL = """
CREATE SEQUENCE IF NOT EXISTS parse_errors_seq START 1;
"""

PARSE_ERRORS_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_errors_received_at ON parse_errors(received_at);",
    "CREATE INDEX IF NOT EXISTS idx_errors_type ON parse_errors(error_type);",
    "CREATE INDEX IF NOT EXISTS idx_errors_prefix ON parse_errors(attempted_prefix);",
]


# PNORI Configuration tables - separate table for each format

# PNORI (basic format) - no coordinate system field
PNORI_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pnori (\n    config_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    original_sentence TEXT NOT NULL,
    instrument_type_name VARCHAR(20) NOT NULL,
    instrument_type_code TINYINT NOT NULL
        CHECK (instrument_type_code IN (0, 2, 4)),
    head_id VARCHAR(30) NOT NULL
        CHECK (length(head_id) BETWEEN 1 AND 30),
    beam_count TINYINT NOT NULL
        CHECK (beam_count > 0 AND beam_count <= 4),
    cell_count SMALLINT NOT NULL
        CHECK (cell_count > 0 AND cell_count <= 128),
    blanking_distance DECIMAL(5,2) NOT NULL
        CHECK (blanking_distance > 0 AND blanking_distance <= 100),
    cell_size DECIMAL(5,2) NOT NULL
        CHECK (cell_size > 0 AND cell_size <= 100),
    coord_system_name VARCHAR(10) NOT NULL
        CHECK (coord_system_name IN ('ENU', 'XYZ', 'BEAM')),
    coord_system_code TINYINT NOT NULL
        CHECK (coord_system_code IN (0, 1, 2)),
    checksum CHAR(2),
    CONSTRAINT valid_signature_config CHECK (
        NOT (instrument_type_code = 4 AND beam_count != 4)
    )
);
"""

PNORI_SEQUENCE_SQL = """
CREATE SEQUENCE IF NOT EXISTS pnori_seq START 1;
"""

PNORI_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnori_head_id ON pnori(head_id);",
    "CREATE INDEX IF NOT EXISTS idx_pnori_received_at ON pnori(received_at);",
]

# PNORI1 (with coordinate system in message)
PNORI1_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pnori1 (
    config_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    original_sentence TEXT NOT NULL,
    instrument_type_name VARCHAR(20) NOT NULL,
    instrument_type_code TINYINT NOT NULL
        CHECK (instrument_type_code IN (0, 2, 4)),
    head_id VARCHAR(30) NOT NULL
        CHECK (length(head_id) BETWEEN 1 AND 30),
    beam_count TINYINT NOT NULL
        CHECK (beam_count > 0 AND beam_count <= 4),
    cell_count SMALLINT NOT NULL
        CHECK (cell_count > 0 AND cell_count <= 128),
    blanking_distance DECIMAL(5,2) NOT NULL
        CHECK (blanking_distance > 0 AND blanking_distance <= 100),
    cell_size DECIMAL(5,2) NOT NULL
        CHECK (cell_size > 0 AND cell_size <= 100),
    coord_system_name VARCHAR(10) NOT NULL
        CHECK (coord_system_name IN ('ENU', 'XYZ', 'BEAM')),
    coord_system_code TINYINT NOT NULL
        CHECK (coord_system_code IN (0, 1, 2)),
    checksum CHAR(2),
    CONSTRAINT valid_signature_config_1 CHECK (
        NOT (instrument_type_code = 4 AND beam_count != 4)
    ),
    CONSTRAINT valid_coord_mapping_1 CHECK (
        (coord_system_name = 'ENU' AND coord_system_code = 0) OR
        (coord_system_name = 'XYZ' AND coord_system_code = 1) OR
        (coord_system_name = 'BEAM' AND coord_system_code = 2)
    )
);
"""

PNORI1_SEQUENCE_SQL = """
CREATE SEQUENCE IF NOT EXISTS pnori1_seq START 1;
"""

PNORI1_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnori1_head_id ON pnori1(head_id);",
    "CREATE INDEX IF NOT EXISTS idx_pnori1_received_at ON pnori1(received_at);",
]

# PNORI2 (tagged format)
PNORI2_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pnori2 (
    config_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    original_sentence TEXT NOT NULL,
    instrument_type_name VARCHAR(20) NOT NULL,
    instrument_type_code TINYINT NOT NULL
        CHECK (instrument_type_code IN (0, 2, 4)),
    head_id VARCHAR(30) NOT NULL
        CHECK (length(head_id) BETWEEN 1 AND 30),
    beam_count TINYINT NOT NULL
        CHECK (beam_count > 0 AND beam_count <= 4),
    cell_count SMALLINT NOT NULL
        CHECK (cell_count > 0 AND cell_count <= 128),
    blanking_distance DECIMAL(5,2) NOT NULL
        CHECK (blanking_distance > 0 AND blanking_distance <= 100),
    cell_size DECIMAL(5,2) NOT NULL
        CHECK (cell_size > 0 AND cell_size <= 100),
    coord_system_name VARCHAR(10) NOT NULL
        CHECK (coord_system_name IN ('ENU', 'XYZ', 'BEAM')),
    coord_system_code TINYINT NOT NULL
        CHECK (coord_system_code IN (0, 1, 2)),
    checksum CHAR(2),
    CONSTRAINT valid_signature_config_2 CHECK (
        NOT (instrument_type_code = 4 AND beam_count != 4)
    ),
    CONSTRAINT valid_coord_mapping_2 CHECK (
        (coord_system_name = 'ENU' AND coord_system_code = 0) OR
        (coord_system_name = 'XYZ' AND coord_system_code = 1) OR
        (coord_system_name = 'BEAM' AND coord_system_code = 2)
    )
);
"""

PNORI2_SEQUENCE_SQL = """
CREATE SEQUENCE IF NOT EXISTS pnori2_seq START 1;
"""

PNORI2_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnori2_head_id ON pnori2(head_id);",
    "CREATE INDEX IF NOT EXISTS idx_pnori2_received_at ON pnori2(received_at);",
]


# ============================================================================
# PNORS FAMILY - Sensor Data (5 separate tables for DF100-104)
# ============================================================================

# PNORS DF=100
PNORS_DF100_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pnors_df100 (
    record_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    original_sentence TEXT NOT NULL,
    measurement_date CHAR(6) NOT NULL,
    measurement_time CHAR(6) NOT NULL,
    error_code CHAR(8),
    status_code CHAR(8),
    battery DECIMAL(4,1),
    sound_speed DECIMAL(6,1),
    heading DECIMAL(5,1) CHECK (heading >= 0 AND heading < 360),
    pitch DECIMAL(4,1) CHECK (pitch >= -90 AND pitch <= 90),
    roll DECIMAL(5,1) CHECK (roll >= -180 AND roll <= 180),
    pressure DECIMAL(7,3),
    temperature DECIMAL(5,2),
    analog1 SMALLINT,
    analog2 SMALLINT,
    speed DECIMAL(8,4),
    direction DECIMAL(5,2),
    amp_unit CHAR(1),
    checksum CHAR(2)
);
"""
PNORS_DF100_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS pnors_df100_seq START 1;"
PNORS_DF100_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnors_df100_date_time "
    "ON pnors_df100(measurement_date, measurement_time);",
]

# PNORS1 DF=101
PNORS_DF101_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pnors_df101 (
    record_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    original_sentence TEXT NOT NULL,
    measurement_date CHAR(6) NOT NULL,
    measurement_time CHAR(6) NOT NULL,
    error_code INTEGER,
    status_code CHAR(8),
    battery DECIMAL(4,1),
    sound_speed DECIMAL(6,1),
    heading_std_dev DECIMAL(5,1),
    heading DECIMAL(5,1),
    pitch DECIMAL(4,1),
    pitch_std_dev DECIMAL(4,1),
    roll DECIMAL(5,1),
    roll_std_dev DECIMAL(5,1),
    pressure DECIMAL(7,3),
    pressure_std_dev DECIMAL(7,3),
    temperature DECIMAL(5,2),
    checksum CHAR(2)
);
"""
PNORS_DF101_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS pnors_df101_seq START 1;"
PNORS_DF101_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnors_df101_date_time "
    "ON pnors_df101(measurement_date, measurement_time);",
]

# PNORS2 DF=102 (same fields as DF101, just tagged format)
PNORS_DF102_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pnors_df102 (
    record_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    original_sentence TEXT NOT NULL,
    measurement_date CHAR(6) NOT NULL,
    measurement_time CHAR(6) NOT NULL,
    error_code INTEGER,
    status_code CHAR(8),
    battery DECIMAL(4,1),
    sound_speed DECIMAL(6,1),
    heading_std_dev DECIMAL(5,1),
    heading DECIMAL(5,1),
    pitch DECIMAL(4,1),
    pitch_std_dev DECIMAL(4,1),
    roll DECIMAL(5,1),
    roll_std_dev DECIMAL(5,1),
    pressure DECIMAL(7,3),
    pressure_std_dev DECIMAL(7,3),
    temperature DECIMAL(5,2),
    checksum CHAR(2)
);
"""
PNORS_DF102_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS pnors_df102_seq START 1;"
PNORS_DF102_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnors_df102_date_time "
    "ON pnors_df102(measurement_date, measurement_time);",
]

# PNORS3 DF=103
PNORS_DF103_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pnors_df103 (
    record_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    original_sentence TEXT NOT NULL,
    measurement_date CHAR(6) NOT NULL,
    measurement_time CHAR(6) NOT NULL,
    battery DECIMAL(4,1),
    heading DECIMAL(5,1),
    pitch DECIMAL(4,1),
    roll DECIMAL(5,1),
    pressure DECIMAL(7,3),
    temperature DECIMAL(5,2),
    checksum CHAR(2)
);
"""
PNORS_DF103_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS pnors_df103_seq START 1;"
PNORS_DF103_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnors_df103_date_time "
    "ON pnors_df103(measurement_date, measurement_time);",
]

# PNORS4 DF=104
PNORS_DF104_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pnors_df104 (
    record_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    original_sentence TEXT NOT NULL,
    measurement_date CHAR(6) NOT NULL,
    measurement_time CHAR(6) NOT NULL,
    battery DECIMAL(4,1),
    sound_speed DECIMAL(6,1),
    heading DECIMAL(5,1),
    pitch DECIMAL(4,1),
    roll DECIMAL(5,1),
    pressure DECIMAL(7,3),
    temperature DECIMAL(5,2),
    checksum CHAR(2)
);
"""
PNORS_DF104_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS pnors_df104_seq START 1;"
PNORS_DF104_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnors_df104_date_time "
    "ON pnors_df104(measurement_date, measurement_time);",
]

# ============================================================================
# PNORC FAMILY - Velocity Data (5 separate tables for DF100-104)
# ============================================================================

# PNORC DF=100
PNORC_DF100_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pnorc_df100 (
    record_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    original_sentence TEXT NOT NULL,
    measurement_date CHAR(6) NOT NULL,
    measurement_time CHAR(6) NOT NULL,
    cell_index SMALLINT NOT NULL CHECK (cell_index > 0),
    vel1 DECIMAL(8,4),
    vel2 DECIMAL(8,4),
    vel3 DECIMAL(8,4),
    vel4 DECIMAL(8,4),
    speed DECIMAL(8,4),
    direction DECIMAL(5,2),
    amp_unit CHAR(1),
    amp1 SMALLINT,
    amp2 SMALLINT,
    amp3 SMALLINT,
    amp4 SMALLINT,
    corr1 SMALLINT,
    corr2 SMALLINT,
    corr3 SMALLINT,
    corr4 SMALLINT,
    checksum CHAR(2)
);
"""
PNORC_DF100_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS pnorc_df100_seq START 1;"
PNORC_DF100_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnorc_df100_date_time "
    "ON pnorc_df100(measurement_date, measurement_time);",
    "CREATE INDEX IF NOT EXISTS idx_pnorc_df100_cell ON pnorc_df100(cell_index);",
]

# PNORC1 DF=101
PNORC_DF101_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pnorc_df101 (
    record_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    original_sentence TEXT NOT NULL,
    measurement_date CHAR(6) NOT NULL,
    measurement_time CHAR(6) NOT NULL,
    cell_index SMALLINT NOT NULL,
    distance DECIMAL(8,3),
    vel1 DECIMAL(8,4),
    vel2 DECIMAL(8,4),
    vel3 DECIMAL(8,4),
    vel4 DECIMAL(8,4),
    amp1 DECIMAL(6,2),
    amp2 DECIMAL(6,2),
    amp3 DECIMAL(6,2),
    amp4 DECIMAL(6,2),
    corr1 SMALLINT,
    corr2 SMALLINT,
    corr3 SMALLINT,
    corr4 SMALLINT,
    checksum CHAR(2)
);
"""
PNORC_DF101_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS pnorc_df101_seq START 1;"
PNORC_DF101_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnorc_df101_date_time "
    "ON pnorc_df101(measurement_date, measurement_time);",
    "CREATE INDEX IF NOT EXISTS idx_pnorc_df101_cell ON pnorc_df101(cell_index);",
]

# PNORC2 DF=102 (same fields as DF101, tagged format)
PNORC_DF102_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pnorc_df102 (
    record_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    original_sentence TEXT NOT NULL,
    measurement_date CHAR(6) NOT NULL,
    measurement_time CHAR(6) NOT NULL,
    cell_index SMALLINT NOT NULL,
    distance DECIMAL(8,3),
    vel1 DECIMAL(8,4),
    vel2 DECIMAL(8,4),
    vel3 DECIMAL(8,4),
    vel4 DECIMAL(8,4),
    amp1 DECIMAL(6,2),
    amp2 DECIMAL(6,2),
    amp3 DECIMAL(6,2),
    amp4 DECIMAL(6,2),
    corr1 SMALLINT,
    corr2 SMALLINT,
    corr3 SMALLINT,
    corr4 SMALLINT,
    checksum CHAR(2)
);
"""
PNORC_DF102_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS pnorc_df102_seq START 1;"
PNORC_DF102_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnorc_df102_date_time "
    "ON pnorc_df102(measurement_date, measurement_time);",
    "CREATE INDEX IF NOT EXISTS idx_pnorc_df102_cell ON pnorc_df102(cell_index);",
]

# PNORC3 DF=103
PNORC_DF103_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pnorc_df103 (
    record_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    original_sentence TEXT NOT NULL,
    measurement_date CHAR(6) NOT NULL,
    measurement_time CHAR(6) NOT NULL,
    cell_index SMALLINT NOT NULL,
    distance DECIMAL(8,3),
    speed DECIMAL(8,4),
    direction DECIMAL(5,2),
    avg_amplitude SMALLINT,
    avg_correlation SMALLINT,
    checksum CHAR(2)
);
"""
PNORC_DF103_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS pnorc_df103_seq START 1;"
PNORC_DF103_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnorc_df103_date_time "
    "ON pnorc_df103(measurement_date, measurement_time);",
    "CREATE INDEX IF NOT EXISTS idx_pnorc_df103_cell ON pnorc_df103(cell_index);",
]

# PNORC4 DF=104
PNORC_DF104_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pnorc_df104 (
    record_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    original_sentence TEXT NOT NULL,
    measurement_date CHAR(6) NOT NULL,
    measurement_time CHAR(6) NOT NULL,
    cell_index SMALLINT NOT NULL,
    distance DECIMAL(8,3),
    speed DECIMAL(8,4),
    direction DECIMAL(5,2),
    avg_amplitude SMALLINT,
    avg_correlation SMALLINT,
    checksum CHAR(2)
);
"""
PNORC_DF104_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS pnorc_df104_seq START 1;"
PNORC_DF104_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnorc_df104_date_time "
    "ON pnorc_df104(measurement_date, measurement_time);",
    "CREATE INDEX IF NOT EXISTS idx_pnorc_df104_cell ON pnorc_df104(cell_index);",
]

# ============================================================================
# PNORH FAMILY - Header Data (2 separate tables for DF103-104)
# ============================================================================

# PNORH3 DF=103
PNORH_DF103_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pnorh_df103 (
    record_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    original_sentence TEXT NOT NULL,
    measurement_date CHAR(6) NOT NULL,
    measurement_time CHAR(6) NOT NULL,
    error_code INTEGER,
    status_code CHAR(8),
    checksum CHAR(2)
);
"""
PNORH_DF103_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS pnorh_df103_seq START 1;"
PNORH_DF103_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnorh_df103_date_time "
    "ON pnorh_df103(measurement_date, measurement_time);",
]

# PNORH4 DF=104
PNORH_DF104_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pnorh_df104 (
    record_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    original_sentence TEXT NOT NULL,
    measurement_date CHAR(6) NOT NULL,
    measurement_time CHAR(6) NOT NULL,
    error_code INTEGER,
    status_code CHAR(8),
    checksum CHAR(2)
);
"""
PNORH_DF104_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS pnorh_df104_seq START 1;"
PNORH_DF104_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnorh_df104_date_time "
    "ON pnorh_df104(measurement_date, measurement_time);",
]

# ============================================================================
# WAVE DATA TABLES (already correct - PNORE, PNORF, PNORWD fixed earlier)
# ============================================================================

# Echo Intensity Data Table (PNORE) - Wave Energy Density Spectrum
ECHO_DATA_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS echo_data (
    record_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    sentence_type VARCHAR(10) NOT NULL CHECK (sentence_type = 'PNORE'),
    original_sentence TEXT NOT NULL,
    measurement_date CHAR(6) NOT NULL,
    measurement_time CHAR(6) NOT NULL,
    spectrum_basis TINYINT NOT NULL CHECK (spectrum_basis IN (0, 1, 3)),
    start_frequency DECIMAL(5,2) CHECK (start_frequency >= 0 AND start_frequency <= 10),
    step_frequency DECIMAL(5,2) CHECK (step_frequency >= 0 AND step_frequency <= 10),
    num_frequencies SMALLINT NOT NULL CHECK (num_frequencies >= 1 AND num_frequencies <= 99),
    energy_densities JSON NOT NULL,
    checksum CHAR(2)
);
"""
ECHO_DATA_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS echo_data_seq START 1;"
ECHO_DATA_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_echo_date_time "
    "ON echo_data(measurement_date, measurement_time);",
]

# Wave Data (PNORW)
PNORW_DATA_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pnorw_data (
    record_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    sentence_type VARCHAR(10) NOT NULL CHECK (sentence_type = 'PNORW'),
    original_sentence TEXT NOT NULL,
    measurement_date CHAR(6) NOT NULL,
    measurement_time CHAR(6) NOT NULL,
    spectrum_basis TINYINT,
    processing_method TINYINT,
    hm0 DECIMAL(6,3),
    hmax DECIMAL(6,3),
    tp DECIMAL(6,3),
    tm02 DECIMAL(6,3),
    mean_dir DECIMAL(6,2),
    peak_dir DECIMAL(6,2),
    directional_spread DECIMAL(6,2),
    peak_directional_spread DECIMAL(6,2),
    mean_period DECIMAL(6,3),
    mean_peak_period DECIMAL(6,3),
    mean_directional_spread DECIMAL(6,2),
    peak_directional_spread_m2 DECIMAL(6,2),
    mean_wavelength DECIMAL(8,3),
    peak_wavelength DECIMAL(8,3),
    mean_steepness DECIMAL(8,5),
    peak_steepness DECIMAL(8,5),
    wave_error_code CHAR(4),
    checksum CHAR(2)
);
"""
PNORW_DATA_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS pnorw_data_seq START 1;"
PNORW_DATA_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnorw_date_time "
    "ON pnorw_data(measurement_date, measurement_time);",
]

# Wave Band Parameters (PNORB) - DF=501
PNORB_DATA_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pnorb_data (
    record_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    sentence_type VARCHAR(10) NOT NULL CHECK (sentence_type = 'PNORB'),
    original_sentence TEXT NOT NULL,
    measurement_date CHAR(6) NOT NULL,
    measurement_time CHAR(6) NOT NULL,
    spectrum_basis TINYINT NOT NULL CHECK (spectrum_basis IN (0, 1, 3)),
    processing_method TINYINT NOT NULL CHECK (processing_method IN (1, 2, 3, 4)),
    freq_low DECIMAL(4,2) CHECK (freq_low >= 0 AND freq_low <= 9.99),
    freq_high DECIMAL(4,2) CHECK (freq_high >= 0 AND freq_high <= 9.99),
    hmo DECIMAL(5,2) CHECK (hmo >= 0 AND hmo <= 99.99),
    tm02 DECIMAL(5,2) CHECK (tm02 >= 0 AND tm02 <= 99.99),
    tp DECIMAL(5,2) CHECK (tp >= 0 AND tp <= 99.99),
    dirtp DECIMAL(5,2) CHECK (dirtp >= 0 AND dirtp <= 359.99),
    sprtp DECIMAL(5,2) CHECK (sprtp >= 0 AND sprtp <= 359.99),
    main_dir DECIMAL(5,2) CHECK (main_dir >= 0 AND main_dir <= 359.99),
    wave_error_code CHAR(4),
    checksum CHAR(2)
);
"""
PNORB_DATA_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS pnorb_data_seq START 1;"
PNORB_DATA_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnorb_date_time "
    "ON pnorb_data(measurement_date, measurement_time);",
]

# Frequency Data (PNORF) - Fourier Coefficient Spectra
PNORF_DATA_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pnorf_data (
    record_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    sentence_type VARCHAR(10) NOT NULL CHECK (sentence_type = 'PNORF'),
    original_sentence TEXT NOT NULL,
    coefficient_flag VARCHAR(2) NOT NULL CHECK (coefficient_flag IN ('A1', 'B1', 'A2', 'B2')),
    measurement_date CHAR(6) NOT NULL,
    measurement_time CHAR(6) NOT NULL,
    spectrum_basis TINYINT NOT NULL CHECK (spectrum_basis IN (0, 1, 3)),
    start_frequency DECIMAL(5,2) CHECK (start_frequency >= 0 AND start_frequency <= 10),
    step_frequency DECIMAL(5,2) CHECK (step_frequency >= 0 AND step_frequency <= 10),
    num_frequencies SMALLINT NOT NULL CHECK (num_frequencies >= 1 AND num_frequencies <= 999),
    coefficients JSON NOT NULL,
    checksum CHAR(2)
);
"""
PNORF_DATA_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS pnorf_data_seq START 1;"
PNORF_DATA_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnorf_date_time "
    "ON pnorf_data(measurement_date, measurement_time);",
    "CREATE INDEX IF NOT EXISTS idx_pnorf_coeff_flag ON pnorf_data(coefficient_flag);",
]

# Wave Directional Data (PNORWD) - Wave Directional Spectra
PNORWD_DATA_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pnorwd_data (
    record_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    sentence_type VARCHAR(10) NOT NULL CHECK (sentence_type = 'PNORWD'),
    original_sentence TEXT NOT NULL,
    direction_type VARCHAR(2) NOT NULL CHECK (direction_type IN ('MD', 'DS')),
    measurement_date CHAR(6) NOT NULL,
    measurement_time CHAR(6) NOT NULL,
    spectrum_basis TINYINT NOT NULL CHECK (spectrum_basis IN (0, 1, 3)),
    start_frequency DECIMAL(5,2) CHECK (start_frequency >= 0 AND start_frequency <= 10),
    step_frequency DECIMAL(5,2) CHECK (step_frequency >= 0 AND start_frequency <= 10),
    num_frequencies SMALLINT NOT NULL CHECK (num_frequencies >= 1 AND num_frequencies <= 999),
    values JSON NOT NULL,
    checksum CHAR(2)
);
"""
PNORWD_DATA_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS pnorwd_data_seq START 1;"
PNORWD_DATA_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnorwd_date_time "
    "ON pnorwd_data(measurement_date, measurement_time);",
    "CREATE INDEX IF NOT EXISTS idx_pnorwd_dir_type ON pnorwd_data(direction_type);",
]

# Altitude Data (PNORA)
PNORA_DATA_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pnora_data (
    record_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    sentence_type VARCHAR(10) NOT NULL CHECK (sentence_type = 'PNORA'),
    original_sentence TEXT NOT NULL,
    measurement_date CHAR(6) NOT NULL,
    measurement_time CHAR(6) NOT NULL,
    pressure DECIMAL(7,3),
    altimeter_distance DECIMAL(7,3),
    quality INTEGER,
    status CHAR(2),
    pitch DECIMAL(4,1),
    roll DECIMAL(4,1),
    checksum CHAR(2)
);
"""
PNORA_DATA_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS pnora_data_seq START 1;"
PNORA_DATA_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnora_date_time "
    "ON pnora_data(measurement_date, measurement_time);",
]

# ============================================================================
# ALL SCHEMA SQL - Complete list in dependency order
# ============================================================================
ALL_SCHEMA_SQL = [
    # Core tables
    RAW_LINES_SEQUENCE_SQL,
    RAW_LINES_TABLE_SQL,
    *RAW_LINES_INDEXES_SQL,
    PARSE_ERRORS_SEQUENCE_SQL,
    PARSE_ERRORS_TABLE_SQL,
    *PARSE_ERRORS_INDEXES_SQL,
    # Configuration - PNORI family (3 tables)
    PNORI_SEQUENCE_SQL,
    PNORI_TABLE_SQL,
    *PNORI_INDEXES_SQL,
    PNORI1_SEQUENCE_SQL,
    PNORI1_TABLE_SQL,
    *PNORI1_INDEXES_SQL,
    PNORI2_SEQUENCE_SQL,
    PNORI2_TABLE_SQL,
    *PNORI2_INDEXES_SQL,
    # PNORS family (5 tables)
    PNORS_DF100_SEQUENCE_SQL,
    PNORS_DF100_TABLE_SQL,
    *PNORS_DF100_INDEXES_SQL,
    PNORS_DF101_SEQUENCE_SQL,
    PNORS_DF101_TABLE_SQL,
    *PNORS_DF101_INDEXES_SQL,
    PNORS_DF102_SEQUENCE_SQL,
    PNORS_DF102_TABLE_SQL,
    *PNORS_DF102_INDEXES_SQL,
    PNORS_DF103_SEQUENCE_SQL,
    PNORS_DF103_TABLE_SQL,
    *PNORS_DF103_INDEXES_SQL,
    PNORS_DF104_SEQUENCE_SQL,
    PNORS_DF104_TABLE_SQL,
    *PNORS_DF104_INDEXES_SQL,
    # PNORC family (5 tables)
    PNORC_DF100_SEQUENCE_SQL,
    PNORC_DF100_TABLE_SQL,
    *PNORC_DF100_INDEXES_SQL,
    PNORC_DF101_SEQUENCE_SQL,
    PNORC_DF101_TABLE_SQL,
    *PNORC_DF101_INDEXES_SQL,
    PNORC_DF102_SEQUENCE_SQL,
    PNORC_DF102_TABLE_SQL,
    *PNORC_DF102_INDEXES_SQL,
    PNORC_DF103_SEQUENCE_SQL,
    PNORC_DF103_TABLE_SQL,
    *PNORC_DF103_INDEXES_SQL,
    PNORC_DF104_SEQUENCE_SQL,
    PNORC_DF104_TABLE_SQL,
    *PNORC_DF104_INDEXES_SQL,
    # PNORH family (2 tables)
    PNORH_DF103_SEQUENCE_SQL,
    PNORH_DF103_TABLE_SQL,
    *PNORH_DF103_INDEXES_SQL,
    PNORH_DF104_SEQUENCE_SQL,
    PNORH_DF104_TABLE_SQL,
    *PNORH_DF104_INDEXES_SQL,
    # Wave data tables
    ECHO_DATA_SEQUENCE_SQL,
    ECHO_DATA_TABLE_SQL,
    *ECHO_DATA_INDEXES_SQL,
    PNORW_DATA_SEQUENCE_SQL,
    PNORW_DATA_TABLE_SQL,
    *PNORW_DATA_INDEXES_SQL,
    PNORB_DATA_SEQUENCE_SQL,
    PNORB_DATA_TABLE_SQL,
    *PNORB_DATA_INDEXES_SQL,
    PNORF_DATA_SEQUENCE_SQL,
    PNORF_DATA_TABLE_SQL,
    *PNORF_DATA_INDEXES_SQL,
    PNORWD_DATA_SEQUENCE_SQL,
    PNORWD_DATA_TABLE_SQL,
    *PNORWD_DATA_INDEXES_SQL,
    PNORA_DATA_SEQUENCE_SQL,
    PNORA_DATA_TABLE_SQL,
    *PNORA_DATA_INDEXES_SQL,
]
