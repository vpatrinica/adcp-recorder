"""Synthetic E2E tests using real NMEA sentences from production DuckDB data.

These tests take actual NMEA sentences recorded from a Nortek Signature1000 ADCP,
feed them through the parser pipeline, and compare the parsed `to_dict()` output
against expected values. No database or file I/O is performed — all comparisons
are in-memory.

Any warning or error on a valid record indicates a parser bug.

Data sourced from: utils/adcp-data/db/adcp.duckdb (latest records with edge cases).
"""

import pytest

from adcp_recorder.core.nmea import compute_checksum
from adcp_recorder.parsers.pnora import PNORA
from adcp_recorder.parsers.pnorb import PNORB
from adcp_recorder.parsers.pnorc import PNORC, PNORC1, PNORC2, PNORC3, PNORC4
from adcp_recorder.parsers.pnore import PNORE
from adcp_recorder.parsers.pnorf import PNORF
from adcp_recorder.parsers.pnorh import PNORH3, PNORH4
from adcp_recorder.parsers.pnori import PNORI, PNORI1, PNORI2
from adcp_recorder.parsers.pnors import PNORS, PNORS1, PNORS2, PNORS3, PNORS4
from adcp_recorder.parsers.pnorw import PNORW
from adcp_recorder.parsers.pnorwd import PNORWD

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _recompute(sentence: str) -> str:
    """Recompute checksum on a sentence to ensure validity."""
    base = sentence.split("*")[0] if "*" in sentence else sentence
    cs = compute_checksum(base)
    return f"{base}*{cs}"


# ---------------------------------------------------------------------------
# PNORI — Instrument Configuration (DF=100)
# ---------------------------------------------------------------------------


class TestPNORIRealData:
    """Real Signature1000 PNORI sentences from production."""

    def test_pnori_real_config(self):
        """Test parsing real instrument configuration sentence."""
        sentence = "$PNORI,4,Signature1000_100297,4,9,0.20,1.00,0*7B"
        msg = PNORI.from_nmea(sentence)
        d = msg.to_dict()

        assert d["sentence_type"] == "PNORI"
        assert d["instrument_type_code"] == 4
        assert d["instrument_type_name"] == "SIGNATURE"
        assert d["head_id"] == "Signature1000_100297"
        assert d["beam_count"] == 4
        assert d["cell_count"] == 9
        assert d["blanking_distance"] == pytest.approx(0.20)
        assert d["cell_size"] == pytest.approx(1.00)
        assert d["coord_system_name"] == "ENU"
        assert d["coord_system_code"] == 0
        assert d["checksum"] == "7B"


# ---------------------------------------------------------------------------
# PNORI1 — Instrument Configuration (DF=101)
# ---------------------------------------------------------------------------


class TestPNORI1RealData:
    """Real Signature1000 PNORI1 sentences from production."""

    def test_pnori1_real_config(self):
        """Test parsing real DF=101 instrument configuration."""
        sentence = "$PNORI1,4,100297,4,10,0.20,1.00,ENU*06"
        msg = PNORI1.from_nmea(sentence)
        d = msg.to_dict()

        assert d["sentence_type"] == "PNORI1"
        assert d["instrument_type_code"] == 4
        assert d["instrument_type_name"] == "SIGNATURE"
        assert d["head_id"] == "100297"
        assert d["beam_count"] == 4
        assert d["cell_count"] == 10
        assert d["blanking_distance"] == pytest.approx(0.20)
        assert d["cell_size"] == pytest.approx(1.00)
        assert d["coord_system_name"] == "ENU"
        assert d["coord_system_code"] == 0
        assert d["checksum"] == "06"


# ---------------------------------------------------------------------------
# PNORS — Sensor Data (DF=100)
# ---------------------------------------------------------------------------


class TestPNORSRealData:
    """Real Signature1000 PNORS sentences from production."""

    def test_pnors_latest_record(self):
        """Latest sensor reading with real heading/pitch/roll values."""
        sentence = (
            "$PNORS,011626,111136,00000000,3EC40002,23.7,1530.3,308.8,-40.8,84.3,0.000,23.34,0,0*7F"
        )
        msg = PNORS.from_nmea(sentence)
        d = msg.to_dict()

        assert d["sentence_type"] == "PNORS"
        assert d["date"] == "011626"
        assert d["time"] == "111136"
        assert d["error_code"] == "00000000"
        assert d["status_code"] == "3EC40002"
        assert d["battery"] == pytest.approx(23.7)
        assert d["sound_speed"] == pytest.approx(1530.3)
        assert d["heading"] == pytest.approx(308.8)
        assert d["pitch"] == pytest.approx(-40.8)
        assert d["roll"] == pytest.approx(84.3)
        assert d["pressure"] == pytest.approx(0.000)
        assert d["temperature"] == pytest.approx(23.34)
        assert d["analog1"] == 0
        assert d["analog2"] == 0
        assert d["checksum"] == "7F"

    def test_pnors_second_record(self):
        """Second-latest sensor reading (slightly different heading)."""
        sentence = (
            "$PNORS,011626,111036,00000000,3EC40002,23.6,1530.3,308.9,-40.8,84.3,0.000,23.34,0,0*7E"
        )
        msg = PNORS.from_nmea(sentence)
        d = msg.to_dict()

        assert d["battery"] == pytest.approx(23.6)
        assert d["heading"] == pytest.approx(308.9)

    def test_pnors_third_record(self):
        """Third-latest sensor reading (heading=309.8, roll=84.4)."""
        sentence = (
            "$PNORS,011626,110936,00000000,3EC40002,23.7,1530.3,309.8,-40.8,84.4,0.000,23.34,0,0*70"
        )
        msg = PNORS.from_nmea(sentence)
        d = msg.to_dict()

        assert d["heading"] == pytest.approx(309.8)
        assert d["roll"] == pytest.approx(84.4)


# ---------------------------------------------------------------------------
# PNORS1 — Sensor Data with Uncertainty (DF=101)
# ---------------------------------------------------------------------------


class TestPNORS1RealData:
    """Real Signature1000 PNORS1 sentences from production."""

    def test_pnors1_latest_record(self):
        """Latest DF=101 sensor reading with std dev fields."""
        sentence = (
            "$PNORS1,021326,232518,0,3EC40002,23.7,1528.5,"
            "0.72,224.9,-8.8,0.01,87.3,0.03,0.000,0.00,22.62*49"
        )
        msg = PNORS1.from_nmea(sentence)
        d = msg.to_dict()

        assert d["sentence_type"] == "PNORS1"
        assert d["date"] == "021326"
        assert d["time"] == "232518"
        assert d["error_code"] == 0  # integer in DF=101
        assert d["status_code"] == "3EC40002"
        assert d["battery"] == pytest.approx(23.7)
        assert d["sound_speed"] == pytest.approx(1528.5)
        assert d["heading_std_dev"] == pytest.approx(0.72)
        assert d["heading"] == pytest.approx(224.9)
        assert d["pitch"] == pytest.approx(-8.8)
        assert d["pitch_std_dev"] == pytest.approx(0.01)
        assert d["roll"] == pytest.approx(87.3)
        assert d["roll_std_dev"] == pytest.approx(0.03)
        assert d["pressure"] == pytest.approx(0.000)
        assert d["pressure_std_dev"] == pytest.approx(0.00)
        assert d["temperature"] == pytest.approx(22.62)
        assert d["checksum"] == "49"

    def test_pnors1_second_record(self):
        """Second-latest DF=101 reading (heading=223.2, heading_std=0.73)."""
        sentence = (
            "$PNORS1,021326,232418,0,3EC40002,23.7,1528.5,"
            "0.73,223.2,-8.8,0.02,87.3,0.03,0.000,0.00,22.62*46"
        )
        msg = PNORS1.from_nmea(sentence)
        d = msg.to_dict()

        assert d["heading_std_dev"] == pytest.approx(0.73)
        assert d["heading"] == pytest.approx(223.2)
        assert d["pitch_std_dev"] == pytest.approx(0.02)


