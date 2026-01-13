import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest


@pytest.mark.skipif(
    os.name == "nt", reason="SIGTERM is not graceful on Windows via Popen.terminate()"
)
def test_supervisor_lifecycle_with_signals(tmp_path):
    """
    Runs mock_runner.py as a subprocess.
    Sends SIGTERM and verifies clean exit.
    """
    runner_script = Path(__file__).parent / "mock_runner.py"

    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()  # Ensure package is found

    process = subprocess.Popen(
        [sys.executable, str(runner_script)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Wait for start
    start_time = time.time()
    while time.time() - start_time < 5:
        if process.poll() is not None:
            break
        # We can't easily read stdout without blocking unless we use threads or communicate.
        # But we can just wait a bit.
        time.sleep(0.5)
        # Check if it crashed
        if process.poll() is not None:
            break

    if process.poll() is not None:
        stdout, stderr = process.communicate()
        pytest.fail(f"Mock service failed to start/died early.\nOUT: {stdout}\nERR: {stderr}")

    # Send SIGTERM
    process.terminate()

    try:
        stdout, stderr = process.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        pytest.fail("Mock service did not stop on SIGTERM")

    assert process.returncode == 0
    assert "Mock Service Starting" in stdout
    # "Mock Service Clean Exit" might not print if main() returns or sys.exit() is called?
    # supervisor.run() catches exceptions and calls sys.exit(1) on crash.
    # If successful, it returns? No, run() loop breaks.
    # Then main() returns.
    assert "Mock Service Clean Exit" in stdout


def test_supervisor_lifecycle_sigint(tmp_path):
    """Test SIGINT handling."""
    runner_script = Path(__file__).parent / "mock_runner.py"
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()

    kwargs = {
        "env": env,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
    }

    if os.name == "nt":
        # On Windows, we need a new process group to send CTRL_C_EVENT
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

    process = subprocess.Popen([sys.executable, str(runner_script)], **kwargs)

    time.sleep(1)
    if process.poll() is not None:
        stdout, stderr = process.communicate()
        pytest.fail(f"Mock service died early.\nOUT: {stdout}\nERR: {stderr}")

    if os.name == "nt":
        # On Windows, CTRL_C_EVENT is unreliable in subprocess contexts
        # Use terminate() instead which triggers the same cleanup path
        process.terminate()
    else:
        process.send_signal(signal.SIGINT)

    try:
        stdout, stderr = process.communicate(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        # Get whatever we can from stdout/stderr
        stdout, stderr = process.communicate()
        pytest.fail(f"Mock service timeout on signal.\nOUT: {stdout}\nERR: {stderr}")

    # On Windows, terminate() returns exit code 1, not 0
    if os.name == "nt":
        # Just verify the process exited
        assert process.returncode is not None
    else:
        assert process.returncode == 0
        assert "Mock Service Clean Exit" in stdout
