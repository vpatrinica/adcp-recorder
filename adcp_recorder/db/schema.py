"""SQL schema definitions for DuckDB tables - CONSOLIDATED schema.

Defines table schemas for raw NMEA sentence storage, error tracking, and parsed data.
Tables are consolidated by data format families for simpler management.
"""

# ============================================================================
# TABLE DESCRIPTIONS - User-friendly labels for visualization
# ============================================================================
TABLE_DESCRIPTIONS = {
    "pnore_data": "Wave Energy Density Spectrum",
    "pnorf_data": "Fourier Coefficient Spectra",
    "pnorwd_data": "Wave Directional Spectra",
    "pnorw_data": "Wave Bulk Parameters",
    "pnorb_data": "Wave Band Parameters",
    "pnori": "Instrument Configuration (DF100)",
    "pnori12": "Instrument Configuration (DF101/102)",
    "pnors_df100": "Sensor Data (DF100)",
    "pnors12": "Sensor Data (DF101/102)",
    "pnors34": "Sensor Data (DF103/104)",
    "pnorc_df100": "Current Velocity (DF100)",
    "pnorc12": "Current Velocity (DF101/102)",
    "pnorc34": "Current Velocity (DF103/104)",
    "pnorh": "Measurement Header (DF103/104)",
    "pnora_data": "Altimeter Data",
    "raw_lines": "Raw NMEA Sentences",
    "parse_errors": "Parse Errors",
}

# ============================================================================
# CORE TABLES - Raw lines and parse errors
# ============================================================================

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
RAW_LINES_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS raw_lines_seq START 1;"
RAW_LINES_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_raw_lines_received_at ON raw_lines(received_at);",
    "CREATE INDEX IF NOT EXISTS idx_raw_lines_record_type ON raw_lines(record_type);",
    "CREATE INDEX IF NOT EXISTS idx_raw_lines_parse_status ON raw_lines(parse_status);",
]

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
PARSE_ERRORS_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS parse_errors_seq START 1;"
PARSE_ERRORS_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_errors_received_at ON parse_errors(received_at);",
    "CREATE INDEX IF NOT EXISTS idx_errors_type ON parse_errors(error_type);",
    "CREATE INDEX IF NOT EXISTS idx_errors_prefix ON parse_errors(attempted_prefix);",
]

# ============================================================================
# PNORI FAMILY - Instrument Configuration
# ============================================================================

# PNORI (DF100) - Basic format
PNORI_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pnori (
    config_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    original_sentence TEXT NOT NULL,
    instrument_type_name VARCHAR(20) NOT NULL,
    instrument_type_code TINYINT NOT NULL CHECK (instrument_type_code IN (0, 2, 4)),
    head_id VARCHAR(30) NOT NULL CHECK (length(head_id) BETWEEN 1 AND 30),
    beam_count TINYINT NOT NULL CHECK (beam_count > 0 AND beam_count <= 4),
    cell_count SMALLINT NOT NULL CHECK (cell_count > 0 AND cell_count <= 128),
    blanking_distance DECIMAL(5,2) NOT NULL
        CHECK (blanking_distance > 0 AND blanking_distance <= 100),
    cell_size DECIMAL(5,2) NOT NULL CHECK (cell_size > 0 AND cell_size <= 100),
    coord_system_name VARCHAR(10) NOT NULL CHECK (coord_system_name IN ('ENU', 'XYZ', 'BEAM')),
    coord_system_code TINYINT NOT NULL CHECK (coord_system_code IN (0, 1, 2)),
    checksum CHAR(2),
    CHECK (
        (coord_system_name = 'ENU' AND coord_system_code = 0) OR
        (coord_system_name = 'XYZ' AND coord_system_code = 1) OR
        (coord_system_name = 'BEAM' AND coord_system_code = 2)
    ),
    CHECK (instrument_type_code != 4 OR beam_count = 4)
);
"""
PNORI_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS pnori_seq START 1;"
PNORI_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnori_head_id ON pnori(head_id);",
    "CREATE INDEX IF NOT EXISTS idx_pnori_received_at ON pnori(received_at);",
]

# PNORI12 (DF101/102) - Consolidated from pnori1 and pnori2
PNORI12_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pnori12 (
    config_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    data_format TINYINT NOT NULL CHECK (data_format IN (101, 102)),
    original_sentence TEXT NOT NULL,
    instrument_type_name VARCHAR(20) NOT NULL,
    instrument_type_code TINYINT NOT NULL CHECK (instrument_type_code IN (0, 2, 4)),
    head_id VARCHAR(30) NOT NULL CHECK (length(head_id) BETWEEN 1 AND 30),
    beam_count TINYINT NOT NULL CHECK (beam_count > 0 AND beam_count <= 4),
    cell_count SMALLINT NOT NULL CHECK (cell_count > 0 AND cell_count <= 128),
    blanking_distance DECIMAL(5,2) NOT NULL
        CHECK (blanking_distance > 0 AND blanking_distance <= 100),
    cell_size DECIMAL(5,2) NOT NULL CHECK (cell_size > 0 AND cell_size <= 100),
    coord_system_name VARCHAR(10) NOT NULL CHECK (coord_system_name IN ('ENU', 'XYZ', 'BEAM')),
    coord_system_code TINYINT NOT NULL CHECK (coord_system_code IN (0, 1, 2)),
    checksum CHAR(2),
    CHECK (
        (coord_system_name = 'ENU' AND coord_system_code = 0) OR
        (coord_system_name = 'XYZ' AND coord_system_code = 1) OR
        (coord_system_name = 'BEAM' AND coord_system_code = 2)
    ),
    CHECK (instrument_type_code != 4 OR beam_count = 4)
);
"""
PNORI12_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS pnori12_seq START 1;"
PNORI12_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnori12_head_id ON pnori12(head_id);",
    "CREATE INDEX IF NOT EXISTS idx_pnori12_received_at ON pnori12(received_at);",
    "CREATE INDEX IF NOT EXISTS idx_pnori12_data_format ON pnori12(data_format);",
]

