import runpy
from unittest.mock import patch


def reproduce():
    # Simulate pytest args in sys.argv
    with patch("sys.argv", ["pytest", "some_test_arg"]):
        try:
            runpy.run_module("adcp_recorder.cli.main", run_name="__main__")
        except SystemExit as e:
            print(f"Caught SystemExit: {e.code}")
            if e.code != 0:
                print("Failure reproduced (non-zero exit)")
            else:
                print("Unexpected zero exit")
        except Exception as e:
            print(f"Caught Exception: {e}")


def verify_fix():
    print("\nVerifying fix...")
    # Fix: Patch sys.argv to something valid for the CLI, e.g. --help
    with patch("sys.argv", ["adcp-recorder", "--help"]):
        try:
            runpy.run_module("adcp_recorder.cli.main", run_name="__main__")
        except SystemExit as e:
            if e.code == 0:
                print("Fix verified (exit code 0)")
            else:
                print(f"Fix failed (exit code {e.code})")


if __name__ == "__main__":
    reproduce()
    verify_fix()
