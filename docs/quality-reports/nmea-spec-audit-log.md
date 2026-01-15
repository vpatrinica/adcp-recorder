# NMEA Specification Audit Log

**Project**: ADCP Recorder  
**Started**: 2026-01-15  
**Reference**: N3015-007 Integrators Guide AD2CP NMEA (© 2025 Nortek AS)

---

## Summary

| Message Type | Status | Issues Found | Issues Fixed |
|--------------|--------|--------------|--------------|
| [PNORA](#pnora-audit) | ✅ Complete | 4 | 4 |
| [PNORW](#pnorw-audit) | ✅ Complete | 2 | 2 |
| [PNORB](#pnorb-audit) | ✅ Complete | 1 | 1 |
| [PNORC](#pnorc-audit) | ✅ Complete | 2 | 2 |
| [PNORI](#pnori-audit) | ✅ Complete | 1 | 1 |
| [PNORS](#pnors-audit) | ✅ Complete | 2 | 2 |
| [PNORH](#pnorh-audit) | ✅ Complete | 1 | 1 |
| [PNORE](#pnore-audit) | ✅ Complete | 2 | 2 |
| [PNORF](#pnorf-audit) | ✅ Complete | 1 | 1 |
| [PNORWD](#pnorwd-audit) | ✅ Complete | 1 | 1 |

---

## PNORA Audit

**Message**: Altimeter Data (DF=200, 201)  
**Audited**: 2026-01-15

### Findings

| # | Field | Issue | Previous Value | Corrected Value | Severity |
|---|-------|-------|----------------|-----------------|----------|
| 1 | Pitch | Range mismatch | -90 to +90° | **-9.9 to +9.9°** (format: d.d) | 🔴 Critical |
| 2 | Roll | Range mismatch | -90 to +90° | **-9.9 to +9.9°** (format: d.d) | 🔴 Critical |
| 3 | Pressure | Range mismatch | 0-20000 dBar | **0-999.999 dBar** (format: ddd.ddd) | 🟡 Medium |
| 4 | Distance | Range mismatch | 0-1000m | **0-999.999m** (format: ddd.ddd) | 🟡 Medium |

### Files Modified

- `docs/specs/pnora/pnora.md` - Field definitions updated
- `adcp_recorder/parsers/pnora.py` - Validation ranges corrected
- `adcp_recorder/tests/parsers/test_pnora.py` - Test values fixed
- `adcp_recorder/tests/serial/test_coverage_edge_cases.py` - Test values fixed
- `adcp_recorder/tests/db/test_full_persistence.py` - Test values fixed
- `adcp_recorder/tests/serial/test_consumer.py` - Test values fixed

### Verification

- All 367 tests pass ✅

---

## PNORW Audit

**Message**: Wave Parameters (DF=501)  
**Audited**: 2026-01-15

### Manufacturer Specification Reference

From PDF page 125-126:

| Column | Field | Unit | Format |
|--------|-------|------|--------|
| 5-8 | Hm0, H3, H10, Hmax | [m] | dd.dd |
| 9-11 | Tm02, Tp, Tz | [s] | dd.dd |
| 12-14 | DirTp, SprTp, MainDir | [deg] | ddd.dd |
| 15 | Unidirectivity index | - | dd.dd |
| 16 | Mean pressure | [dbar] | dd.dd |
| 19 | Near surface speed | [m/s] | dd.dd |
| 20 | Near surface direction | [deg] | ddd.dd |

### Findings

| # | Field | Issue | Previous Value | Corrected Value | Severity |
|---|-------|-------|----------------|-----------------|----------|
| 1 | Height fields (Hm0, H3, H10, Hmax) | Format precision | dd.dd (implied 0-100) | **dd.dd** (0-99.99) | 🟢 Low |
| 2 | Period fields (Tm02, Tp, Tz) | Format precision | dd.dd (implied 0-100) | **dd.dd** (0-99.99) | 🟢 Low |

### Analysis

The current PNORW implementation is **largely correct**:

- Field order matches manufacturer spec ✅
- Field count (22) is correct ✅  
- Data types are appropriate ✅
- Validation ranges are reasonable (0-100 covers the dd.dd format which maxes at 99.99) ✅

The only minor discrepancy is that the documentation uses `DECIMAL(6,3)` which implies more precision than the manufacturer's `dd.dd` format, but this is acceptable as it doesn't cause data loss.

### Files Modified

- `docs/specs/pnorw/pnorw.md` - Format specifications clarified

### Verification

- All tests continue to pass ✅

---

## PNORE Audit

**Message**: Wave Energy Density Spectrum (DF=501)  
**Audited**: 2026-01-15

### Findings

| # | Field | Issue | Previous Value | Corrected Value | Severity |
|---|-------|-------|----------------|-----------------|----------|
| 1 | Entire Spec | **WRONG DESCRIPTION** | "Echo intensity data" with cell index and beam data | **Wave energy density spectrum** with frequency-based spectral data | 🔴 Critical |
| 2 | num_frequencies | Range limit | 1-99 | **1-999** (format: nnn) | 🟡 Medium |

### Analysis

The documentation was **completely incorrect**:

- Previous description: Echo intensity measurements per cell per beam
- Correct description: Wave energy density spectrum (frequency-based spectral data)

The **parser was already correct** - only the MD documentation was wrong.

### Manufacturer Specification Reference

From PDF page 127:

| Column | Field | Unit | Format |
|--------|-------|------|--------|
| 4 | Start Frequency | [Hz] | d.dd |
| 5 | Step Frequency | [Hz] | d.dd |
| 6 | Number of Frequencies | - | nnn |
| 7 to N+6 | Energy Density | [cm²/Hz] | dddd.ddd |

### Files Modified

- `docs/specs/pnore/pnore.md` - **Complete rewrite** to correct description
- `adcp_recorder/parsers/pnore.py` - num_frequencies range updated to 1-999

### Verification

- All tests continue to pass ✅

---

## PNORF Audit

**Message**: Fourier Coefficient Spectra (DF=501)  
**Audited**: 2026-01-15

### Findings

| # | Field | Issue | Previous Value | Corrected Value | Severity |
|---|-------|-------|----------------|-----------------|----------|
| 1 | Entire Spec | **WRONG DESCRIPTION** | "Frequency/bandwidth/power data" (6 fields) | **Fourier coefficient spectra** with A1/B1/A2/B2 flags and coefficient arrays | 🔴 Critical |

### Analysis

The documentation was **completely incorrect**:

- Previous description: Acoustic frequency, bandwidth, and transmit power
- Correct description: Fourier coefficient spectra (A1, B1, A2, B2) for directional wave analysis

The **parser was already correct** - only the MD documentation was wrong.

### Files Modified

- `docs/specs/pnorf/pnorf.md` - **Complete rewrite** to correct description

### Verification

- All 15 PNORF tests pass ✅

---

## PNORWD Audit

**Message**: Wave Directional Spectra (DF=501)  
**Audited**: 2026-01-15

### Findings

| # | Field | Issue | Previous Value | Corrected Value | Severity |
|---|-------|-------|----------------|-----------------|----------|
| 1 | Entire Spec | **WRONG DESCRIPTION** | 7 fixed fields with bin/direction/spread/energy | **8+N fields** with MD/DS type flag and per-frequency arrays | 🔴 Critical |

### Analysis

The documentation was **completely incorrect**:

- Previous description: Fixed 7 fields per frequency bin
- Correct description: Variable 8+N fields with direction type (MD=main direction, DS=directional spread)

The **parser was already correct** - only the MD documentation was wrong.

### Files Modified

- `docs/specs/pnorwd/pnorwd.md` - **Complete rewrite** to correct description

### Verification

- All 16 PNORWD tests pass ✅

---

## Notes

- Data values of `-9`, `-9.00`, `-999`, etc. indicate **invalid data** per manufacturer spec
- Empty fields are unused
- Checksum is XOR of all characters between `$` and `*`
