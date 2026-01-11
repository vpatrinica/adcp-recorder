"""Comprehensive persistence tests for ALL message types.

Verifies:
1. Successful insertion and retrieval for every message type.
2. Database constraint enforcement (error handling) for every message type.
"""

import pytest
import duckdb
from adcp_recorder.db.db import DatabaseManager
from adcp_recorder.parsers.pnori import PNORI
from adcp_recorder.parsers.pnors import PNORS
from adcp_recorder.parsers.pnorc import PNORC
from adcp_recorder.parsers.pnorh import PNORH3
from adcp_recorder.parsers.pnorw import PNORW
from adcp_recorder.parsers.pnorb import PNORB
from adcp_recorder.parsers.pnore import PNORE
from adcp_recorder.parsers.pnorf import PNORF
from adcp_recorder.parsers.pnorwd import PNORWD
from adcp_recorder.parsers.pnora import PNORA
from adcp_recorder.db.operations import (
    insert_pnori_configuration, query_pnori_configurations,
    insert_sensor_data, query_sensor_data,
    insert_velocity_data, query_velocity_data,
    insert_header_data, query_header_data,
    insert_pnorw_data, query_pnorw_data,
    insert_pnorb_data, query_pnorb_data,
    insert_echo_data, query_echo_data,
    insert_pnorf_data, query_pnorf_data,
    insert_pnorwd_data, query_pnorwd_data,
    insert_pnora_data, query_pnora_data,
)


@pytest.fixture
def db():
    """Create a temporary in-memory database for testing."""
    manager = DatabaseManager(":memory:")
    manager.initialize_schema()
    conn = manager.get_connection()
    yield conn
    conn.close()