# ---------------------------------------------------------------------------
# PNORC — Current Velocity (DF=100, sentinel velocities)
# ---------------------------------------------------------------------------


class TestPNORCRealData:
    """Real Signature1000 PNORC sentences — all velocities are -32.77 sentinel."""

    def test_pnorc_cell9_sentinel_velocities(self):
        """Cell 9: all velocities sentinel, zero correlations."""
        sentence = (
            "$PNORC,011626,111136,9,-32.77,-32.77,-32.77,-32.77,"
            "46.34,225.0,C,68,69,66,65,0,0,0,0*3F"
        )
        msg = PNORC.from_nmea(sentence)
        d = msg.to_dict()

        assert d["sentence_type"] == "PNORC"
        assert d["date"] == "011626"
        assert d["time"] == "111136"
        assert d["cell_index"] == 9
        # Sentinel velocities pass through as floats (NOT treated as None)
        assert d["vel1"] == pytest.approx(-32.77)
        assert d["vel2"] == pytest.approx(-32.77)
        assert d["vel3"] == pytest.approx(-32.77)
        assert d["vel4"] == pytest.approx(-32.77)
        assert d["speed"] == pytest.approx(46.34)
        assert d["direction"] == pytest.approx(225.0)
        assert d["amp_unit"] == "C"
        assert d["amp1"] == 68
        assert d["amp2"] == 69
        assert d["amp3"] == 66
        assert d["amp4"] == 65
        assert d["corr1"] == 0
        assert d["corr2"] == 0
        assert d["corr3"] == 0
        assert d["corr4"] == 0

    def test_pnorc_cell1_with_nonzero_correlations(self):
        """Cell 1: sentinel velocities but non-zero correlations."""
        sentence = (
            "$PNORC,011626,111136,1,-32.77,-32.77,-32.77,-32.77,"
            "46.34,225.0,C,68,68,64,63,52,53,37,40*33"
        )
        msg = PNORC.from_nmea(sentence)
        d = msg.to_dict()

        assert d["cell_index"] == 1
        assert d["amp1"] == 68
        assert d["amp3"] == 64
        assert d["amp4"] == 63
        assert d["corr1"] == 52
        assert d["corr2"] == 53
        assert d["corr3"] == 37
        assert d["corr4"] == 40


# ---------------------------------------------------------------------------
# PNORC1 — Current Velocity (DF=101, sentinel velocities, cell distance)
# ---------------------------------------------------------------------------


class TestPNORC1RealData:
    """Real PNORC1 sentences — sentinel -32.768, with cell_distance field."""

    def test_pnorc1_cell10_sentinel(self):
        """Cell 10: distance=10.2, sentinel velocities, zero correlations."""
        sentence = (
            "$PNORC1,021326,232518,10,10.2,-32.768,-32.768,"
            "-32.768,-32.768,36.1,38.4,35.2,35.2,0,0,0,0*6D"
        )
        msg = PNORC1.from_nmea(sentence)
        d = msg.to_dict()

        assert d["sentence_type"] == "PNORC1"
        assert d["date"] == "021326"
        assert d["time"] == "232518"
        assert d["cell_index"] == 10
        assert d["distance"] == pytest.approx(10.2)
        # -32.768 sentinel passes through as float
        assert d["vel1"] == pytest.approx(-32.768)
        assert d["vel2"] == pytest.approx(-32.768)
        assert d["vel3"] == pytest.approx(-32.768)
        assert d["vel4"] == pytest.approx(-32.768)
        # Amplitudes are float in DF=101
        assert d["amp1"] == pytest.approx(36.1)
        assert d["amp2"] == pytest.approx(38.4)
        assert d["amp3"] == pytest.approx(35.2)
        assert d["amp4"] == pytest.approx(35.2)
        assert d["corr1"] == 0
        assert d["corr2"] == 0
        assert d["corr3"] == 0
        assert d["corr4"] == 0

    def test_pnorc1_cell1_nonzero_correlations(self):
        """Cell 1: distance=1.2, sentinel velocities, mixed correlations."""
        sentence = (
            "$PNORC1,021326,232518,1,1.2,-32.768,-32.768,"
            "-32.768,-32.768,33.7,36.3,34.9,33.2,0,66,55,53*5D"
        )
        msg = PNORC1.from_nmea(sentence)
        d = msg.to_dict()

        assert d["cell_index"] == 1
        assert d["distance"] == pytest.approx(1.2)
        assert d["amp1"] == pytest.approx(33.7)
        assert d["corr1"] == 0
        assert d["corr2"] == 66
        assert d["corr3"] == 55
        assert d["corr4"] == 53


# ---------------------------------------------------------------------------
# PNORB — Wave Burst Parameters
# ---------------------------------------------------------------------------


class TestPNORBRealData:
    """Real PNORB sentences — includes -99.99 sentinel and fully valid records."""

    def test_pnorb_with_minus9_sentinels(self):
        """Record with -99.99 sentinels for optional wave parameters.

        Real record: hm0=20.50 (valid), tm02=-99.99 (None), tp=4.42 (valid),
        dir_tp/spr_tp/main_dir all -99.99 (None).
        """
        sentence = (
            "$PNORB,021326,225248,1,4,0.21,0.99,20.50,-99.99,4.42,-99.99,-99.99,-99.99,0000*51"
        )
        msg = PNORB.from_nmea(sentence)
        d = msg.to_dict()

        assert d["sentence_type"] == "PNORB"
        assert d["date"] == "021326"
        assert d["time"] == "225248"
        assert d["spectrum_basis"] == 1
        assert d["processing_method"] == 4
        assert d["freq_low"] == pytest.approx(0.21)
        assert d["freq_high"] == pytest.approx(0.99)
        assert d["hm0"] == pytest.approx(20.50)
        assert d["tm02"] is None  # -99.99 → None
        assert d["tp"] == pytest.approx(4.42)
        assert d["dir_tp"] is None  # -99.99 → None
        assert d["spr_tp"] is None  # -99.99 → None
        assert d["main_dir"] is None  # -99.99 → None
        assert d["wave_error_code"] == "0000"

    def test_pnorb_all_valid_fields(self):
        """Record where all optional fields have real values."""
        sentence = "$PNORB,021326,222348,1,4,0.21,0.99,0.02,1.73,2.99,198.25,73.25,156.07,0000*56"
        msg = PNORB.from_nmea(sentence)
        d = msg.to_dict()

        assert d["hm0"] == pytest.approx(0.02)
        assert d["tm02"] == pytest.approx(1.73)
        assert d["tp"] == pytest.approx(2.99)
        assert d["dir_tp"] == pytest.approx(198.25)
        assert d["spr_tp"] == pytest.approx(73.25)
        assert d["main_dir"] == pytest.approx(156.07)

    def test_pnorb_low_frequency_burst(self):
        """Second burst of same measurement (low-frequency band)."""
        sentence = "$PNORB,021326,222348,1,4,0.02,0.20,0.01,8.03,12.29,303.78,78.26,132.33,0000*67"
        msg = PNORB.from_nmea(sentence)
        d = msg.to_dict()

        assert d["freq_low"] == pytest.approx(0.02)
        assert d["freq_high"] == pytest.approx(0.20)
        assert d["hm0"] == pytest.approx(0.01)
        assert d["tm02"] == pytest.approx(8.03)
        assert d["tp"] == pytest.approx(12.29)
        assert d["dir_tp"] == pytest.approx(303.78)