# ============================================================================
# PNORS FAMILY - Sensor Data
# ============================================================================

# PNORS DF100 - Keep but remove extra fields
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
    heading DECIMAL(5,1),
    pitch DECIMAL(4,1),
    roll DECIMAL(5,1),
    pressure DECIMAL(7,3),
    temperature DECIMAL(5,2),
    analog1 SMALLINT,
    analog2 SMALLINT,
    checksum CHAR(2)
);
"""
PNORS_DF100_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS pnors_df100_seq START 1;"
PNORS_DF100_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnors_df100_date_time "
    "ON pnors_df100(measurement_date, measurement_time);",
]

# PNORS12 (DF101/102) - Consolidated from pnors_df101 and pnors_df102
PNORS12_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pnors12 (
    record_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    data_format TINYINT NOT NULL CHECK (data_format IN (101, 102)),
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
PNORS12_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS pnors12_seq START 1;"
PNORS12_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnors12_date_time "
    "ON pnors12(measurement_date, measurement_time);",
    "CREATE INDEX IF NOT EXISTS idx_pnors12_data_format ON pnors12(data_format);",
]

# PNORS34 (DF103/104) - Consolidated from pnors_df103 and pnors_df104
PNORS34_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pnors34 (
    record_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    data_format TINYINT NOT NULL CHECK (data_format IN (103, 104)),
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
PNORS34_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS pnors34_seq START 1;"
PNORS34_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnors34_date_time "
    "ON pnors34(measurement_date, measurement_time);",
    "CREATE INDEX IF NOT EXISTS idx_pnors34_data_format ON pnors34(data_format);",
]

# ============================================================================
# PNORC FAMILY - Velocity Data
# ============================================================================

# PNORC DF100
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

# PNORC12 (DF101/102) - Consolidated
PNORC12_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pnorc12 (
    record_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    data_format TINYINT NOT NULL CHECK (data_format IN (101, 102)),
    original_sentence TEXT NOT NULL,
    measurement_date CHAR(6) NOT NULL,
    measurement_time CHAR(6) NOT NULL,
    cell_index SMALLINT NOT NULL,
    cell_distance DECIMAL(8,3),
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
PNORC12_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS pnorc12_seq START 1;"
PNORC12_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnorc12_date_time "
    "ON pnorc12(measurement_date, measurement_time);",
    "CREATE INDEX IF NOT EXISTS idx_pnorc12_cell ON pnorc12(cell_index);",
    "CREATE INDEX IF NOT EXISTS idx_pnorc12_data_format ON pnorc12(data_format);",
]

# PNORC34 (DF103/104) - Consolidated with minimal fields
PNORC34_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pnorc34 (
    record_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    data_format TINYINT NOT NULL CHECK (data_format IN (103, 104)),
    original_sentence TEXT NOT NULL,
    measurement_date CHAR(6) NOT NULL,
    measurement_time CHAR(6) NOT NULL,
    cell_index SMALLINT NOT NULL,
    cell_distance DECIMAL(8,3),
    speed DECIMAL(8,4),
    direction DECIMAL(5,2),
    checksum CHAR(2)
);
"""
PNORC34_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS pnorc34_seq START 1;"
PNORC34_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnorc34_date_time "
    "ON pnorc34(measurement_date, measurement_time);",
    "CREATE INDEX IF NOT EXISTS idx_pnorc34_cell ON pnorc34(cell_index);",
    "CREATE INDEX IF NOT EXISTS idx_pnorc34_data_format ON pnorc34(data_format);",
]

