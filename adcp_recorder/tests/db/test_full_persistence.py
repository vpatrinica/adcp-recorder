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
        
        results = query_sensor_data(db)
        assert len(results) == 1
        assert float(results[0]["battery"]) == 14.4
        assert float(results[0]["heading"]) == 275.9

    def test_pnorc_persistence(self, db):
        # PNORC: date, time, cell_index, vel1, vel2, vel3, checksum
        sentence = "$PNORC,102115,090715,1,0.123,-0.456,0.012*XX"
        msg = PNORC.from_nmea(sentence)
        record_id = insert_velocity_data(db, sentence, msg.to_dict())
        assert record_id > 0
        
        results = query_velocity_data(db)
        assert len(results) == 1
        assert results[0]["cell_index"] == 1
        assert float(results[0]["vel1"]) == 0.123

    def test_pnorh_persistence(self, db):
        # PNORH3: date, time, num_cells, first_cell, ping_count, checksum
        sentence = "$PNORH3,102115,090715,20,1,50*XX"
        msg = PNORH3.from_nmea(sentence)
        record_id = insert_header_data(db, sentence, msg.to_dict())
        assert record_id > 0
        
        results = query_header_data(db)
        assert len(results) == 1
        assert results[0]["sentence_type"] == "PNORH3"
        assert results[0]["num_cells"] == 20

    def test_pnorw_persistence(self, db):
        sentence = "$PNORW,102115,090715,1.5,2.5,10.0,180.0*XX"
        msg = PNORW.from_nmea(sentence)
        record_id = insert_pnorw_data(db, sentence, msg.to_dict())
        assert record_id > 0
        
        results = query_pnorw_data(db)
        assert len(results) == 1
        assert results[0]["sig_wave_height"] == 1.5

    def test_pnorb_persistence(self, db):
        sentence = "$PNORB,102115,090715,0.1,0.2,0.05,25.5,95*XX"
        msg = PNORB.from_nmea(sentence)
        record_id = insert_pnorb_data(db, sentence, msg.to_dict())
        assert record_id > 0
        
        results = query_pnorb_data(db)
        assert len(results) == 1
        assert results[0]["bottom_dist"] == 25.5

    def test_pnore_persistence(self, db):
        sentence = "$PNORE,102115,090715,1,50,60,70,80*XX"
        msg = PNORE.from_nmea(sentence)
        record_id = insert_echo_data(db, sentence, msg.to_dict())
        assert record_id > 0
        
        results = query_echo_data(db)
        assert len(results) == 1
        assert results[0]["echo1"] == 50

    def test_pnorf_persistence(self, db):
        sentence = "$PNORF,102115,090715,1000.0,25.0,90.0*XX"
        msg = PNORF.from_nmea(sentence)
        record_id = insert_pnorf_data(db, sentence, msg.to_dict())
        assert record_id > 0
        
        results = query_pnorf_data(db)
        assert len(results) == 1
        assert results[0]["frequency"] == 1000.0

    def test_pnorwd_persistence(self, db):
        sentence = "$PNORWD,102115,090715,10,180.0,20.0,50.0*XX"
        msg = PNORWD.from_nmea(sentence)
        record_id = insert_pnorwd_data(db, sentence, msg.to_dict())
        assert record_id > 0
        
        results = query_pnorwd_data(db)
        assert len(results) == 1
        assert results[0]["freq_bin"] == 10

    def test_pnora_persistence(self, db):
        sentence = "$PNORA,102115,090715,1,15.50,95*XX"
        msg = PNORA.from_nmea(sentence)
        record_id = insert_pnora_data(db, sentence, msg.to_dict())
        assert record_id > 0
        
        results = query_pnora_data(db)
        assert len(results) == 1
        assert results[0]["distance"] == 15.5


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
            "vel1": 1.0, "vel2": 1.0, "vel3": 1.0,
            "corr1": 0, "corr2": 0, "corr3": 0,
            "amp1": 0, "amp2": 0, "amp3": 0, "amp4": 0,
            "checksum": "XX"
        }
        with pytest.raises(duckdb.ConstraintException):
            insert_velocity_data(db, "$PNORC...", valid)

    def test_pnorh_constraint(self, db):
        valid = {
            "sentence_type": "PNORH3",
            "date": "101010", "time": "101010",
            "num_cells": None, # VIOLATION
            "first_cell": 1, "ping_count": 10,
            "coordinate_system": "ENU", "profile_interval": 1.0,
            "checksum": "XX"
        }
        with pytest.raises(duckdb.ConstraintException):
            insert_header_data(db, "$PNORH...", valid)

    def test_pnorw_constraint(self, db):
        valid = {
            "sentence_type": "PNORW",
            "date": "101010", "time": "101010",
            "sig_wave_height": "NOT A NUMBER", # VIOLATION
            "max_wave_height": 1.0, "peak_period": 1.0, "mean_direction": 1.0,
            "checksum": "XX"
        }
        with pytest.raises((duckdb.ConversionException, duckdb.BinderException)):
             insert_pnorw_data(db, "$PNORW...", valid)

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
            "cell_index": None, # VIOLATION
            "echo1": 0, "echo2": 0, "echo3": 0, "echo4": 0,
            "checksum": "XX"
        }
        with pytest.raises(duckdb.ConstraintException):
             insert_echo_data(db, "$PNORE...", valid)

    def test_pnorf_constraint(self, db):
        valid = {
            "sentence_type": "PNORF",
            "date": None, # VIOLATION (NOT NULL)
            "time": "101010",
            "frequency": 1000.0,
            "bandwidth": 10, "transmit_power": 10,
            "checksum": "XX"
        }
        with pytest.raises(duckdb.ConstraintException):
             insert_pnorf_data(db, "$PNORF...", valid)

    def test_pnorwd_constraint(self, db):
        valid = {
            "sentence_type": "PNORWD",
            "date": None, # VIOLATION
            "time": "101010", 
            "freq_bin": 1, "direction": 0, "spread_angle": 0, "energy": 0,
            "checksum": "XX"
        }
        with pytest.raises(duckdb.ConstraintException):
             insert_pnorwd_data(db, "$PNORWD...", valid)

    def test_pnora_constraint(self, db):
        valid = {
            "sentence_type": "PNORA",
            "date": "101010", "time": "101010",
            "method": 1,
            "distance": "NAN", # VIOLATION
            "quality": 100, "checksum": "XX"
        }
        with pytest.raises(Exception):
             insert_pnora_data(db, "$PNORA...", valid)