# ---------------------------------------------------------------------------
# PNORW — Wave Statistics
# ---------------------------------------------------------------------------


class TestPNORWRealData:
    """Real PNORW sentences — mixed valid/-99.99 and all -99.99 edge cases."""

    def test_pnorw_mixed_valid_and_sentinels(self):
        """Record with mix of valid values and -99.99 sentinels."""
        sentence = (
            "$PNORW,021326,222348,1,4,0.03,-99.99,0.04,0.05,1.91,2.99,-99.99,"
            "198.40,73.25,94.84,0.12,0.00,550,0,1.96,136.35,0D0B*72"
        )
        msg = PNORW.from_nmea(sentence)
        d = msg.to_dict()

        assert d["sentence_type"] == "PNORW"
        assert d["date"] == "021326"
        assert d["time"] == "222348"
        assert d["spectrum_basis"] == 1
        assert d["processing_method"] == 4
        assert d["hm0"] == pytest.approx(0.03)
        assert d["h3"] is None  # -99.99
        assert d["h10"] == pytest.approx(0.04)
        assert d["hmax"] == pytest.approx(0.05)
        assert d["tm02"] == pytest.approx(1.91)
        assert d["tp"] == pytest.approx(2.99)
        assert d["tz"] is None  # -99.99
        assert d["dir_tp"] == pytest.approx(198.40)
        assert d["spr_tp"] == pytest.approx(73.25)
        assert d["main_dir"] == pytest.approx(94.84)
        assert d["uni_index"] == pytest.approx(0.12)
        assert d["mean_pressure"] == pytest.approx(0.00)
        assert d["num_no_detects"] == 550
        assert d["num_bad_detects"] == 0
        assert d["near_surface_speed"] == pytest.approx(1.96)
        assert d["near_surface_dir"] == pytest.approx(136.35)
        assert d["wave_error_code"] == "0D0B"

    def test_pnorw_mostly_sentinels(self):
        """Record where most wave stats are -99.99 but some are valid."""
        sentence = (
            "$PNORW,021326,225248,1,4,-99.99,-99.99,192.68,253.37,-99.99,12.38,"
            "-99.99,-99.99,-99.99,-99.99,-99.99,0.00,496,0,2.00,136.29,0D9B*47"
        )
        msg = PNORW.from_nmea(sentence)
        d = msg.to_dict()

        assert d["hm0"] is None
        assert d["h3"] is None
        assert d["h10"] == pytest.approx(192.68)
        assert d["hmax"] == pytest.approx(253.37)
        assert d["tm02"] is None
        assert d["tp"] == pytest.approx(12.38)
        assert d["tz"] is None
        assert d["dir_tp"] is None
        assert d["spr_tp"] is None
        assert d["main_dir"] is None
        assert d["uni_index"] is None
        assert d["mean_pressure"] == pytest.approx(0.00)
        assert d["num_no_detects"] == 496
        assert d["near_surface_speed"] == pytest.approx(2.00)
        assert d["wave_error_code"] == "0D9B"

    def test_pnorw_all_wave_sentinels(self):
        """Record where all wave measurements are -99.99 (no valid wave data)."""
        sentence = (
            "$PNORW,021326,010748,1,4,-99.99,-99.99,-99.99,-99.99,-99.99,"
            "-99.99,-99.99,-99.99,-99.99,-99.99,-99.99,0.00,515,0,"
            "1.97,134.33,0D1B*61"
        )
        msg = PNORW.from_nmea(sentence)
        d = msg.to_dict()

        assert d["hm0"] is None
        assert d["h3"] is None
        assert d["h10"] is None
        assert d["hmax"] is None
        assert d["tm02"] is None
        assert d["tp"] is None
        assert d["tz"] is None
        assert d["dir_tp"] is None
        assert d["spr_tp"] is None
        assert d["main_dir"] is None
        assert d["uni_index"] is None
        # Non-wave fields still have real values
        assert d["mean_pressure"] == pytest.approx(0.00)
        assert d["num_no_detects"] == 515
        assert d["num_bad_detects"] == 0
        assert d["near_surface_speed"] == pytest.approx(1.97)
        assert d["near_surface_dir"] == pytest.approx(134.33)
        assert d["wave_error_code"] == "0D1B"


# ---------------------------------------------------------------------------
# PNORE — Energy Density Spectrum (truncated to first 22 values for brevity)
# ---------------------------------------------------------------------------


class TestPNORERealData:
    """Real PNORE sentences — 98-frequency energy density spectra."""

    def test_pnore_with_real_energy_data(self):
        """Spectrum with real energy values in first 22 bins, zeros after."""
        # Full 98-value sentence from production (id=364)
        energies = (
            "0.047,2.722,48.345,450.248,2787.814,13023.619,49505.240,"
            "23110.268,11182.673,6619.859,5402.685,4255.501,3981.173,"
            "4518.136,4442.116,3330.520,2608.781,2425.357,1861.114,"
            "1681.874,1217.472,1407.955"
        )
        # Remaining 76 bins are 0.000
        zeros = ",".join(["0.000"] * 76)
        raw = f"$PNORE,021326,225248,1,0.02,0.01,98,{energies},{zeros}"
        sentence = _recompute(raw)

        msg = PNORE.from_nmea(sentence)
        d = msg.to_dict()

        assert d["sentence_type"] == "PNORE"
        assert d["date"] == "021326"
        assert d["time"] == "225248"
        assert d["spectrum_basis"] == 1
        assert d["start_frequency"] == pytest.approx(0.02)
        assert d["step_frequency"] == pytest.approx(0.01)
        assert d["num_frequencies"] == 98
        assert len(d["energy_densities"]) == 98

        # Verify specific energy values
        assert d["energy_densities"][0] == pytest.approx(0.047)
        assert d["energy_densities"][1] == pytest.approx(2.722)
        assert d["energy_densities"][6] == pytest.approx(49505.240)
        assert d["energy_densities"][21] == pytest.approx(1407.955)
        # All remaining bins should be 0.0
        assert d["energy_densities"][22] == pytest.approx(0.0)
        assert d["energy_densities"][97] == pytest.approx(0.0)

    def test_pnore_all_zeros(self):
        """Spectrum where all energy values are zero."""
        zeros = ",".join(["0.000"] * 98)
        raw = f"$PNORE,021326,222348,1,0.02,0.01,98,{zeros}"
        sentence = _recompute(raw)

        msg = PNORE.from_nmea(sentence)
        d = msg.to_dict()

        assert d["num_frequencies"] == 98
        assert all(v == pytest.approx(0.0) for v in d["energy_densities"])


# ---------------------------------------------------------------------------
# PNORF — Fourier Coefficients (A1/B1/A2/B2)
# ---------------------------------------------------------------------------