# ============================================================================
# PNORH - Header Data (Consolidated from pnorh_df103 and pnorh_df104)
# ============================================================================

PNORH_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pnorh (
    record_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    data_format TINYINT NOT NULL CHECK (data_format IN (103, 104)),
    original_sentence TEXT NOT NULL,
    measurement_date CHAR(6) NOT NULL,
    measurement_time CHAR(6) NOT NULL,
    error_code INTEGER,
    status_code CHAR(8),
    checksum CHAR(2)
);
"""
PNORH_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS pnorh_seq START 1;"
PNORH_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnorh_date_time ON pnorh(measurement_date, measurement_time);",
    "CREATE INDEX IF NOT EXISTS idx_pnorh_data_format ON pnorh(data_format);",
]

# ============================================================================
# WAVE DATA TABLES
# ============================================================================

# PNORE (renamed from echo_data) - Wave Energy Density Spectrum
PNORE_DATA_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pnore_data (
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
PNORE_DATA_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS pnore_data_seq START 1;"
PNORE_DATA_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnore_date_time "
    "ON pnore_data(measurement_date, measurement_time);",
]

# PNORW - Wave Bulk Parameters
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
    hm0 DECIMAL(5,2),
    h3 DECIMAL(5,2),
    h10 DECIMAL(5,2),
    hmax DECIMAL(5,2),
    tm02 DECIMAL(5,2),
    tp DECIMAL(5,2),
    tz DECIMAL(5,2),
    dir_tp DECIMAL(6,2),
    spr_tp DECIMAL(6,2),
    main_dir DECIMAL(6,2),
    uni_index DECIMAL(5,2),
    mean_pressure DECIMAL(5,2),
    num_no_detects INTEGER,
    num_bad_detects INTEGER,
    near_surface_speed DECIMAL(5,2),
    near_surface_dir DECIMAL(6,2),
    wave_error_code CHAR(4),
    checksum CHAR(2)
);
"""
PNORW_DATA_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS pnorw_data_seq START 1;"
PNORW_DATA_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnorw_date_time "
    "ON pnorw_data(measurement_date, measurement_time);",
]

# PNORB - Wave Band Parameters
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

# PNORF - Fourier Coefficient Spectra
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

# PNORWD - Wave Directional Spectra
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
    step_frequency DECIMAL(5,2) CHECK (step_frequency >= 0 AND step_frequency <= 10),
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

# PNORA - Altimeter Data
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
# LINKING VIEWS - Join related records by date/time
# ============================================================================

# Wave measurement view - links all wave data
WAVE_MEASUREMENT_VIEW_SQL = """
CREATE OR REPLACE VIEW wave_measurement AS
SELECT
    w.record_id,
    w.received_at,
    w.measurement_date,
    w.measurement_time,
    w.spectrum_basis,
    w.processing_method,
    w.hm0, w.h3, w.h10, w.hmax,
    w.tm02, w.tp, w.tz,
    w.dir_tp, w.spr_tp, w.main_dir,
    w.wave_error_code,
    e.energy_densities,
    e.start_frequency AS energy_start_freq,
    e.step_frequency AS energy_step_freq,
    e.num_frequencies AS energy_num_freq
FROM pnorw_data w
LEFT JOIN pnore_data e
    ON w.measurement_date = e.measurement_date
    AND w.measurement_time = e.measurement_time;
"""

# Full Wave measurement view - links all wave-related tables (PNORE, PNORB, PNORF, PNORWD)
WAVE_MEASUREMENT_FULL_VIEW_SQL = """
CREATE OR REPLACE VIEW wave_measurement_full AS
SELECT
    w.record_id,
    w.received_at,
    w.measurement_date,
    w.measurement_time,
    w.spectrum_basis,
    w.hm0, w.tp, w.main_dir,
    e.energy_densities,
    e.start_frequency AS energy_start_freq,
    e.step_frequency AS energy_step_freq,
    b.hmo AS band_hm0,
    b.tp AS band_tp,
    b.main_dir AS band_main_dir,
    f.coefficients,
    f.coefficient_flag,
    wd.values AS directional_values,
    wd.direction_type
FROM pnorw_data w
LEFT JOIN pnore_data e
    ON w.measurement_date = e.measurement_date
    AND w.measurement_time = e.measurement_time
LEFT JOIN pnorb_data b
    ON w.measurement_date = b.measurement_date
    AND w.measurement_time = b.measurement_time
LEFT JOIN pnorf_data f
    ON w.measurement_date = f.measurement_date
    AND w.measurement_time = f.measurement_time
LEFT JOIN pnorwd_data wd
    ON w.measurement_date = wd.measurement_date
    AND w.measurement_time = wd.measurement_time;
"""

