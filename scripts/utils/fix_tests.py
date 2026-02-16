"""Fix NMEA checksums in test files.

Finds NMEA sentences in test files and recomputes their checksums.
Handles single-line, multi-line concatenated strings, and *XX placeholders.
Skips f-strings with expressions to avoid corruption.
"""

import re
from adcp_recorder.core.nmea import compute_checksum

FILES = [
    r"adcp_recorder\tests\parsers\test_pnora.py",
    r"adcp_recorder\tests\parsers\test_pnorb.py",
    r"adcp_recorder\tests\parsers\test_pnorb_extended.py",
    r"adcp_recorder\tests\parsers\test_pnorc.py",
    r"adcp_recorder\tests\parsers\test_pnore.py",
    r"adcp_recorder\tests\parsers\test_pnorf.py",
    r"adcp_recorder\tests\parsers\test_pnorh.py",
    r"adcp_recorder\tests\parsers\test_pnori.py",
    r"adcp_recorder\tests\parsers\test_pnors.py",
    r"adcp_recorder\tests\parsers\test_pnorw.py",
    r"adcp_recorder\tests\parsers\test_pnorwd.py",
    r"adcp_recorder\tests\parsers\test_parsers_coverage.py",
    r"adcp_recorder\tests\parsers\test_global_nan.py",
    r"adcp_recorder\tests\parsers\test_utils.py",
    r"adcp_recorder\tests\db\test_full_persistence.py",
    r"adcp_recorder\tests\db\test_operations.py",
    r"adcp_recorder\tests\serial\test_consumer.py",
    r"adcp_recorder\tests\serial\test_consumer_resilience.py",
    r"adcp_recorder\tests\test_compliance_100.py",
]

# Match single-line sentences with checksum (hex or XX placeholder)
SINGLE_LINE = re.compile(r'"(\$PNOR[A-Z0-9]*(?:,[^"*{]*?))\*([0-9A-Fa-fXx]{2,})"')

# Match multi-line concatenated sentences where checksum is on second line
MULTI_LINE = re.compile(
    r'"(\$PNOR[A-Z0-9]*[^"*{]*?)"\s*\r?\n(\s*)"([^"*{]*?)\*([0-9A-Fa-fXx]{2,})"', re.MULTILINE
)


def fix_single_line(line: str) -> str:
    """Fix checksums in single-line NMEA sentences."""
    # Skip f-strings with expressions
    stripped = line.strip()
    if "{" in stripped and "}" in stripped and stripped.startswith(('f"', "f'")):
        return line

    def replace_match(m):
        payload = m.group(1)
        if "{" in payload or "}" in payload:
            return m.group(0)
        cs = compute_checksum(payload)
        return f'"{payload}*{cs}"'

    return SINGLE_LINE.sub(replace_match, line)


def fix_multiline_sentences(content: str) -> str:
    """Fix checksums in multi-line concatenated NMEA sentences."""

    def replace_multiline(m):
        part1 = m.group(1)
        indent = m.group(2)
        part2 = m.group(3)
        if "{" in part1 or "{" in part2:
            return m.group(0)
        full_payload = part1 + part2
        cs = compute_checksum("$" + full_payload.lstrip("$"))
        return f'"{part1}"\n{indent}"{part2}*{cs}"'

    return MULTI_LINE.sub(replace_multiline, content)


def fix_file(path: str) -> None:
    with open(path, "r") as f:
        content = f.read()

    # First pass: fix multi-line concatenated sentences
    content = fix_multiline_sentences(content)

    # Second pass: fix single-line sentences
    lines = content.split("\n")
    fixed_lines = [fix_single_line(line) for line in lines]
    content = "\n".join(fixed_lines)

    with open(path, "w") as f:
        f.write(content)
    print(f"Fixed {path}")


if __name__ == "__main__":
    for f in FILES:
        try:
            fix_file(f)
        except Exception as e:
            print(f"ERROR in {f}: {e}")