class TestPNORFRealData:
    """Real PNORF sentences — 4 coefficient types per measurement."""

    def test_pnorf_a1_valid_coefficients(self):
        """A1 Fourier coefficients with real data."""
        # First 10 coefficients from production A1 record, rest zeros for brevity
        coeffs_real = "0.0526,0.0153,-0.0238,-0.0030"
        coeffs_zero = ",".join(["0.0000"] * 94)
        raw = f"$PNORF,A1,021326,222348,1,0.02,0.01,98,{coeffs_real},{coeffs_zero}"
        sentence = _recompute(raw)

        msg = PNORF.from_nmea(sentence)
        d = msg.to_dict()

        assert d["sentence_type"] == "PNORF"
        assert d["coefficient_flag"] == "A1"
        assert d["date"] == "021326"
        assert d["time"] == "222348"
        assert d["spectrum_basis"] == 1
        assert d["start_frequency"] == pytest.approx(0.02)
        assert d["step_frequency"] == pytest.approx(0.01)
        assert d["num_frequencies"] == 98
        assert len(d["coefficients"]) == 98
        assert d["coefficients"][0] == pytest.approx(0.0526)
        assert d["coefficients"][1] == pytest.approx(0.0153)
        assert d["coefficients"][2] == pytest.approx(-0.0238)
        assert d["coefficients"][3] == pytest.approx(-0.0030)

    def test_pnorf_b2_negative_coefficients(self):
        """B2 Fourier coefficients — typically large negative values."""
        coeffs_real = "-0.9285,-0.8940,-0.8077,-0.8006"
        coeffs_zero = ",".join(["0.0000"] * 94)
        raw = f"$PNORF,B2,021326,222348,1,0.02,0.01,98,{coeffs_real},{coeffs_zero}"
        sentence = _recompute(raw)

        msg = PNORF.from_nmea(sentence)
        d = msg.to_dict()

        assert d["coefficient_flag"] == "B2"
        assert d["coefficients"][0] == pytest.approx(-0.9285)
        assert d["coefficients"][1] == pytest.approx(-0.8940)
        assert d["coefficients"][2] == pytest.approx(-0.8077)
        assert d["coefficients"][3] == pytest.approx(-0.8006)

    def test_pnorf_all_minus9_sentinels(self):
        """Record where all coefficients are -999.9999 sentinel (no valid data)."""
        sentinels = ",".join(["-999.9999"] * 98)
        raw = f"$PNORF,A2,021326,225248,1,0.02,0.01,98,{sentinels}"
        sentence = _recompute(raw)

        msg = PNORF.from_nmea(sentence)
        d = msg.to_dict()

        assert d["coefficient_flag"] == "A2"
        assert d["num_frequencies"] == 98
        assert len(d["coefficients"]) == 98
        # All -999.9999 should be parsed as None
        assert all(c is None for c in d["coefficients"])

    def test_pnorf_all_four_flags_parse(self):
        """Verify all four coefficient flags (A1, B1, A2, B2) parse cleanly."""
        coeffs = ",".join(["0.1234"] * 98)
        for flag in ("A1", "B1", "A2", "B2"):
            raw = f"$PNORF,{flag},021326,222348,1,0.02,0.01,98,{coeffs}"
            sentence = _recompute(raw)
            msg = PNORF.from_nmea(sentence)
            assert msg.to_dict()["coefficient_flag"] == flag


# ---------------------------------------------------------------------------
# PNORWD — Directional Spectra (MD and DS)
# ---------------------------------------------------------------------------


class TestPNORWDRealData:
    """Real PNORWD sentences — MD (Mean Direction) and DS (Directional Spread)."""

    def test_pnorwd_ds_valid_data(self):
        """DS (Directional Spread) with real spread values."""
        # First 4 values from production, rest filled for brevity
        vals_real = "78.0052,79.9675,80.0364,80.6764"
        vals_zero = ",".join(["0.0000"] * 94)
        raw = f"$PNORWD,DS,021326,222348,1,0.02,0.01,98,{vals_real},{vals_zero}"
        sentence = _recompute(raw)

        msg = PNORWD.from_nmea(sentence)
        d = msg.to_dict()

        assert d["sentence_type"] == "PNORWD"
        assert d["direction_type"] == "DS"
        assert d["date"] == "021326"
        assert d["time"] == "222348"
        assert d["spectrum_basis"] == 1
        assert d["start_frequency"] == pytest.approx(0.02)
        assert d["step_frequency"] == pytest.approx(0.01)
        assert d["num_frequencies"] == 98
        assert len(d["values"]) == 98
        assert d["values"][0] == pytest.approx(78.0052)
        assert d["values"][1] == pytest.approx(79.9675)
        assert d["values"][2] == pytest.approx(80.0364)
        assert d["values"][3] == pytest.approx(80.6764)

    def test_pnorwd_md_valid_data(self):
        """MD (Mean Direction) with real direction values."""
        vals_real = "315.9213,306.0914,168.0277,110.5509"
        vals_zero = ",".join(["0.0000"] * 94)
        raw = f"$PNORWD,MD,021326,222348,1,0.02,0.01,98,{vals_real},{vals_zero}"
        sentence = _recompute(raw)

        msg = PNORWD.from_nmea(sentence)
        d = msg.to_dict()

        assert d["direction_type"] == "MD"
        assert d["values"][0] == pytest.approx(315.9213)
        assert d["values"][1] == pytest.approx(306.0914)
        assert d["values"][2] == pytest.approx(168.0277)
        assert d["values"][3] == pytest.approx(110.5509)

    def test_pnorwd_all_minus9_sentinels(self):
        """DS record where all values are -999.9999 sentinel (no valid data)."""
        sentinels = ",".join(["-999.9999"] * 98)
        raw = f"$PNORWD,DS,021326,225248,1,0.02,0.01,98,{sentinels}"
        sentence = _recompute(raw)

        msg = PNORWD.from_nmea(sentence)
        d = msg.to_dict()

        assert d["direction_type"] == "DS"
        assert d["num_frequencies"] == 98
        assert all(v is None for v in d["values"])


# ---------------------------------------------------------------------------
# Checksum Integrity Tests
# ---------------------------------------------------------------------------


class TestChecksumIntegrity:
    """Verify all real sentences have valid checksums that survive round-trip."""

    REAL_SENTENCES = [
        "$PNORI,4,Signature1000_100297,4,9,0.20,1.00,0*7B",
        "$PNORI1,4,100297,4,10,0.20,1.00,ENU*06",
        "$PNORS,011626,111136,00000000,3EC40002,23.7,1530.3,308.8,-40.8,84.3,0.000,23.34,0,0*7F",
        "$PNORS1,021326,232518,0,3EC40002,23.7,1528.5,0.72,224.9,-8.8,0.01,87.3,0.03,0.000,0.00,22.62*49",
        "$PNORC,011626,111136,9,-32.77,-32.77,-32.77,-32.77,46.34,225.0,C,68,69,66,65,0,0,0,0*3F",
        "$PNORC1,021326,232518,10,10.2,-32.768,-32.768,-32.768,-32.768,36.1,38.4,35.2,35.2,0,0,0,0*6D",
        "$PNORB,021326,225248,1,4,0.21,0.99,20.50,-9.00,4.42,-9.00,-9.00,-9.00,0000*51",
        "$PNORB,021326,222348,1,4,0.21,0.99,0.02,1.73,2.99,198.25,73.25,156.07,0000*56",
    ]

    @pytest.mark.parametrize("sentence", REAL_SENTENCES)
    def test_checksum_validity(self, sentence: str):
        """Verify that recomputed checksum matches the original."""
        expected_cs = sentence.rsplit("*", 1)[1]
        computed_cs = compute_checksum(sentence)
        assert computed_cs == expected_cs, (
            f"Checksum mismatch for {sentence[:30]}...: expected {expected_cs}, got {computed_cs}"
        )