class TestPersistenceSuccess:
    """Validate successful insertion and complete retrieval for all types."""

    def test_pnori_persistence(self, db):
        sentence = "$PNORI,4,Signature1000,4,20,0.20,1.00,0*2E"
        # Manually constructing expected dict to avoid relying on parser in this specific test? 
        # No, better to use parser to ensure end-to-end alignment.
        msg = PNORI.from_nmea(sentence)
        record_id = insert_pnori_configuration(db, msg.to_dict(), sentence)
        assert record_id > 0
        
        results = query_pnori_configurations(db)
        assert len(results) == 1
        row = results[0]
        assert row["sentence_type"] == "PNORI"
        assert row["head_id"] == "Signature1000"
        assert row["cell_size"] == 1.00

    def test_pnors_persistence(self, db):
        sentence = "$PNORS,102115,090715,00000000,2A480000,14.4,1523.0,275.9,15.7,2.3,0.0,22.45,0,0*XX"
        msg = PNORS.from_nmea(sentence)
        record_id = insert_sensor_data(db, sentence, msg.to_dict())
        assert record_id > 0
        
        # Query from new pnors_df100 table
        # Columns: record_id, received_at, original_sentence, measurement_date, measurement_time, error_code, status_code, battery, ...
        results = db.execute("SELECT * FROM pnors_df100").fetchall()
        assert len(results) == 1
        assert float(results[0][7]) == 14.4  # battery (index 7)
        assert float(results[0][9]) == 275.9  # heading (index 9)

    def test_pnorc_persistence(self, db):
        # PNORC: 19 fields
        # vel1=0.5, vel2=0.1, vel3=0.2, vel4=0.3, speed=1.5, dir=180.0, amp_unit=C
        sentence = "$PNORC,102115,090715,1,0.5,0.1,0.2,0.3,1.5,180.0,C,100,101,102,103,90,91,92,93*41"
        msg = PNORC.from_nmea(sentence)
        record_id = insert_velocity_data(db, sentence, msg.to_dict())
        assert record_id > 0
        
        # Query from new pnorc_df100 table
        # Columns: id, recv, orig, date, time, cell, vel1, vel2, vel3, vel4, speed, dir, amp_unit...
        results = db.execute("SELECT * FROM pnorc_df100").fetchall()
        assert len(results) == 1
        assert results[0][5] == 1  # cell_index
        assert float(results[0][6]) == 0.5  # vel1
        assert float(results[0][10]) == 1.5 # speed
        assert float(results[0][11]) == 180.0 # direction

    def test_pnorh_persistence(self, db):
        # PNORH3: tagged (minimal)
        sentence = "$PNORH3,DATE=211021,TIME=090715,EC=0,SC=2A4C0000*XX"
        msg = PNORH3.from_nmea(sentence)
        record_id = insert_header_data(db, sentence, msg.to_dict())
        assert record_id > 0
        
        # Query from new pnorh_df103 table
        results = db.execute("SELECT * FROM pnorh_df103").fetchall()
        assert len(results) == 1
        # Minimal PNORH3 doesn't populate num_cells (index 5)
        # assert results[0][5] == 20 
        assert int(results[0][5]) == 0  # error_code

    def test_pnorw_persistence(self, db):
        sentence = "$PNORW,102115,090715,1,1,1.5,1.6,1.7,2.5,5.0,6.0,5.5,180.0,10.0,180.0,1.0,10.0,0,0,0.5,90.0,0000*XX"
        msg = PNORW.from_nmea(sentence)
        record_id = insert_pnorw_data(db, sentence, msg.to_dict())
        assert record_id > 0
        
        results = query_pnorw_data(db)
        assert len(results) == 1
        assert results[0]["hm0"] == 1.5

    def test_pnorb_persistence(self, db):
        sentence = "$PNORB,102115,090715,1,4,0.02,0.20,0.27,7.54,12.00,82.42,75.46,82.10,0000*XX"
        msg = PNORB.from_nmea(sentence)
        record_id = insert_pnorb_data(db, sentence, msg.to_dict())
        assert record_id > 0
        
        results = db.execute("SELECT * FROM pnorb_data WHERE record_id = ?", [record_id]).fetchall()
        assert len(results) == 1
        # Check new wave band parameter fields (columns: record_id, received_at, sentence_type, original_sentence, date, time, spectrum_basis, processing_method, freq_low, freq_high, hmo, tm02, tp, dirtp, sprtp, main_dir, wave_error_code, checksum)
        assert results[0][6] == 1  # spectrum_basis
        assert results[0][7] == 4  # processing_method
        assert float(results[0][8]) == 0.02  # freq_low
        assert float(results[0][9]) == 0.20  # freq_high
        assert float(results[0][10]) == 0.27  # hmo

    def test_pnore_persistence(self, db):
        # PNORE now uses energy density spectrum format
        sentence = "$PNORE,102115,090715,1,0.02,0.01,5,1.5,2.5,3.5,4.5,5.5*XX"
        msg = PNORE.from_nmea(sentence)
        record_id = insert_echo_data(db, sentence, msg.to_dict())
        assert record_id > 0
        
        # Columns: record_id, received_at, sentence_type, original_sentence, measurement_date, measurement_time, spectrum_basis, ...
        results = db.execute("SELECT * FROM echo_data").fetchall()
        assert len(results) == 1
        assert results[0][6] == 1  # spectrum_basis (index 6)

    def test_pnorf_persistence(self, db):
        # PNORF now uses Fourier coefficient format
        sentence = "$PNORF,A1,102115,090715,1,0.02,0.01,3,0.5,1.5,2.5*XX"
        msg = PNORF.from_nmea(sentence)
        record_id = insert_pnorf_data(db, sentence, msg.to_dict())
        assert record_id > 0
        
        # Columns: record_id, received_at, sentence_type, original_sentence, coefficient_flag, measurement_date, ...
        results = db.execute("SELECT * FROM pnorf_data").fetchall()
        assert len(results) == 1
        assert results[0][4] == "A1"  # coefficient_flag (index 4)

    def test_pnorwd_persistence(self, db):
        # PNORWD now uses directional spectra format
        sentence = "$PNORWD,MD,102115,090715,1,0.02,0.01,3,45.0,90.0,135.0*XX"
        msg = PNORWD.from_nmea(sentence)
        record_id = insert_pnorwd_data(db, sentence, msg.to_dict())
        assert record_id > 0
        
        # Columns: record_id, received_at, sentence_type, original_sentence, direction_type, measurement_date, ...
        results = db.execute("SELECT * FROM pnorwd_data").fetchall()
        assert len(results) == 1
        assert results[0][4] == "MD"  # direction_type (index 4)

    def test_pnora_persistence(self, db):
        sentence = "$PNORA,151021,090715,10.5,15.50,1,00,0.0,10.0*XX"
        msg = PNORA.from_nmea(sentence)
        record_id = insert_pnora_data(db, sentence, msg.to_dict())
        assert record_id > 0
        
        results = query_pnora_data(db)
        assert len(results) == 1
        assert results[0]["altimeter_distance"] == 15.5
        assert results[0]["pressure"] == 10.5


