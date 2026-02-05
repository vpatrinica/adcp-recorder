"""Tests for the ADCP Recorder CLI migration command."""

from unittest.mock import patch

import duckdb
import pytest
from click.testing import CliRunner

from adcp_recorder.cli.main import cli


@pytest.fixture
def old_db(tmp_path):
    """Create a mock old schema database."""
    db_path = tmp_path / "old.duckdb"
    conn = duckdb.connect(str(db_path))
    # Create an old table that needs migration
    conn.execute(
        """
        CREATE TABLE echo_data (
            received_at TIMESTAMP,
            measurement_date VARCHAR,
            measurement_time VARCHAR,
            original_sentence VARCHAR,
            spectrum_basis TINYINT,
            start_frequency DOUBLE,
            step_frequency DOUBLE,
            num_frequencies INTEGER,
            energy_densities DOUBLE[],
            checksum VARCHAR
        )
        """
    )
    conn.execute(
        """
        INSERT INTO echo_data VALUES (
            now(), '240101', '120000', '$PNORE,240101,120000,...*AB',
            0, 1.0, 0.1, 10, [1.0, 2.0], 'AB'
        )
        """
    )
    conn.close()
    return db_path


class TestCliMigration:
    """Tests for the migrate CLI command."""

    def test_migrate_usage_error(self):
        """Test migrate command with missing arguments."""
        runner = CliRunner()
        result = runner.invoke(cli, ["migrate"])
        assert result.exit_code != 0
        assert "Missing argument 'SOURCE'" in result.output

    def test_migrate_success(self, old_db, tmp_path):
        """Test successful migration via CLI."""
        target_db = tmp_path / "new.duckdb"
        runner = CliRunner()
        result = runner.invoke(
            cli, ["migrate", str(old_db), "--target", str(target_db), "--verify"]
        )

        assert result.exit_code == 0
        assert "Migration Statistics" in result.output
        assert "Verification" in result.output
        assert target_db.exists()

    def test_migrate_in_place(self, old_db):
        """Test in-place migration via CLI."""
        runner = CliRunner()
        result = runner.invoke(cli, ["migrate", str(old_db), "--in-place"])
        assert result.exit_code == 0
        assert "Migration Statistics" in result.output

    def test_migrate_in_place_verify(self, old_db):
        """Test in-place migration with verification via CLI."""
        runner = CliRunner()
        result = runner.invoke(cli, ["migrate", str(old_db), "--in-place", "--verify"])
        assert result.exit_code == 0
        assert "Verification" in result.output

        # Verify echo_data is gone (migrated)
        conn = duckdb.connect(str(old_db))
        res = conn.execute(
            "SELECT count(*) FROM information_schema.tables WHERE table_name = 'echo_data'"
        ).fetchone()
        assert res is not None
        assert res[0] == 0
        conn.close()

    def test_migrate_exception(self, old_db):
        """Test CLI behavior when migration fails."""
        runner = CliRunner()

        with patch(
            "adcp_recorder.cli.main.migrate_database", side_effect=RuntimeError("Migration crashed")
        ):
            result = runner.invoke(cli, ["migrate", str(old_db)])
            assert result.exit_code == 1
            assert "Migration failed: Migration crashed" in result.output

    def test_migrate_default_target(self, old_db):
        """Test migration with default target path generation."""
        runner = CliRunner()
        result = runner.invoke(cli, ["migrate", str(old_db), "--verify"])

        assert result.exit_code == 0
        expected_target = old_db.parent / "old_migrated.duckdb"
        assert expected_target.exists()