# ---------------------------------------------------------------------------
# Edge Case: -nan handling (regression test for the bug we fixed)
# ---------------------------------------------------------------------------


class TestNanEdgeCases:
    """Test that -nan and +nan are properly handled as None by all parsers."""

    def test_pnorb_minus_nan_fields(self):
        """Regression: -nan in PNORB fields should parse as None, not raise."""
        # This is the exact pattern that caused parse error #6 in production
        raw = "$PNORB,021326,225248,1,4,0.21,0.99,-nan,-nan,-nan,-nan,-nan,-nan,0000"
        sentence = _recompute(raw)
        msg = PNORB.from_nmea(sentence)
        d = msg.to_dict()

        assert d["hm0"] is None
        assert d["tm02"] is None
        assert d["tp"] is None
        assert d["dir_tp"] is None
        assert d["spr_tp"] is None
        assert d["main_dir"] is None

    def test_pnorw_plus_nan_fields(self):
        """+nan should also be treated as None."""
        raw = (
            "$PNORW,021326,222348,1,4,+nan,+nan,+nan,+nan,+nan,+nan,+nan,"
            "+nan,+nan,+nan,+nan,0.00,0,0,0.00,0.00,0000"
        )
        sentence = _recompute(raw)
        msg = PNORW.from_nmea(sentence)
        d = msg.to_dict()

        assert d["hm0"] is None
        assert d["h3"] is None
        assert d["tp"] is None

    def test_pnors_minus_nan_analog(self):
        """-nan in integer fields (analog1/analog2) should parse as None."""
        raw = (
            "$PNORS,011626,111136,00000000,3EC40002,"
            "23.7,1530.3,308.8,-40.8,84.3,0.000,23.34,-nan,-nan"
        )
        sentence = _recompute(raw)
        msg = PNORS.from_nmea(sentence)
        d = msg.to_dict()

        assert d["analog1"] is None
        assert d["analog2"] is None

    def test_pnors1_minus_nan_error_code(self):
        """-nan in error_code (integer) should parse as None."""
        raw = (
            "$PNORS1,021326,232518,-nan,3EC40002,"
            "23.7,1528.5,0.72,224.9,-8.8,0.01,87.3,0.03,0.000,0.00,22.62"
        )
        sentence = _recompute(raw)
        msg = PNORS1.from_nmea(sentence)
        d = msg.to_dict()

        assert d["error_code"] is None

    def test_pnorc_minus_nan_correlations(self):
        """-nan in correlation fields should parse as None."""
        raw = (
            "$PNORC,011626,111136,1,-32.77,-32.77,-32.77,-32.77,"
            "46.34,225.0,C,68,68,64,63,-nan,-nan,-nan,-nan"
        )
        sentence = _recompute(raw)
        msg = PNORC.from_nmea(sentence)
        d = msg.to_dict()

        assert d["corr1"] is None
        assert d["corr2"] is None
        assert d["corr3"] is None
        assert d["corr4"] is None

    def test_pnori_minus_nan_beam_cell(self):
        """-nan in beam_count/cell_count should parse as None."""
        raw = "$PNORI,4,HEAD1,-nan,-nan,0.20,1.00,0"
        sentence = _recompute(raw)
        msg = PNORI.from_nmea(sentence)
        d = msg.to_dict()

        assert d["beam_count"] is None
        assert d["cell_count"] is None


# ---------------------------------------------------------------------------
# PNORI2 — Instrument Configuration (DF=102, Tagged)
# ---------------------------------------------------------------------------


class TestPNORI2SpecData:
    """PNORI2 tests using spec-documented examples."""

    def test_pnori2_spec_example_beam(self):
        """Spec example: Signature with BEAM coords."""
        raw = "$PNORI2,IT=4,SN=123456,NB=4,NC=30,BD=1.00,CS=5.00,CY=BEAM"
        sentence = _recompute(raw)
        msg = PNORI2.from_nmea(sentence)
        d = msg.to_dict()

        assert d["sentence_type"] == "PNORI2"
        assert d["instrument_type_code"] == 4
        assert d["instrument_type_name"] == "SIGNATURE"
        assert d["head_id"] == "123456"
        assert d["beam_count"] == 4
        assert d["cell_count"] == 30
        assert d["blanking_distance"] == pytest.approx(1.00)
        assert d["cell_size"] == pytest.approx(5.00)
        assert d["coord_system_name"] == "BEAM"
        assert d["coord_system_code"] == 2

    def test_pnori2_enu_coords(self):
        """ENU coordinate system parsing."""
        raw = "$PNORI2,IT=4,SN=100297,NB=4,NC=20,BD=0.20,CS=1.00,CY=ENU"
        sentence = _recompute(raw)
        msg = PNORI2.from_nmea(sentence)
        d = msg.to_dict()

        assert d["coord_system_name"] == "ENU"
        assert d["coord_system_code"] == 0
        assert d["blanking_distance"] == pytest.approx(0.20)

    def test_pnori2_xyz_different_order(self):
        """Tags in non-canonical order should still parse."""
        raw = "$PNORI2,CY=XYZ,CS=2.00,BD=0.50,NC=15,NB=4,SN=999888,IT=4"
        sentence = _recompute(raw)
        msg = PNORI2.from_nmea(sentence)
        d = msg.to_dict()

        assert d["coord_system_name"] == "XYZ"
        assert d["coord_system_code"] == 1
        assert d["head_id"] == "999888"
        assert d["cell_count"] == 15
        assert d["cell_size"] == pytest.approx(2.00)

    def test_pnori2_aquadopp_3beam(self):
        """Aquadopp (IT=0) with 3 beams."""
        raw = "$PNORI2,IT=0,SN=54321,NB=3,NC=10,BD=0.40,CS=1.50,CY=ENU"
        sentence = _recompute(raw)
        msg = PNORI2.from_nmea(sentence)
        d = msg.to_dict()

        assert d["instrument_type_code"] == 0
        assert d["instrument_type_name"] == "AQUADOPP"
        assert d["beam_count"] == 3


# ---------------------------------------------------------------------------
# PNORS2 — Sensor Data with Uncertainty (DF=102, Tagged)
# ---------------------------------------------------------------------------


class TestPNORS2SpecData:
    """PNORS2 tests using spec-documented examples."""

    def test_pnors2_spec_example(self):
        """Spec example with all fields populated."""
        raw = (
            "$PNORS2,DATE=083013,TIME=132455,"
            "EC=0,SC=34000034,BV=22.9,SS=1500.0,"
            "HSD=0.02,H=123.4,PI=45.6,PISD=0.02,"
            "R=23.4,RSD=0.02,P=123.456,PSD=0.02,T=24.56"
        )
        sentence = _recompute(raw)
        msg = PNORS2.from_nmea(sentence)
        d = msg.to_dict()

        assert d["sentence_type"] == "PNORS2"
        assert d["date"] == "083013"
        assert d["time"] == "132455"
        assert d["error_code"] == 0
        assert d["status_code"] == "34000034"
        assert d["battery"] == pytest.approx(22.9)
        assert d["sound_speed"] == pytest.approx(1500.0)
        assert d["heading_std_dev"] == pytest.approx(0.02)
        assert d["heading"] == pytest.approx(123.4)
        assert d["pitch"] == pytest.approx(45.6)
        assert d["pitch_std_dev"] == pytest.approx(0.02)
        assert d["roll"] == pytest.approx(23.4)
        assert d["roll_std_dev"] == pytest.approx(0.02)
        assert d["pressure"] == pytest.approx(123.456)
        assert d["pressure_std_dev"] == pytest.approx(0.02)
        assert d["temperature"] == pytest.approx(24.56)

    def test_pnors2_mandatory_only(self):
        """Only DATE, TIME, SC provided — optionals become None."""
        raw = "$PNORS2,DATE=010123,TIME=120000,SC=00000000"
        sentence = _recompute(raw)
        msg = PNORS2.from_nmea(sentence)
        d = msg.to_dict()

        assert d["date"] == "010123"
        assert d["time"] == "120000"
        assert d["status_code"] == "00000000"
        assert d["error_code"] is None
        assert d["battery"] is None
        assert d["sound_speed"] is None
        assert d["heading"] is None
        assert d["temperature"] is None

    def test_pnors2_negative_pitch_roll(self):
        """Negative pitch/roll values."""
        raw = (
            "$PNORS2,DATE=102115,TIME=090715,"
            "EC=0,SC=2A480000,BV=14.4,SS=1523.0,"
            "HSD=0.1,H=275.9,PI=-15.7,PISD=0.2,"
            "R=-2.3,RSD=0.3,P=0.000,PSD=0.001,T=22.45"
        )
        sentence = _recompute(raw)
        msg = PNORS2.from_nmea(sentence)
        d = msg.to_dict()

        assert d["pitch"] == pytest.approx(-15.7)
        assert d["roll"] == pytest.approx(-2.3)
        assert d["heading"] == pytest.approx(275.9)


