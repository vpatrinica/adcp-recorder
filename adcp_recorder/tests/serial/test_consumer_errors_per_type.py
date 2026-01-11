"""Tests for consumer parse error handling per message type.

Verifies that invalid messages for each documented type result in a PRESERVED error record
in the database, rather than being discarded or crashing the consumer.
"""

import pytest
import time
from queue import Queue
from adcp_recorder.db.db import DatabaseManager
from adcp_recorder.serial.consumer import SerialConsumer, MessageRouter
from adcp_recorder.db.operations import query_parse_errors

@pytest.fixture
def db_conn(tmp_path):
    """Create file-based DB for consumer tests to ensure thread visibility."""
    db_file = tmp_path / "consumer_test.db"
    db_manager = DatabaseManager(str(db_file))
    db_manager.initialize_schema()
    yield db_manager

@pytest.fixture
def consumer_stack(db_conn):
    """Setup queue, router, consumer with registered parsers."""
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

    queue = Queue()
    router = MessageRouter()
    
    # Register all parsers so strict consumer logic finds them
    router.register_parser("PNORI", PNORI)
    router.register_parser("PNORS", PNORS)
    router.register_parser("PNORC", PNORC)
    router.register_parser("PNORH3", PNORH3)
    router.register_parser("PNORW", PNORW)
    router.register_parser("PNORB", PNORB)
    router.register_parser("PNORE", PNORE)
    router.register_parser("PNORF", PNORF)
    router.register_parser("PNORWD", PNORWD)
    router.register_parser("PNORA", PNORA)

    consumer = SerialConsumer(queue, db_conn, router)
    consumer.start()
    yield queue, consumer, db_conn
    consumer.stop()


class TestConsumerParseErrors:
    
    def _verify_error_captured(self, queue, db_manager, prefix, bad_sentence):
        """Helper to inject bad message and verify error capture."""
        queue.put(bad_sentence.encode('utf-8'))
        
        # Poll for result
        for _ in range(20): # 20 * 0.1 = 2 seconds max
            time.sleep(0.1)
            conn = db_manager.get_connection()
            errors = query_parse_errors(conn, limit=10)
            found = [e for e in errors if e["attempted_prefix"] == prefix and e["raw_sentence"] == bad_sentence]
            if found:
                break
        
        assert len(found) == 1, f"Expected 1 error for {prefix}, found {len(found)}. Errors: {errors}"
        assert found[0]["error_type"] is not None

    def test_pnori_parse_error(self, consumer_stack):
        q, _, db = consumer_stack
        # PNORI: Invalid field count
        self._verify_error_captured(q, db, "PNORI", "$PNORI,1,2*XX")

    def test_pnors_parse_error(self, consumer_stack):
        q, _, db = consumer_stack
        # PNORS: Invalid field count
        self._verify_error_captured(q, db, "PNORS", "$PNORS,1,2*XX")

    def test_pnorc_parse_error(self, consumer_stack):
        q, _, db = consumer_stack
        # PNORC: Invalid field count
        self._verify_error_captured(q, db, "PNORC", "$PNORC,1,2*XX")

    def test_pnorh_parse_error(self, consumer_stack):
        q, _, db = consumer_stack
        # PNORH3: Invalid field count
        self._verify_error_captured(q, db, "PNORH3", "$PNORH3,1,2*XX")

    def test_pnorw_parse_error(self, consumer_stack):
        q, _, db = consumer_stack
        # PNORW: Invalid field count
        self._verify_error_captured(q, db, "PNORW", "$PNORW,1,2*XX")

    def test_pnorb_parse_error(self, consumer_stack):
        q, _, db = consumer_stack
        # PNORB: Invalid field count
        self._verify_error_captured(q, db, "PNORB", "$PNORB,1,2*XX")

    def test_pnore_parse_error(self, consumer_stack):
        q, _, db = consumer_stack
        # PNORE: Invalid field count
        self._verify_error_captured(q, db, "PNORE", "$PNORE,1,2*XX")

    def test_pnorf_parse_error(self, consumer_stack):
        q, _, db = consumer_stack
        # PNORF: Invalid field count
        self._verify_error_captured(q, db, "PNORF", "$PNORF,1,2*XX")

    def test_pnorwd_parse_error(self, consumer_stack):
        q, _, db = consumer_stack
        # PNORWD: Invalid field count
        self._verify_error_captured(q, db, "PNORWD", "$PNORWD,1,2*XX")

    def test_pnora_parse_error(self, consumer_stack):
        q, _, db = consumer_stack
        # PNORA: Invalid field count
        self._verify_error_captured(q, db, "PNORA", "$PNORA,1,2*XX")

    def test_checksum_failure_generic(self, consumer_stack):
        q, _, db = consumer_stack
        # Valid format but bad checksum, routed to PNORI logic first? 
        # No, Consumer validates checksum BEFORE routing if it can split?
        # Actually Consumer calls `parser.from_nmea`.
        # core/nmea.py `from_nmea` does checksum validation.
        # So it should be caught as ValueError("Checksum mismatch...")
        
        fake_sentence = "$PNORI,4,S,4,20,0,1,0*FF" # FF is likely wrong
        self._verify_error_captured(q, db, "PNORI", fake_sentence)
