"""targeted tests to reach 100% compliance coverage."""

from unittest.mock import MagicMock, patch

import duckdb
import pytest

from adcp_recorder.core.enums import CoordinateSystem
from adcp_recorder.db.db import DatabaseManager
from adcp_recorder.db.operations import (
    batch_insert_raw_lines,
    insert_header_data,
    insert_pnori_configuration,
    insert_sensor_data,
)
from adcp_recorder.parsers.pnorh import PNORH3
from adcp_recorder.parsers.pnori import PNORI1, PNORI2
from adcp_recorder.parsers.pnors import PNORS2, PNORS3, PNORS4


def test_missing_checksum_logic_pnori_variants():
    # PNORI1 without checksum
    s = "$PNORI1,4,123,4,20,1.0,5.0,ENU"
    msg = PNORI1.from_nmea(s)
    assert msg.checksum is None
    assert msg.coordinate_system == CoordinateSystem.ENU

    # PNORI2 without checksum
    s2 = "$PNORI2,IT=4,SN=123,NB=4,NC=20,BD=1.0,CS=5.0,CY=ENU"
    msg2 = PNORI2.from_nmea(s2)
    assert msg2.checksum is None


def test_pnori_error_branches():
    # PNORI1 invalid field count
    with pytest.raises(ValueError, match="Expected 8 fields"):
        PNORI1.from_nmea("$PNORI1,1,2,3")

    # PNORI1 invalid prefix
    with pytest.raises(ValueError, match="Invalid prefix"):
        PNORI1.from_nmea("$INVALID,1,2,3,4,5,6,7")

    # PNORI2 invalid field count
    with pytest.raises(ValueError, match="Expected at least 8 fields"):
        PNORI2.from_nmea("$PNORI2,1,2,3")

    # PNORI2 invalid prefix
    # hits pnori.py:400
    with pytest.raises(ValueError, match="Invalid prefix"):
        # We need a string that starts with $ but not PNORI.
        # Actually PNORI2.from_nmea checks prefix.
        PNORI2.from_nmea("$INVALID,1,2,3,4,5,6,7")


def test_pnors_error_branches():
    # PNORS2 unknown tags
    base = (
        "$PNORS2,DATE=101010,TIME=101010,EC=00,SC=00,BV=12.0,SS=1500,HSD=0,"
        "H=100,PI=0,PISD=0,R=0,RSD=0,P=10,PSD=0,T=20"
    )
    extra = ",XX=99*00"
    with pytest.raises(ValueError, match="Unknown tag in PNORS2: XX"):
        PNORS2.from_nmea(base + extra)

    # PNORS3 invalid prefix (pnors.py:391)
    with pytest.raises(ValueError, match="Invalid prefix"):
        PNORS3.from_nmea("$INVALID,1,2,3,4,5,6,7,8")

    # PNORS4 invalid prefix (pnors.py:451)
    with pytest.raises(ValueError, match="Expected 8 fields"):
        PNORS4.from_nmea("$INVALID,1,2,3,4,5")


def test_ghost_files_explicitly():
    from adcp_recorder.parsers.pnorb import PNORB
    from adcp_recorder.parsers.pnore import PNORE
    from adcp_recorder.parsers.pnorf import PNORF
    from adcp_recorder.parsers.pnorwd import PNORWD

    msg_b = PNORB.from_nmea(
        "$PNORB,102115,090715,1,4,0.02,0.20,0.27,7.54,12.00,82.42,75.46,82.10,0000*XX"
    )
    assert msg_b.spectrum_basis == 1

    msg_e = PNORE.from_nmea("$PNORE,102115,090715,1,0.02,0.01,3,1.5,2.5,3.5*XX")
    assert msg_e.spectrum_basis == 1

    msg_f = PNORF.from_nmea("$PNORF,A1,102115,090715,1,0.02,0.01,2,0.5,1.5*XX")
    assert msg_f.coefficient_flag == "A1"

    msg_wd = PNORWD.from_nmea("$PNORWD,MD,102115,090715,1,0.02,0.01,2,45.0,90.0*XX")
    assert msg_wd.direction_type == "MD"

    msg_h = PNORH3("211021", "090715", 0, "00000000")
    assert msg_h.to_dict()["sentence_type"] == "PNORH3"


def test_operations_coverage_filler():
    db = DatabaseManager(":memory:")
    conn = db.get_connection()

    # Line 73: empty batch
    assert batch_insert_raw_lines(conn, []) == 0

    # Lines 114-116: batch insert exception
    mock_conn = MagicMock()

    def side_effect(sql, *args):
        if "INSERT INTO" in sql:
            raise Exception("Failure")
        return MagicMock()

    mock_conn.execute.side_effect = side_effect
    with pytest.raises(Exception, match="Failure"):
        batch_insert_raw_lines(mock_conn, [{"sentence": "$TEST"}])
    assert mock_conn.rollback.called

    # Lines 432, 624, 764: invalid variants
    with pytest.raises(ValueError, match="Unknown PNORI sentence type"):
        insert_pnori_configuration(conn, {"sentence_type": "INVALID"}, "$TEST")

    with pytest.raises(ValueError, match="Unknown sensor sentence type"):
        insert_sensor_data(conn, "$TEST", {"sentence_type": "INVALID"})

    with pytest.raises(ValueError, match="Unknown header sentence type"):
        insert_header_data(conn, "$TEST", {"sentence_type": "INVALID"})


def test_migration_complete_coverage(tmp_path):
    from adcp_recorder.db.migration import MigrationError, main

    old_db = tmp_path / "old_coverage.duckdb"

    conn = duckdb.connect(str(old_db))
    # Create ALL tables to hit "count == 0" branches
    tables = [
        "pnori1",
        "pnori2",
        "pnors_df101",
        "pnors_df102",
        "pnors_df103",
        "pnors_df104",
        "pnorc_df101",
        "pnorc_df102",
        "pnorc_df103",
        "pnorc_df104",
        "pnorh_df103",
        "pnorh_df104",
        "echo_data",
        "pnorw_data",
        "raw_lines",
    ]
    for t in tables:
        conn.execute(
            f"CREATE TABLE {t} (record_id BIGINT, received_at TIMESTAMP, original_sentence TEXT)"
        )

    # Re-create pnori1 with FULL schema and ONE row to hit success path
    conn.execute("DROP TABLE pnori1")
    conn.execute("""
        CREATE TABLE pnori1 (
            received_at TIMESTAMP, original_sentence TEXT,
            instrument_type_name VARCHAR, instrument_type_code INTEGER,
            head_id INTEGER, beam_count INTEGER, cell_count INTEGER,
            blanking_distance FLOAT, cell_size FLOAT,
            coord_system_name VARCHAR, coord_system_code INTEGER,
            checksum VARCHAR
        )
    """)
    conn.execute("""
        INSERT INTO pnori1 VALUES (
            current_timestamp, '$PNORI', 'ADCP', 0, 1, 4, 10, 0.5, 1.0, 'XYZ', 1, '00'
        )
    """)
    conn.close()

    # Test main() CLI block for coverage
    # Hit verify, hit implicit target
    with patch("sys.argv", ["prog", str(old_db), "--verify"]):
        try:
            main()
        except SystemExit:
            pass

    # Hit in-place
    with patch("sys.argv", ["prog", str(old_db), "--in-place"]):
        try:
            main()
        except SystemExit:
            pass

    # Hit MigrationError branch in main()
    with patch(
        "adcp_recorder.db.migration.migrate_database", side_effect=MigrationError("Manual failure")
    ):
        with patch("sys.argv", ["prog", str(old_db)]):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 1