# ---------------------------------------------------------------------------
# PNORS3 — Compact Sensor Data (DF=103, Tagged, no date/time)
# ---------------------------------------------------------------------------


class TestPNORS3SpecData:
    """PNORS3 tests using spec-documented examples."""

    def test_pnors3_spec_example(self):
        """Spec example with all fields."""
        raw = "$PNORS3,BV=22.9,SS=1546.1,H=151.1,PI=-12.0,R=-5.2,P=705.669,T=24.96"
        sentence = _recompute(raw)
        msg = PNORS3.from_nmea(sentence)
        d = msg.to_dict()

        assert d["sentence_type"] == "PNORS3"
        assert d["battery"] == pytest.approx(22.9)
        assert d["sound_speed"] == pytest.approx(1546.1)
        assert d["heading"] == pytest.approx(151.1)
        assert d["pitch"] == pytest.approx(-12.0)
        assert d["roll"] == pytest.approx(-5.2)
        assert d["pressure"] == pytest.approx(705.669)
        assert d["temperature"] == pytest.approx(24.96)

    def test_pnors3_all_fields(self):
        """All fields with typical deployment values."""
        raw = "$PNORS3,BV=14.4,SS=1523.0,H=275.9,PI=15.7,R=2.3,P=0.000,T=22.45"
        sentence = _recompute(raw)
        msg = PNORS3.from_nmea(sentence)
        d = msg.to_dict()

        assert d["battery"] == pytest.approx(14.4)
        assert d["heading"] == pytest.approx(275.9)

    def test_pnors3_single_tag(self):
        """Only battery provided — others become None."""
        raw = "$PNORS3,BV=12.0"
        sentence = _recompute(raw)
        msg = PNORS3.from_nmea(sentence)
        d = msg.to_dict()

        assert d["battery"] == pytest.approx(12.0)
        assert d["sound_speed"] is None
        assert d["heading"] is None
        assert d["pitch"] is None
        assert d["roll"] is None
        assert d["pressure"] is None
        assert d["temperature"] is None


# ---------------------------------------------------------------------------
# PNORS4 — Minimal Sensor Data (DF=104, positional, no date/time)
# ---------------------------------------------------------------------------


class TestPNORS4SpecData:
    """PNORS4 tests using spec-documented examples."""

    def test_pnors4_spec_example(self):
        """Spec example with all fields."""
        raw = "$PNORS4,14.4,1523.0,275.9,15.7,2.3,0.000,22.45"
        sentence = _recompute(raw)
        msg = PNORS4.from_nmea(sentence)
        d = msg.to_dict()

        assert d["sentence_type"] == "PNORS4"
        assert d["battery"] == pytest.approx(14.4)
        assert d["sound_speed"] == pytest.approx(1523.0)
        assert d["heading"] == pytest.approx(275.9)
        assert d["pitch"] == pytest.approx(15.7)
        assert d["roll"] == pytest.approx(2.3)
        assert d["pressure"] == pytest.approx(0.000)
        assert d["temperature"] == pytest.approx(22.45)

    def test_pnors4_high_pressure_negative_pitch(self):
        """High-pressure deep deployment with negative pitch/roll."""
        raw = "$PNORS4,22.9,1546.1,151.1,-12.0,-5.2,705.669,24.96"
        sentence = _recompute(raw)
        msg = PNORS4.from_nmea(sentence)
        d = msg.to_dict()

        assert d["pressure"] == pytest.approx(705.669)
        assert d["pitch"] == pytest.approx(-12.0)
        assert d["roll"] == pytest.approx(-5.2)


# ---------------------------------------------------------------------------
# PNORC2 — Tagged Current Velocity (DF=102)
# ---------------------------------------------------------------------------


class TestPNORC2SpecData:
    """PNORC2 tests using spec-documented examples."""

    def test_pnorc2_spec_example_beam_tags(self):
        """Spec example: BEAM velocity tags (V1-V4)."""
        raw = (
            "$PNORC2,DATE=083013,TIME=132455,CN=3,"
            "CP=11.0,V1=0.332,V2=0.332,"
            "V3=-0.332,V4=-0.332,A1=78.9,A2=78.9,"
            "A3=78.9,A4=78.9,C1=78,C2=78,C3=78,C4=78"
        )
        sentence = _recompute(raw)
        msg = PNORC2.from_nmea(sentence)
        d = msg.to_dict()

        assert d["sentence_type"] == "PNORC2"
        assert d["date"] == "083013"
        assert d["time"] == "132455"
        assert d["cell_index"] == 3
        assert d["distance"] == pytest.approx(11.0)
        assert d["vel1"] == pytest.approx(0.332)
        assert d["vel2"] == pytest.approx(0.332)
        assert d["vel3"] == pytest.approx(-0.332)
        assert d["vel4"] == pytest.approx(-0.332)
        assert d["amp1"] == pytest.approx(78.9)
        assert d["amp2"] == pytest.approx(78.9)
        assert d["corr1"] == 78
        assert d["corr4"] == 78

    def test_pnorc2_enu_velocity_tags(self):
        """ENU velocity tags (VE/VN/VU/VU2)."""
        raw = (
            "$PNORC2,DATE=102115,TIME=090715,CN=1,"
            "CP=1.00,VE=0.1,VN=0.2,"
            "VU=0.3,VU2=0.4,A1=45.5,A2=46.0,"
            "A3=45.8,A4=45.2,C1=90,C2=91,C3=92,C4=93"
        )
        sentence = _recompute(raw)
        msg = PNORC2.from_nmea(sentence)
        d = msg.to_dict()

        assert d["vel1"] == pytest.approx(0.1)
        assert d["vel2"] == pytest.approx(0.2)
        assert d["vel3"] == pytest.approx(0.3)
        assert d["vel4"] == pytest.approx(0.4)
        assert d["corr1"] == 90
        assert d["corr4"] == 93

    def test_pnorc2_xyz_velocity_tags(self):
        """XYZ velocity tags (VX/VY/VZ/VZ2)."""
        raw = (
            "$PNORC2,DATE=102115,TIME=090715,CN=5,"
            "CP=5.00,VX=-1.5,VY=2.3,"
            "VZ=0.05,VZ2=-0.03,A1=50.1,A2=50.2,"
            "A3=50.3,A4=50.4,C1=85,C2=86,C3=87,C4=88"
        )
        sentence = _recompute(raw)
        msg = PNORC2.from_nmea(sentence)
        d = msg.to_dict()

        assert d["vel1"] == pytest.approx(-1.5)
        assert d["vel2"] == pytest.approx(2.3)
        assert d["vel3"] == pytest.approx(0.05)
        assert d["vel4"] == pytest.approx(-0.03)