# Current profile view for DF100
CURRENT_PROFILE_DF100_VIEW_SQL = """
CREATE OR REPLACE VIEW current_profile_df100 AS
SELECT
    s.record_id AS sensor_id,
    s.received_at,
    s.measurement_date,
    s.measurement_time,
    s.heading, s.pitch, s.roll, s.pressure, s.temperature,
    c.cell_index, c.vel1, c.vel2, c.vel3, c.vel4, c.speed, c.direction
FROM pnors_df100 s
JOIN pnorc_df100 c
    ON s.measurement_date = c.measurement_date
    AND s.measurement_time = c.measurement_time;
"""

# Current profile view for DF101/102
CURRENT_PROFILE_12_VIEW_SQL = """
CREATE OR REPLACE VIEW current_profile_12 AS
SELECT
    s.record_id AS sensor_id,
    s.data_format,
    s.received_at,
    s.measurement_date,
    s.measurement_time,
    s.heading, s.pitch, s.roll, s.pressure, s.temperature,
    c.cell_index, c.cell_distance, c.vel1, c.vel2, c.vel3, c.vel4
FROM pnors12 s
JOIN pnorc12 c
    ON s.measurement_date = c.measurement_date
    AND s.measurement_time = c.measurement_time
    AND s.data_format = c.data_format;
"""

# Current profile view for DF103/104
CURRENT_PROFILE_34_VIEW_SQL = """
CREATE OR REPLACE VIEW current_profile_34 AS
SELECT
    h.record_id AS header_id,
    h.data_format,
    h.received_at,
    h.measurement_date,
    h.measurement_time,
    h.error_code, h.status_code,
    s.heading, s.pitch, s.roll, s.pressure, s.temperature,
    c.cell_index, c.cell_distance, c.speed, c.direction
FROM pnorh h
JOIN pnors34 s
    ON h.measurement_date = s.measurement_date
    AND h.measurement_time = s.measurement_time
    AND h.data_format = s.data_format
JOIN pnorc34 c
    ON h.measurement_date = c.measurement_date
    AND h.measurement_time = c.measurement_time
    AND h.data_format = c.data_format;
"""


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
    # Configuration - PNORI family
    PNORI_SEQUENCE_SQL,
    PNORI_TABLE_SQL,
    *PNORI_INDEXES_SQL,
    PNORI12_SEQUENCE_SQL,
    PNORI12_TABLE_SQL,
    *PNORI12_INDEXES_SQL,
    # PNORS family
    PNORS_DF100_SEQUENCE_SQL,
    PNORS_DF100_TABLE_SQL,
    *PNORS_DF100_INDEXES_SQL,
    PNORS12_SEQUENCE_SQL,
    PNORS12_TABLE_SQL,
    *PNORS12_INDEXES_SQL,
    PNORS34_SEQUENCE_SQL,
    PNORS34_TABLE_SQL,
    *PNORS34_INDEXES_SQL,
    # PNORC family
    PNORC_DF100_SEQUENCE_SQL,
    PNORC_DF100_TABLE_SQL,
    *PNORC_DF100_INDEXES_SQL,
    PNORC12_SEQUENCE_SQL,
    PNORC12_TABLE_SQL,
    *PNORC12_INDEXES_SQL,
    PNORC34_SEQUENCE_SQL,
    PNORC34_TABLE_SQL,
    *PNORC34_INDEXES_SQL,
    # PNORH
    PNORH_SEQUENCE_SQL,
    PNORH_TABLE_SQL,
    *PNORH_INDEXES_SQL,
    # Wave data tables
    PNORE_DATA_SEQUENCE_SQL,
    PNORE_DATA_TABLE_SQL,
    *PNORE_DATA_INDEXES_SQL,
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
    # Linking views
    WAVE_MEASUREMENT_VIEW_SQL,
    WAVE_MEASUREMENT_FULL_VIEW_SQL,
    CURRENT_PROFILE_DF100_VIEW_SQL,
    CURRENT_PROFILE_12_VIEW_SQL,
    CURRENT_PROFILE_34_VIEW_SQL,
]