class TestPersistenceConstraints:
    """Validate that the database rejects invalid data for all types."""

    def test_pnori_constraint(self, db):
        # Construct full valid dict but set required field to None
        valid_sentence = "$PNORI,4,S,4,20,0,1,0*XX"
        # We manually build dict to avoid valid_sentence parser errors
        valid_dict = {
            "sentence_type": "PNORI",
            "instrument_type_name": None, # VIOLATION
            "instrument_type_code": 4, "head_id": "S",
            "beam_count": 4, "cell_count": 20,
            "blanking_distance": 0.2, "cell_size": 1.0,
            "coord_system_name": "ENU", "coord_system_code": 0,
            "checksum": "XX"
        }
        with pytest.raises(duckdb.ConstraintException):
            insert_pnori_configuration(db, valid_dict, valid_sentence)

    def test_pnors_constraint(self, db):
        # Missing date
        valid = {
             "sentence_type": "PNORS",
             "date": None, # VIOLATION
             "time": "101010",
             "error_code": "0", "status_code": "0",
             "battery": 12.0, "sound_speed": 1500,
             "heading": 0, "pitch": 0, "roll": 0, "pressure": 0, "temperature": 20,
             "analog1": 0, "analog2": 0, "salinity": 0, "checksum": "XX"
        }
        with pytest.raises(duckdb.ConstraintException):
            insert_sensor_data(db, "$PNORS...", valid)

    def test_pnorc_constraint(self, db):
        valid = {
            "sentence_type": "PNORC",
            "date": "101010", "time": "101010",
            "cell_index": None, # VIOLATION
            "vel1": 1.0, "vel2": 1.0, "vel3": 1.0, "vel4": 1.0,
            "speed": 1.0, "direction": 180.0, "amp_unit": "C",
            "amp1": 0, "amp2": 0, "amp3": 0, "amp4": 0,
            "corr1": 0, "corr2": 0, "corr3": 0, "corr4": 0,
            "checksum": "XX"
        }
        with pytest.raises(duckdb.ConstraintException):
            insert_velocity_data(db, "$PNORC...", valid)

    def test_pnorh_constraint(self, db):
        valid = {
            "sentence_type": "PNORH3",
            "date": "211021", "time": "090715",
            "error_code": 0, "status_code": "00000000",
            "checksum": "XX"
        }
        
        # Violation: date is None
        invalid = valid.copy()
        invalid["date"] = None
        
        with pytest.raises(duckdb.ConstraintException):
            insert_header_data(db, "$PNORH...", invalid)

    def test_pnorw_constraint(self, db):
        valid = {
            "sentence_type": "PNORW",
            "date": "101010", "time": "120000",
            "hm0": 1.5, "checksum": "XX"
        }
        
        # Violation: invalid type for hm0
        invalid = valid.copy()
        invalid["hm0"] = "NOT A NUMBER"
        
        with pytest.raises((duckdb.ConversionException, duckdb.BinderException)):
            insert_pnorw_data(db, "$PNORW...", invalid)

    def test_pnorb_constraint(self, db):
        valid = {
            "sentence_type": "PNORB",
            "date": "101010", "time": "101010",
            "vel_east": 0, "vel_north": 0, "vel_up": 0,
            "bottom_dist": "garbage", # VIOLATION
            "quality": 100, "checksum": "XX"
        }
        with pytest.raises(Exception):
             insert_pnorb_data(db, "$PNORB...", valid)

    def test_pnore_constraint(self, db):
        valid = {
            "sentence_type": "PNORE",
            "date": "101010", "time": "101010",
            "spectrum_basis": 1,
            "start_frequency": 0.02, "step_frequency": 0.01,
            "num_frequencies": 2,
            "energy_densities": [1.0, 2.0],
            "checksum": None  # Missing checksum is OK
        }
        # Test with invalid spectrum_basis
        valid["spectrum_basis"] = 99  # VIOLATION
        with pytest.raises(duckdb.ConstraintException):
             insert_echo_data(db, "$PNORE...", valid)

    def test_pnorf_constraint(self, db):
        valid = {
            "sentence_type": "PNORF",
            "date": None, # VIOLATION (NOT NULL)
            "time": "101010",
            "coefficient_flag": "A1",
            "spectrum_basis": 1,
            "start_frequency": 0.02, "step_frequency": 0.01,
            "num_frequencies": 2,
            "coefficients": [1.0, 2.0],
            "checksum": "XX"
        }
        with pytest.raises(duckdb.ConstraintException):
             insert_pnorf_data(db, "$PNORF...", valid)

    def test_pnorwd_constraint(self, db):
        valid = {
            "sentence_type": "PNORWD",
            "date": None, # VIOLATION
            "time": "101010",
            "direction_type": "MD",
            "spectrum_basis": 1,
            "start_frequency": 0.02, "step_frequency": 0.01,
            "num_frequencies": 2,
            "values": [45.0, 90.0],
            "checksum": "XX"
        }
        with pytest.raises(duckdb.ConstraintException):
             insert_pnorwd_data(db, "$PNORWD...", valid)

    def test_pnora_constraint(self, db):
        valid = {
            "sentence_type": "PNORA",
            "date": "101010", "time": "101010",
            "pressure": 10.0,
            "distance": "NAN", # VIOLATION
            "quality": 100, "status": "01",
            "pitch": 0.0, "roll": 0.0,
            "checksum": "XX"
        }
        with pytest.raises(Exception):
             insert_pnora_data(db, "$PNORA...", valid)
