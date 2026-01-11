[🏠 Home](../README.md)

# Parser / Spec Tracksheet

| ID | Area | Issue | Severity | Reference | Action | Status |
|----|------|-------|----------|-----------|--------|--------|
| 1 | PNORI / PNORI1 / PNORI2 | `cell_count` validation now correctly allows 1-1000 cells (`adcp_recorder/parsers/pnori.py::_validate_cell_count`), matching the spec (`docs/specs/pnori/pnori.md`). | High | [parser](adcp_recorder/parsers/pnori.py#L27-L40), [spec](docs/specs/pnori/pnori.md#field-definitions) | Added regression tests and adjusted validation to accept up to 1000 cells; keep monitoring new spec versions. | Completed |
| 2 | Specification review process | Need a lightweight proof-of-life so new spec updates are cross-checked against the parser registry. | Medium | [report](quality-reports/parser-spec-discrepancies.md) | Script/CI job that diffs `docs/specs` subfolders vs `adcp_recorder/parsers` exports and fails if a spec lacks a parser. | Completed |
| 3 | Full spec scan | Captured output from `scripts/check_parser_spec_alignment.py` verifying each spec family is covered; no additional mismatches found. | Low | [script](scripts/check_parser_spec_alignment.py) | Re-run the script as part of CI to keep this record updated. | Completed |
| 4 | Alignment protocol log | Reality-check notes for serial processing now live in a dedicated log so the architecture docs can simply point readers there. | Low | [log](quality-reports/alignment-protocol-log.md) | Maintain this log, cite it from the tracksheet when a reality check is added, and keep the log entry aligned with future follow-ups. | Completed |