# ---------------------------------------------------------------------------
# PNORC3 — Tagged Averaged Current (DF=103)
# ---------------------------------------------------------------------------


class TestPNORC3SpecData:
    """PNORC3 tests using spec-documented examples."""

    def test_pnorc3_spec_example(self):
        """Spec example with all fields."""
        raw = "$PNORC3,CP=4.5,SP=3.519,DIR=110.9,AC=6,AA=28"
        sentence = _recompute(raw)
        msg = PNORC3.from_nmea(sentence)
        d = msg.to_dict()

        assert d["sentence_type"] == "PNORC3"
        assert d["distance"] == pytest.approx(4.5)
        assert d["speed"] == pytest.approx(3.519)
        assert d["direction"] == pytest.approx(110.9)
        assert d["avg_correlation"] == 6
        assert d["avg_amplitude"] == 28

    def test_pnorc3_high_speed(self):
        """Strong current scenario."""
        raw = "$PNORC3,CP=10.5,SP=1.23,DIR=180.5,AA=150,AC=95"
        sentence = _recompute(raw)
        msg = PNORC3.from_nmea(sentence)
        d = msg.to_dict()

        assert d["speed"] == pytest.approx(1.23)
        assert d["direction"] == pytest.approx(180.5)
        assert d["avg_amplitude"] == 150
        assert d["avg_correlation"] == 95

    def test_pnorc3_minimal_distance_only(self):
        """Only CP tag provided — others become None."""
        raw = "$PNORC3,CP=0.5"
        sentence = _recompute(raw)
        msg = PNORC3.from_nmea(sentence)
        d = msg.to_dict()

        assert d["distance"] == pytest.approx(0.5)
        assert d["speed"] is None
        assert d["direction"] is None
        assert d["avg_amplitude"] is None
        assert d["avg_correlation"] is None


# ---------------------------------------------------------------------------
# PNORC4 — Positional Averaged Current (DF=104)
# ---------------------------------------------------------------------------


class TestPNORC4SpecData:
    """PNORC4 tests using spec-documented examples."""

    def test_pnorc4_spec_example(self):
        """Spec example: NW current at 27.5m depth."""
        raw = "$PNORC4,27.5,1.815,322.6,4,28"
        sentence = _recompute(raw)
        msg = PNORC4.from_nmea(sentence)
        d = msg.to_dict()

        assert d["sentence_type"] == "PNORC4"
        assert d["distance"] == pytest.approx(27.5)
        assert d["speed"] == pytest.approx(1.815)
        assert d["direction"] == pytest.approx(322.6)
        assert d["avg_correlation"] == 4
        assert d["avg_amplitude"] == 28

    def test_pnorc4_near_surface(self):
        """Near-surface cell with moderate current."""
        raw = "$PNORC4,10.5,1.23,180.5,95,150"
        sentence = _recompute(raw)
        msg = PNORC4.from_nmea(sentence)
        d = msg.to_dict()

        assert d["distance"] == pytest.approx(10.5)
        assert d["speed"] == pytest.approx(1.23)
        assert d["avg_correlation"] == 95
        assert d["avg_amplitude"] == 150


# ---------------------------------------------------------------------------
# PNORH3 — Tagged Measurement Header (DF=103)
# ---------------------------------------------------------------------------


class TestPNORH3SpecData:
    """PNORH3 tests using spec-documented examples."""

    def test_pnorh3_spec_example(self):
        """Spec example: Nov 12, 2014 header."""
        raw = "$PNORH3,DATE=141112,TIME=081946,EC=0,SC=2A4C0000"
        sentence = _recompute(raw)
        msg = PNORH3.from_nmea(sentence)
        d = msg.to_dict()

        assert d["sentence_type"] == "PNORH3"
        assert d["date"] == "141112"
        assert d["time"] == "081946"
        assert d["error_code"] == 0
        assert d["status_code"] == "2A4C0000"

    def test_pnorh3_nonzero_error(self):
        """Header with a nonzero error code."""
        raw = "$PNORH3,DATE=230615,TIME=143022,EC=5,SC=1A2B3C4D"
        sentence = _recompute(raw)
        msg = PNORH3.from_nmea(sentence)
        d = msg.to_dict()

        assert d["error_code"] == 5
        assert d["status_code"] == "1A2B3C4D"


# ---------------------------------------------------------------------------
# PNORH4 — Positional Measurement Header (DF=104)
# ---------------------------------------------------------------------------


class TestPNORH4SpecData:
    """PNORH4 tests using spec-documented examples."""

    def test_pnorh4_spec_example(self):
        """Spec example: Nov 12, 2014 header."""
        raw = "$PNORH4,141112,083149,0,2A4C0000"
        sentence = _recompute(raw)
        msg = PNORH4.from_nmea(sentence)
        d = msg.to_dict()

        assert d["sentence_type"] == "PNORH4"
        assert d["date"] == "141112"
        assert d["time"] == "083149"
        assert d["error_code"] == 0
        assert d["status_code"] == "2A4C0000"

    def test_pnorh4_high_error_code(self):
        """Header with large error code."""
        raw = "$PNORH4,260101,235959,42,DEADBEEF"
        sentence = _recompute(raw)
        msg = PNORH4.from_nmea(sentence)
        d = msg.to_dict()

        assert d["error_code"] == 42
        assert d["status_code"] == "DEADBEEF"
        assert d["date"] == "260101"
        assert d["time"] == "235959"


# ---------------------------------------------------------------------------
# PNORA — Altitude/Range Data (DF=200 positional, DF=201 tagged)
# ---------------------------------------------------------------------------


class TestPNORASpecData:
    """PNORA tests using spec-documented examples."""

    def test_pnora_positional_spec(self):
        """Positional format (DF=200) with valid altimeter data."""
        raw = "$PNORA,250101,120000,10.5,15.50,95,01,1.5,2.3"
        sentence = _recompute(raw)
        msg = PNORA.from_nmea(sentence)
        d = msg.to_dict()

        assert d["sentence_type"] == "PNORA"
        assert d["date"] == "250101"
        assert d["time"] == "120000"
        assert d["pressure"] == pytest.approx(10.5)
        assert d["distance"] == pytest.approx(15.50)
        assert d["quality"] == 95
        assert d["status"] == "01"
        assert d["pitch"] == pytest.approx(1.5)
        assert d["roll"] == pytest.approx(2.3)

    def test_pnora_tagged_spec(self):
        """Tagged format (DF=201) from spec documentation."""
        raw = "$PNORA,DATE=190902,TIME=122341,P=0.000,A=24.274,Q=13068,ST=08,PI=-2.6,R=-0.8"
        sentence = _recompute(raw)
        msg = PNORA.from_nmea(sentence)
        d = msg.to_dict()

        assert d["sentence_type"] == "PNORA"
        assert d["date"] == "190902"
        assert d["time"] == "122341"
        assert d["pressure"] == pytest.approx(0.000)
        assert d["distance"] == pytest.approx(24.274)
        assert d["quality"] == 13068
        assert d["status"] == "08"
        assert d["pitch"] == pytest.approx(-2.6)
        assert d["roll"] == pytest.approx(-0.8)

    def test_pnora_positional_zero_pressure(self):
        """Surface deployment with zero pressure."""
        raw = "$PNORA,230101,120000,0.000,1.0,1,00,0.0,0.0"
        sentence = _recompute(raw)
        msg = PNORA.from_nmea(sentence)
        d = msg.to_dict()

        assert d["pressure"] == pytest.approx(0.0)
        assert d["distance"] == pytest.approx(1.0)
        assert d["pitch"] == pytest.approx(0.0)
        assert d["roll"] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Additional NaN Edge Cases for New Parser Types
