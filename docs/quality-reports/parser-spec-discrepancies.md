[🏠 Home](../README.md)

# Parser / Spec Alignment Report

**Date:** 2026-01-11  
**Scope:** All documented ADCP message families under `docs/specs/*` versus the runtime parser implementations in `adcp_recorder/parsers`.

## Methodology

1. Mapped each spec sub-folder (PNORI, PNORS, PNORC, PNORH, PNORA, PNORB, PNORE, PNORF, PNORW, PNORWD) to the classes exported by `adcp_recorder/parsers/__init__.py`.
2. Compared each family’s described field counts, ranges, and validation rules to the code paths in the parser module (e.g., `adcp_recorder/parsers/pnori.py`).
3. Highlighted the notable divergences and documented them for tracking.

## Findings

1. **Coverage ✔️** – Every documented family has a matching parser class (PNORI/PNORI1/PNORI2, PNORS1-4, PNORC1-4, PNORH3/PNORH4, PNORA, PNORB, PNORE, PNORF, PNORW, PNORWD). See `adcp_recorder/parsers/__init__.py` for the registry used by `SerialConsumer`.
2. **Cell-count range gap ⚠️** – The PNORI family spec explicitly states `cell_count` spans 1-1000 ([docs/specs/pnori/pnori.md#field-definitions](docs/specs/pnori/pnori.md#field-definitions)). The shared helper `_validate_cell_count` in `adcp_recorder/parsers/pnori.py` caps at 128, so any instrument reporting >128 cells will be rejected even though the spec allows it.
3. **Cross-validation alignment ✅** – The cross-field rules described in the spec (e.g., Signature instruments require 4 beams, coordinate system names map to numeric codes) are enforced via `InstrumentType.valid_beam_counts` and `CoordinateSystem` helpers, so no action is needed there.

## Recommendations & Next Steps

- Adjust `_validate_cell_count` to match the documented 1-1000 range and protect it with regression tests (done on 2026-01-11).  
- Add automation to re-check spec coverage whenever new spec folders land (see `scripts/check_parser_spec_alignment.py`, run before this report).  
- Iteratively repeat this reconciliation for the other families (PNORS, PNORC, etc.) once the first gap is closed; track the additional findings in the companion tracksheet.

## Validation

- Verified with `python scripts/check_parser_spec_alignment.py` that each spec directory has at least one exported parser in `adcp_recorder/parsers/__init__.py`. This script is now part of the proof-of-life per the tracksheet.