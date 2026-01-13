"""Targeted coverage tests for SerialProducer, SerialConsumer, and various parser edge cases."""

import time
from queue import Queue
from unittest.mock import Mock, patch

import pytest

from adcp_recorder.core.enums import CoordinateSystem, InstrumentType
from adcp_recorder.db.db import DatabaseManager
from adcp_recorder.parsers.pnora import PNORA
from adcp_recorder.parsers.pnorb import PNORB
from adcp_recorder.parsers.pnorc import PNORC, PNORC1, PNORC2, PNORC3, PNORC4
from adcp_recorder.parsers.pnore import PNORE
from adcp_recorder.parsers.pnorf import PNORF
from adcp_recorder.parsers.pnorh import PNORH3, PNORH4
from adcp_recorder.parsers.pnori import PNORI
from adcp_recorder.parsers.pnors import PNORS4
from adcp_recorder.parsers.pnorw import PNORW
from adcp_recorder.parsers.pnorwd import PNORWD
from adcp_recorder.parsers.utils import parse_tagged_field
from adcp_recorder.serial.consumer import MessageRouter, SerialConsumer
from adcp_recorder.serial.port_manager import SerialConnectionManager
from adcp_recorder.serial.producer import SerialProducer


def test_producer_unicode_decode_error_threshold(tmp_path):
    """Test hitting UnicodeDecodeError in producer without hitting is_binary_data."""
    manager = Mock(spec=SerialConnectionManager)
    manager.is_connected.return_value = True

    # invalid_data fails decode but is NOT binary by 10% rule
    invalid_data = b"ABCDEFG\x80HI"
    import itertools

    # Infinite empty bytes after invalid data
    manager.read_line.side_effect = itertools.chain([invalid_data], itertools.cycle([b""]))

    queue = Queue()
    producer = SerialProducer(manager, queue)

    with patch("adcp_recorder.serial.producer.logger") as mock_logger:
        producer.start()
        time.sleep(0.2)
        producer.stop()

        mock_logger.warning.assert_any_call(f"Failed to decode ASCII: {invalid_data[:50]}")
        assert queue.qsize() == 1


def test_consumer_unicode_decode_error(tmp_path):
    """Test handle UnicodeDecodeError in consumer."""
    db_path = tmp_path / "test_consumer_cov.db"
    db = DatabaseManager(str(db_path))
    queue = Queue()
    router = MessageRouter()

    consumer = SerialConsumer(queue, db, router)

    # Data that fails decode
    invalid_data = b"ABCDEFG\x80HI"
    queue.put(invalid_data)

    consumer.start()
    time.sleep(0.2)
    consumer.stop()

    conn = db.get_connection()
    errors = conn.execute("SELECT error_type FROM parse_errors").fetchall()
    assert len(errors) == 1
    assert errors[0][0] == "DECODE_ERROR"


def test_consumer_empty_sentence(tmp_path):
    """Test handling of empty or whitespace-only lines in consumer."""
    db_path = tmp_path / "test_consumer_empty.db"
    db = DatabaseManager(str(db_path))
    queue = Queue()
    router = MessageRouter()

    consumer = SerialConsumer(queue, db, router)
    queue.put(b"   \r\n")

    consumer.start()
    time.sleep(0.2)
    consumer.stop()

    conn = db.get_connection()
    count = conn.execute("SELECT count(*) FROM raw_lines").fetchone()[0]
    assert count == 0


def test_pnora_coverage():
    with pytest.raises(ValueError, match="Expected 9 fields for PNORA"):
        PNORA.from_nmea("$PNORA,1,2,3,4*00")
    with pytest.raises(ValueError, match="Invalid prefix"):
        PNORA.from_nmea("$NOTRA,1,2,3,4,5,6,7,8*00")
    msg = PNORA("151021", "090715", 1, 10.0, 95, "00", 0.0, 10.0)
    assert msg.to_dict()["sentence_type"] == "PNORA"


