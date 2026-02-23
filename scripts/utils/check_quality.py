import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """Run a shell command and exit if it fails."""
    print(f"\n[INFO] {description}...")
    try:
        # Use shell=True for complex commands (like pip install with quotes)
        # Check=True raises CalledProcessError on non-zero exit code
        subprocess.run(command, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] {description} failed with exit code {e.returncode}.")
        sys.exit(e.returncode)


def main():
    # Set working directory to project root
    project_root = Path(__file__).resolve().parent.parent.parent

    # 1. Install Dependencies
    # run_command(
    #     f"{sys.executable} -m pip install --upgrade pip",
    #     "Upgrading pip"
    # )
    run_command("uv pip install --upgrade pip", "Upgrading pip via uv")
    # run_command(
    #     f"{sys.executable} -m pip install ruff mypy types-pyserial pytest-cov safety bandit pdoc",
    #     "Installing quality tools"
    # )
    run_command(
        "uv pip install ruff mypy types-pyserial pytest-cov safety bandit pdoc",
        "Installing quality tools via uv",
    )
    # Use quotes for extras installation
    # run_command(
    #     f"{sys.executable} -m pip install -e \".[dev,analysis]\"",
    #     "Installing project in editable mode with dev dependencies"
    # )
    run_command('uv pip install -e ".[dev,analysis]"', "Installing project in editable mode via uv")
    # Use quotes for extras installation
    run_command(
        f'{sys.executable} -m pip install -e ".[dev,analysis]"',
        "Installing project in editable mode with dev dependencies",
    )

    # 2. Code Quality Checks
    print("\n" + "=" * 50)
    print("Running Quality Checks")
    print("=" * 50)

    # Ruff Format
    run_command("uv run ruff format --check adcp_recorder/", "Checking Code Formatting (Ruff)")

    # Ruff Lint
    run_command("uv run ruff check adcp_recorder/", "Linting Code (Ruff)")

    # Mypy Static Analysis
    run_command("uv run mypy adcp_recorder/", "Static Type Checking (Mypy)")

    # Documentation Check
    script_path = project_root / "scripts" / "check_docs.py"
    run_command(f"{sys.executable} {script_path}", "Checking Documentation Coverage")

    # 3. Tests & Coverage
    print("\n" + "=" * 50)
    print("Running Tests")
    print("=" * 50)

    # Using python -m pytest to ensure it runs in the current environment
    # Note: Using uv run pytest is also fine if uv is available
    run_command(
        "uv run pytest --cov=adcp_recorder --cov-fail-under=100 --cov-report=term-missing adcp_recorder/tests/",
        "Running Tests with Coverage",
    )

    print("\n" + "=" * 50)
    print("ALL CHECKS PASSED SUCCESSFULLY")
    print("=" * 50)


if __name__ == "__main__":
    main()
