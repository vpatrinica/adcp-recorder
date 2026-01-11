"""SQL schema definitions for DuckDB tables.

Defines table schemas for raw NMEA sentence storage and error tracking.
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

# Create sequence for line_id
RAW_LINES_SEQUENCE_SQL = """
CREATE SEQUENCE IF NOT EXISTS raw_lines_seq START 1;
"""

# Indexes for raw_lines table
RAW_LINES_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_raw_lines_received_at ON raw_lines(received_at);",
    "CREATE INDEX IF NOT EXISTS idx_raw_lines_record_type ON raw_lines(record_type);",
    "CREATE INDEX IF NOT EXISTS idx_raw_lines_parse_status ON raw_lines(parse_status);",
]

# Parse errors table - stores sentences that failed parsing
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

# Create sequence for error_id
PARSE_ERRORS_SEQUENCE_SQL = """
CREATE SEQUENCE IF NOT EXISTS parse_errors_seq START 1;
"""

# Indexes for parse_errors table
PARSE_ERRORS_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_errors_received_at ON parse_errors(received_at);",
    "CREATE INDEX IF NOT EXISTS idx_errors_type ON parse_errors(error_type);",
    "CREATE INDEX IF NOT EXISTS idx_errors_prefix ON parse_errors(attempted_prefix);",
]

# All schema creation statements in order
ALL_SCHEMA_SQL = [
    RAW_LINES_SEQUENCE_SQL,
    RAW_LINES_TABLE_SQL,
    *RAW_LINES_INDEXES_SQL,
    PARSE_ERRORS_SEQUENCE_SQL,
    PARSE_ERRORS_TABLE_SQL,
    *PARSE_ERRORS_INDEXES_SQL,
]

# PNORI configurations table - stores parsed configuration messages
PNORI_CONFIGURATIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pnori_configurations (
    config_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    sentence_type VARCHAR(10) NOT NULL 
        CHECK (sentence_type IN ('PNORI', 'PNORI1', 'PNORI2')),
    original_sentence TEXT NOT NULL,
    
    -- Configuration fields
    instrument_type_name VARCHAR(20) NOT NULL,
    instrument_type_code TINYINT NOT NULL 
        CHECK (instrument_type_code IN (0, 2, 4)),
    head_id VARCHAR(30) NOT NULL 
        CHECK (length(head_id) BETWEEN 1 AND 30),
    beam_count TINYINT NOT NULL 
        CHECK (beam_count > 0 AND beam_count <= 4),
    cell_count SMALLINT NOT NULL 
        CHECK (cell_count > 0 AND cell_count <= 1000),
    blanking_distance DECIMAL(5,2) NOT NULL 
        CHECK (blanking_distance > 0 AND blanking_distance <= 100),
    cell_size DECIMAL(5,2) NOT NULL 
        CHECK (cell_size > 0 AND cell_size <= 100),
    coord_system_name VARCHAR(10) NOT NULL 
        CHECK (coord_system_name IN ('ENU', 'XYZ', 'BEAM')),
    coord_system_code TINYINT NOT NULL 
        CHECK (coord_system_code IN (0, 1, 2)),
    
    -- Metadata
    checksum CHAR(2),
    
    -- Cross-field validation
    CONSTRAINT valid_signature_config CHECK (
        NOT (instrument_type_code = 4 AND beam_count != 4)
    ),
    CONSTRAINT valid_coord_mapping CHECK (
        (coord_system_name = 'ENU' AND coord_system_code = 0) OR
        (coord_system_name = 'XYZ' AND coord_system_code = 1) OR
        (coord_system_name = 'BEAM' AND coord_system_code = 2)
    )
);
"""

# Create sequence for config_id
PNORI_CONFIGURATIONS_SEQUENCE_SQL = """
CREATE SEQUENCE IF NOT EXISTS pnori_configurations_seq START 1;
"""

# Indexes for pnori_configurations table
PNORI_CONFIGURATIONS_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnori_head_id ON pnori_configurations(head_id);",
    "CREATE INDEX IF NOT EXISTS idx_pnori_received_at ON pnori_configurations(received_at);",
    "CREATE INDEX IF NOT EXISTS idx_pnori_sentence_type ON pnori_configurations(sentence_type);",
]

