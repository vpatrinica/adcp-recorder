from unittest.mock import patch

import pytest
from click.testing import CliRunner

from adcp_recorder.cli.main import cli


@pytest.fixture
def runner():
    return CliRunner()


def test_generate_service_linux(runner, tmp_path):
    with patch(
        "adcp_recorder.templates.__file__", "/fake/path/adcp_recorder/templates/__init__.py"
    ):
        # We need to mock shutil.copy or ensure the source path exists in test env.
        # Since we rely on package data, let's assume the real files confirm existence
        # but for unit test we might want to mock if we are not installing as package.
        # However, in this dev env, the files exist on disk.
        pass

    # Let's run it against the real file system since we created the files
    result = runner.invoke(cli, ["generate-service", "--platform", "linux", "--out", str(tmp_path)])

    assert result.exit_code == 0
    generated_file = tmp_path / "adcp-recorder.service"
    assert generated_file.exists()
    content = generated_file.read_text()
    assert "[Unit]" in content
    assert "ExecStart" in content


def test_generate_service_windows(runner, tmp_path):
    result = runner.invoke(
        cli, ["generate-service", "--platform", "windows", "--out", str(tmp_path)]
    )

    assert result.exit_code == 0
    generated_file = tmp_path / "install_service.bat"
    assert generated_file.exists()
    content = generated_file.read_text()
    assert "servy-cli install" in content