# ---------------------------------------------------------------------------


class TestNanEdgeCasesExtended:
    """NaN/-nan/+nan tests for parser types not covered above."""

    def test_pnori2_minus_nan_beams_cells(self):
        """-nan in NB/NC tags should parse as None."""
        raw = "$PNORI2,IT=4,SN=100297,NB=-nan,NC=-nan,BD=0.20,CS=1.00,CY=ENU"
        sentence = _recompute(raw)
        msg = PNORI2.from_nmea(sentence)
        d = msg.to_dict()

        assert d["beam_count"] is None
        assert d["cell_count"] is None

    def test_pnors2_minus_nan_optional_fields(self):
        """-nan in optional tagged fields should parse as None."""
        raw = (
            "$PNORS2,DATE=102115,TIME=090715,"
            "EC=-nan,SC=2A480000,BV=-nan,SS=-nan,"
            "HSD=-nan,H=-nan,PI=-nan,PISD=-nan,"
            "R=-nan,RSD=-nan,P=-nan,PSD=-nan,T=-nan"
        )
        sentence = _recompute(raw)
        msg = PNORS2.from_nmea(sentence)
        d = msg.to_dict()

        assert d["error_code"] is None
        assert d["battery"] is None
        assert d["sound_speed"] is None
        assert d["heading"] is None
        assert d["pitch"] is None
        assert d["temperature"] is None

    def test_pnors3_plus_nan_all(self):
        """+nan in all PNORS3 tagged fields → all None."""
        raw = "$PNORS3,BV=+nan,SS=+nan,H=+nan,PI=+nan,R=+nan,P=+nan,T=+nan"
        sentence = _recompute(raw)
        msg = PNORS3.from_nmea(sentence)
        d = msg.to_dict()

        assert d["battery"] is None
        assert d["sound_speed"] is None
        assert d["heading"] is None
        assert d["pitch"] is None
        assert d["roll"] is None
        assert d["pressure"] is None
        assert d["temperature"] is None

    def test_pnors4_minus_nan_all(self):
        """-nan in all PNORS4 positional fields → all None."""
        raw = "$PNORS4,-nan,-nan,-nan,-nan,-nan,-nan,-nan"
        sentence = _recompute(raw)
        msg = PNORS4.from_nmea(sentence)
        d = msg.to_dict()

        assert d["battery"] is None
        assert d["sound_speed"] is None
        assert d["heading"] is None
        assert d["pitch"] is None
        assert d["roll"] is None
        assert d["pressure"] is None
        assert d["temperature"] is None

    def test_pnorc2_minus_nan_velocities(self):
        """-nan in velocity and correlation tags → None."""
        raw = (
            "$PNORC2,DATE=102115,TIME=090715,"
            "CN=1,CP=-nan,VE=-nan,VN=-nan,"
            "VU=-nan,VU2=-nan,A1=-nan,A2=-nan,"
            "A3=-nan,A4=-nan,C1=-nan,C2=-nan,C3=-nan,C4=-nan"
        )
        sentence = _recompute(raw)
        msg = PNORC2.from_nmea(sentence)
        d = msg.to_dict()

        assert d["distance"] is None
        assert d["vel1"] is None
        assert d["vel2"] is None
        assert d["corr1"] is None
        assert d["corr4"] is None

    def test_pnorc3_minus_nan_all(self):
        """-nan in all PNORC3 tags → all None."""
        raw = "$PNORC3,CP=-nan,SP=-nan,DIR=-nan,AA=-nan,AC=-nan"
        sentence = _recompute(raw)
        msg = PNORC3.from_nmea(sentence)
        d = msg.to_dict()

        assert d["distance"] is None
        assert d["speed"] is None
        assert d["direction"] is None
        assert d["avg_amplitude"] is None
        assert d["avg_correlation"] is None

    def test_pnorc4_plus_nan_all(self):
        """+nan in all PNORC4 positional fields → all None."""
        raw = "$PNORC4,+nan,+nan,+nan,+nan,+nan"
        sentence = _recompute(raw)
        msg = PNORC4.from_nmea(sentence)
        d = msg.to_dict()

        assert d["distance"] is None
        assert d["speed"] is None
        assert d["direction"] is None
        assert d["avg_correlation"] is None
        assert d["avg_amplitude"] is None

    def test_pnorh3_minus_nan_error_code(self):
        """-nan in EC tag should parse as None."""
        raw = "$PNORH3,DATE=141112,TIME=081946,EC=-nan,SC=2A4C0000"
        sentence = _recompute(raw)
        msg = PNORH3.from_nmea(sentence)
        d = msg.to_dict()

        assert d["error_code"] is None

    def test_pnorh4_minus_nan_error_code(self):
        """-nan in error_code field should parse as None."""
        raw = "$PNORH4,141112,083149,-nan,2A4C0000"
        sentence = _recompute(raw)
        msg = PNORH4.from_nmea(sentence)
        d = msg.to_dict()

        assert d["error_code"] is None

    def test_pnora_positional_nan_fields(self):
        """-nan in pressure/distance/pitch/roll → None."""
        raw = "$PNORA,230101,120000,-nan,-nan,1,00,-nan,-nan"
        sentence = _recompute(raw)
        msg = PNORA.from_nmea(sentence)
        d = msg.to_dict()

        assert d["pressure"] is None
        assert d["distance"] is None
        assert d["pitch"] is None
        assert d["roll"] is None

    def test_pnora_tagged_nan_fields(self):
        """-nan in tagged PNORA optional fields → None."""
        raw = "$PNORA,DATE=190902,TIME=122341,P=-nan,A=-nan,Q=1,ST=08,PI=-nan,R=-nan"
        sentence = _recompute(raw)
        msg = PNORA.from_nmea(sentence)
        d = msg.to_dict()

        assert d["pressure"] is None
        assert d["distance"] is None
        assert d["pitch"] is None
        assert d["roll"] is None


# ---------------------------------------------------------------------------
# Additional Checksum Integrity Tests for New Types
# ---------------------------------------------------------------------------


class TestChecksumIntegrityExtended:
    """Verify known-good checksums from spec documentation."""

    @pytest.mark.parametrize(
        "sentence",
        [
            ("$PNORH3,DATE=141112,TIME=081946,EC=0,SC=2A4C0000*5F"),
            "$PNORH4,141112,083149,0,2A4C0000*4A",
            ("$PNORC3,CP=4.5,SP=3.519,DIR=110.9,AC=6,AA=28*3B"),
            "$PNORC4,27.5,1.815,322.6,4,28*70",
            ("$PNORS3,BV=22.9,SS=1546.1,H=151.1,PI=-12.0,R=-5.2,P=705.669,T=24.96*73"),
        ],
    )
    def test_spec_checksum_validity(self, sentence: str):
        """Checksums from spec docs must validate."""
        from adcp_recorder.core.nmea import validate_checksum

        assert validate_checksum(sentence)