# Sensor Data Table (PNORS Family)
SENSOR_DATA_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS sensor_data (
    record_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    sentence_type VARCHAR(10) NOT NULL 
        CHECK (sentence_type IN ('PNORS', 'PNORS1', 'PNORS2', 'PNORS3', 'PNORS4')),
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
    salinity DECIMAL(4,1),
    checksum CHAR(2)
);
"""

SENSOR_DATA_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS sensor_data_seq START 1;"
SENSOR_DATA_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_sensor_date_time ON sensor_data(measurement_date, measurement_time);",
    "CREATE INDEX IF NOT EXISTS idx_sensor_received_at ON sensor_data(received_at);",
]

# Velocity Data Table (PNORC Family)
VELOCITY_DATA_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS velocity_data (
    record_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    sentence_type VARCHAR(10) NOT NULL 
        CHECK (sentence_type IN ('PNORC', 'PNORC1', 'PNORC2', 'PNORC3', 'PNORC4')),
    original_sentence TEXT NOT NULL,
    measurement_date CHAR(6) NOT NULL,
    measurement_time CHAR(6) NOT NULL,
    cell_index SMALLINT NOT NULL CHECK (cell_index > 0),
    vel1 DECIMAL(8,4) CHECK (vel1 >= -10 AND vel1 <= 10),
    vel2 DECIMAL(8,4) CHECK (vel2 >= -10 AND vel2 <= 10),
    vel3 DECIMAL(8,4) CHECK (vel3 >= -10 AND vel3 <= 10),
    corr1 TINYINT CHECK (corr1 >= 0 AND corr1 <= 100),
    corr2 TINYINT CHECK (corr2 >= 0 AND corr2 <= 100),
    corr3 TINYINT CHECK (corr3 >= 0 AND corr3 <= 100),
    amp1 TINYINT CHECK (amp1 >= 0 AND amp1 <= 255),
    amp2 TINYINT CHECK (amp2 >= 0 AND amp2 <= 255),
    amp3 TINYINT CHECK (amp3 >= 0 AND amp3 <= 255),
    amp4 TINYINT CHECK (amp4 >= 0 AND amp4 <= 255),
    checksum CHAR(2)
);
"""

VELOCITY_DATA_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS velocity_data_seq START 1;"
VELOCITY_DATA_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_velocity_date_time ON velocity_data(measurement_date, measurement_time);",
    "CREATE INDEX IF NOT EXISTS idx_velocity_cell ON velocity_data(cell_index);",
]

# Header Data Table (PNORH Family)
HEADER_DATA_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS header_data (
    record_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    sentence_type VARCHAR(10) NOT NULL 
        CHECK (sentence_type IN ('PNORH3', 'PNORH4')),
    original_sentence TEXT NOT NULL,
    measurement_date CHAR(6) NOT NULL,
    measurement_time CHAR(6) NOT NULL,
    num_cells SMALLINT NOT NULL CHECK (num_cells > 0),
    first_cell SMALLINT NOT NULL CHECK (first_cell > 0),
    ping_count INTEGER NOT NULL CHECK (ping_count > 0),
    coord_system VARCHAR(10),
    profile_interval DECIMAL(7,1),
    checksum CHAR(2)
);
"""

HEADER_DATA_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS header_data_seq START 1;"

# Echo Intensity Data Table (PNORE Family)
ECHO_DATA_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS echo_data (
    record_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    sentence_type VARCHAR(10) NOT NULL CHECK (sentence_type = 'PNORE'),
    original_sentence TEXT NOT NULL,
    measurement_date CHAR(6) NOT NULL,
    measurement_time CHAR(6) NOT NULL,
    cell_index SMALLINT NOT NULL CHECK (cell_index > 0),
    echo1 TINYINT CHECK (echo1 >= 0 AND echo1 <= 255),
    echo2 TINYINT CHECK (echo2 >= 0 AND echo2 <= 255),
    echo3 TINYINT CHECK (echo3 >= 0 AND echo3 <= 255),
    echo4 TINYINT CHECK (echo4 >= 0 AND echo4 <= 255),
    checksum CHAR(2)
);
"""