def test_pnorh_coverage():
    # PNORH3
    with pytest.raises(ValueError, match="Tagged field must contain '='"):
        PNORH3.from_nmea("$PNORH3,1,2,3,4*00")
    with pytest.raises(ValueError, match="Invalid prefix"):
        PNORH3.from_nmea("$NOTRH3,ID=1*00")

    # PNORH4
    with pytest.raises(ValueError, match="Expected 5 fields"):
        PNORH4.from_nmea("$PNORH4,1,2,3,4,5,6*00")
    with pytest.raises(ValueError, match="Invalid prefix"):
        # 5 fields to pass length check
        PNORH4.from_nmea("$NOTRH4,1,2,3,4*00")


def test_pnori_coverage():
    # Beam count validation
    with pytest.raises(ValueError, match="Beam count must be 1-4"):
        PNORI.from_nmea("$PNORI,4,Test,5,20,0.20,1.00,0*00")

    # Valid init
    msg = PNORI(InstrumentType.SIGNATURE, "H1", 4, 20, 0.2, 1.0, CoordinateSystem.ENU, "00")
    d = msg.to_dict()
    assert d["head_id"] == "H1"


def test_pnorw_family_coverage():
    # Covering missing branches in pnorw parsers - test invalid prefix with correct field counts
    test_cases = [
        (
            PNORW,
            "$NOTR,102115,090715,0,1,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0,0,0,0,0,0,0,0,0,0000*00",
        ),  # 22 fields
        (
            PNORB,
            "$NOTR,102115,090715,1,4,0.02,0.20,0.27,7.54,12.00,82.42,75.46,82.10,0000*00",
        ),  # 14 fields
        (PNORE, "$NOTR,102115,090715,1,0.02,0.01,2,1.5,2.5*00"),  # 9 fields
        (PNORF, "$NOTR,A1,102115,090715,1,0.02,0.01,2,0.5,1.5*00"),  # 10 fields
        (PNORWD, "$NOTR,MD,102115,090715,1,0.02,0.01,2,45.0,90.0*00"),  # 10 fields
    ]
    for cls, sentence in test_cases:
        with pytest.raises(ValueError, match="Invalid prefix"):
            cls.from_nmea(sentence)


def test_pnors_coverage():
    # PNORS4 to_dict
    msg = PNORS4(12.0, 1500.0, 270.0, 0.0, 0.0, 10.0, 20.0)
    assert msg.to_dict()["sentence_type"] == "PNORS4"

    # parse_tagged_field coverage
    with pytest.raises(ValueError, match="must contain '='"):
        parse_tagged_field("INVALID")


def test_pnorc_coverage():
    # PNORC
    with pytest.raises(ValueError, match="Expected 19 fields for PNORC"):
        PNORC.from_nmea("$PNORC,1,2,3,4,5*00")  # 6 fields

    with pytest.raises(ValueError, match="Invalid prefix"):
        # 19 fields to pass length check, but invalid prefix
        PNORC.from_nmea("$NOTRC,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18*00")

    # PNORC1
    with pytest.raises(ValueError, match="Expected 17 fields for PNORC1"):
        PNORC1.from_nmea("$PNORC1,1,2,3,4,5,6,7,8*00")

    # PNORC2
    with pytest.raises(ValueError, match="Tagged field must contain '='"):
        PNORC2.from_nmea("$PNORC2,1,2,3*00")
    with pytest.raises(ValueError, match="Invalid prefix"):
        PNORC2.from_nmea("$NOTRC2,DATE=010101,TIME=120000,CN=1,CP=0*00")
    with pytest.raises(ValueError, match="Duplicate tag"):
        PNORC2.from_nmea("$PNORC2,DATE=010101,DATE=010101,TIME=120000,CN=1,CP=0*00")

    # PNORC3
    with pytest.raises(ValueError, match="Tagged field must contain '='"):
        PNORC3.from_nmea("$PNORC3,1,2,3,4,5*00")

    # PNORC4
    with pytest.raises(ValueError, match="Expected 6 fields for PNORC4"):
        PNORC4.from_nmea("$PNORC4,1,2,3,4*00")
