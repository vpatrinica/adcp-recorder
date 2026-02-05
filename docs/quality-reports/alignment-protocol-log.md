[🏠 Home](../README.md)

# Alignment Protocol Log

This log centralizes the reality-check notes that feed the parser/spec tracksheet. Update this file whenever the serial-processing architecture needs new follow-ups so the tracksheet can cite a single source of truth.

| Date | Topic | Status | Notes |
|------|-------|--------|-------|
| 2026-01-11 | Serial processing reality checks | Completed | Document now points to this log; see the bullet list below for the considered items. |

#### Recent Notes

- Reconciled the documented `reconnect(max_retries=3)` behavior with the producer's drop-oldest queue logic.
- Added integration-test plans for queue-full behavior and binary stream handling as part of the proof-of-life checks.
- Evaluated batching strategy for `SerialConsumer`/`adcp_recorder.db.operations` and logged the idea of a transaction helper.
- Logged the binary blob capture state and associated writer separation that may be needed when streaming binary data.
- Captured the spec verification reminder that maps `adcp_recorder/parsers` to `docs/specs` and notes the PNORI `cell_count` cap discrepancy (spec 1-1000 versus code 1-128).

Use [parser-spec-tracksheet](parser-spec-tracksheet.md) entry 4 to track the status of this log.