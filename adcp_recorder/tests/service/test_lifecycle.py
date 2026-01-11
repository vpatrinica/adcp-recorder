import os
import signal
import subprocess
import sys
import time
import pytest
from pathlib import Path

def test_supervisor_lifecycle_with_signals(tmp_path):
    """
    Runs mock_runner.py as a subprocess.
    Sends SIGTERM and verifies clean exit.
    """
    runner_script = Path(__file__).parent / "mock_runner.py"
    
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd() # Ensure package is found
    
    process = subprocess.Popen(
        [sys.executable, str(runner_script)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for start
    started = False
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

    process = subprocess.Popen(
        [sys.executable, str(runner_script)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    time.sleep(1)
    if process.poll() is not None:
         stdout, stderr = process.communicate()
         pytest.fail(f"Mock service died early.\nOUT: {stdout}\nERR: {stderr}")

    process.send_signal(signal.SIGINT)
    
    try:
        stdout, stderr = process.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        pytest.fail("Mock service timeout on SIGINT")
        
    assert process.returncode == 0
    assert "Mock Service Clean Exit" in stdout
