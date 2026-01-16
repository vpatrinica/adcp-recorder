"""Lightweight spec-to-parser alignment check.

Usage:
    python scripts/check_parser_spec_alignment.py

Exits with non-zero status if any spec family lacks a parser.
"""

import re
import sys
from pathlib import Path

from adcp_recorder.parsers import __all__ as parser_exports

SPEC_DIR = Path(__file__).resolve().parents[1] / "docs" / "specs"


def normalize_parser_name(name: str) -> str:
    return re.sub(r"\d+$", "", name)


def main() -> int:
    spec_families = {p.name.upper() for p in SPEC_DIR.iterdir() if p.is_dir()}
    parser_families = {normalize_parser_name(name) for name in parser_exports}

    missing = [spec for spec in sorted(spec_families) if spec not in parser_families]

    if missing:
        print("Spec families without parsers:")
        for spec in missing:
            print(f"  - {spec}")
        return 1

    print(
        "All spec families have at least one parser export.\n"
        + "Spec check passed for families: "
        + ", ".join(sorted(spec_families))
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