ECHO_DATA_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS echo_data_seq START 1;"
ECHO_DATA_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_echo_date_time ON echo_data(measurement_date, measurement_time);",
    "CREATE INDEX IF NOT EXISTS idx_echo_cell ON echo_data(cell_index);",
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
    sig_wave_height DECIMAL(5,2),
    max_wave_height DECIMAL(5,2),
    peak_period DECIMAL(5,1),
    mean_direction DECIMAL(5,1),
    checksum CHAR(2)
);
"""
PNORW_DATA_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS pnorw_data_seq START 1;"
PNORW_DATA_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnorw_date_time ON pnorw_data(measurement_date, measurement_time);",
]

# Bottom Track Data (PNORB)
PNORB_DATA_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pnorb_data (
    record_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    sentence_type VARCHAR(10) NOT NULL CHECK (sentence_type = 'PNORB'),
    original_sentence TEXT NOT NULL,
    measurement_date CHAR(6) NOT NULL,
    measurement_time CHAR(6) NOT NULL,
    vel_east DECIMAL(8,4),
    vel_north DECIMAL(8,4),
    vel_up DECIMAL(8,4),
    bottom_dist DECIMAL(6,2),
    quality TINYINT,
    checksum CHAR(2)
);
"""
PNORB_DATA_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS pnorb_data_seq START 1;"
PNORB_DATA_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnorb_date_time ON pnorb_data(measurement_date, measurement_time);",
]

# Frequency Data (PNORF)
PNORF_DATA_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pnorf_data (
    record_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    sentence_type VARCHAR(10) NOT NULL CHECK (sentence_type = 'PNORF'),
    original_sentence TEXT NOT NULL,
    measurement_date CHAR(6) NOT NULL,
    measurement_time CHAR(6) NOT NULL,
    frequency DECIMAL(7,1),
    bandwidth DECIMAL(5,1),
    transmit_power DECIMAL(5,1),
    checksum CHAR(2)
);
"""
PNORF_DATA_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS pnorf_data_seq START 1;"
PNORF_DATA_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnorf_date_time ON pnorf_data(measurement_date, measurement_time);",
]

# Wave Directional Data (PNORWD)
PNORWD_DATA_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pnorwd_data (
    record_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    sentence_type VARCHAR(10) NOT NULL CHECK (sentence_type = 'PNORWD'),
    original_sentence TEXT NOT NULL,
    measurement_date CHAR(6) NOT NULL,
    measurement_time CHAR(6) NOT NULL,
    freq_bin TINYINT,
    direction DECIMAL(5,1),
    spread_angle DECIMAL(5,1),
    energy DECIMAL(8,4),
    checksum CHAR(2)
);
"""
PNORWD_DATA_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS pnorwd_data_seq START 1;"
PNORWD_DATA_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnorwd_date_time ON pnorwd_data(measurement_date, measurement_time);",
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
    method TINYINT,
    distance DECIMAL(6,2),
    quality TINYINT,
    checksum CHAR(2)
);
"""
PNORA_DATA_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS pnora_data_seq START 1;"
PNORA_DATA_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pnora_date_time ON pnora_data(measurement_date, measurement_time);",
]

WAVE_DATA_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS wave_data_seq START 1;"

# All schema creation statements in order
ALL_SCHEMA_SQL = [
    RAW_LINES_SEQUENCE_SQL,
    RAW_LINES_TABLE_SQL,
    *RAW_LINES_INDEXES_SQL,
    PARSE_ERRORS_SEQUENCE_SQL,
    PARSE_ERRORS_TABLE_SQL,
    *PARSE_ERRORS_INDEXES_SQL,
    PNORI_CONFIGURATIONS_SEQUENCE_SQL,
    PNORI_CONFIGURATIONS_TABLE_SQL,
    *PNORI_CONFIGURATIONS_INDEXES_SQL,
    SENSOR_DATA_SEQUENCE_SQL,
    SENSOR_DATA_TABLE_SQL,
    *SENSOR_DATA_INDEXES_SQL,
    VELOCITY_DATA_SEQUENCE_SQL,
    VELOCITY_DATA_TABLE_SQL,
    *VELOCITY_DATA_INDEXES_SQL,
    HEADER_DATA_SEQUENCE_SQL,
    HEADER_DATA_TABLE_SQL,
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
