import pytest

from adcp_recorder.parsers.pnora import PNORA
from adcp_recorder.parsers.pnorb import PNORB
from adcp_recorder.parsers.pnorc import PNORC
from adcp_recorder.parsers.pnore import PNORE
from adcp_recorder.parsers.pnorf import PNORF
from adcp_recorder.parsers.pnorh import PNORH3
from adcp_recorder.parsers.pnori import PNORI
from adcp_recorder.parsers.pnors import PNORS
from adcp_recorder.parsers.pnorw import PNORW
from adcp_recorder.parsers.pnorwd import PNORWD
from adcp_recorder.parsers.utils import parse_optional_float, validate_range


def test_utils_nan_handling():
    # Test parse_optional_float
    assert parse_optional_float("nan") is None
    assert parse_optional_float("NaN") is None
    assert parse_optional_float("NAN") is None
    assert parse_optional_float("") is None
    assert parse_optional_float("-9.0000") is None
    assert parse_optional_float("1.23") == 1.23

    # Test validate_range with NaN (should raise ValueError)
    with pytest.raises(ValueError, match="out of range"):
        validate_range(float("nan"), "test_field", 0, 10)


def test_pnora_nan():
    # Positional NaN (DF=200)
    # Format: $PNORA,Date,Time,Pres,Dist,Qual,Status,Pitch,Roll*CS
    sentence = "$PNORA,151021,090715,nan,nan,1,00,nan,nan*7F"
    msg = PNORA.from_nmea(sentence)
    assert msg.pressure is None
    assert msg.distance is None
    assert msg.pitch is None
    assert msg.roll is None

    # Tagged NaN (DF=201)
    # Format: $PNORA,DATE=MMDDYY,TIME=HHMMSS,DF=201,P=nan,A=nan,Q=1,ST=00,PI=nan,R=nan*CS
    sentence = "$PNORA,DATE=151021,TIME=090715,DF=201,P=nan,A=nan,Q=1,ST=00,PI=nan,R=nan*52"
    msg = PNORA.from_nmea(sentence)
    assert msg.pressure is None
    assert msg.distance is None
    assert msg.status == "00"
    assert msg.pitch is None
    assert msg.roll is None


def test_pnorb_nan():
    # Format: $PNORB,Date,Time,Basis,Method,FreqLow,FreqHigh,Hm0,Tm02,Tp,
    #         DirTp,SprTp,MainDir,ErrorCode*CS
    sentence = "$PNORB,102115,090715,1,1,0.01,0.1,nan,nan,nan,nan,nan,nan,0000*51"
    msg = PNORB.from_nmea(sentence)
    assert msg.hm0 is None
    assert msg.tm02 is None


def test_pnorc_nan():
    # PNORC Positional (DF=100)
    # Format: $PNORC,MMDDYY,HHMMSS,Cell,Vel1,Vel2,Vel3,Vel4,Speed,Dir,
    #         AmpUnit,Amp1,Amp2,Amp3,Amp4,Corr1,Corr2,Corr3,Corr4*CS
    # Total 19 fields
    sentence = "$PNORC,102115,090715,1,nan,nan,nan,nan,nan,nan,C,nan,nan,nan,nan,nan,nan,nan,nan*3E"
    msg = PNORC.from_nmea(sentence)
    assert msg.vel1 is None
    assert msg.speed is None
    assert msg.amp1 is None
    assert msg.corr1 is None


def test_pnorw_nan():
    # PNORW Positional
    # Format: $PNORW,Date,Time,Basis,Method,Hm0,H3,H10,Hmax,Tm02,Tp,Tz,DirTp,SprTp,MainDir,
    #         UI,MeanPress,NoDetect,BadDetect,NSurfSpeed,NSurfDir,ErrorCode*CS (22 fields)
    sentence = (
        "$PNORW,102115,090715,1,1,nan,nan,nan,nan,nan,nan,nan,nan,nan,nan,"
        "nan,nan,nan,nan,nan,nan,0000*74"
    )
    msg = PNORW.from_nmea(sentence)
    assert msg.hm0 is None
    assert msg.tm02 is None


def test_pnorwd_nan():
    # PNORWD Positional
    # Format: $PNORWD,DirType,Date,Time,Basis,Start,Step,Num,V1,V2,...,VN*CS
    sentence = "$PNORWD,MD,102115,090715,nan,nan,nan,2,0.1,0.2*69"
    msg = PNORWD.from_nmea(sentence)
    assert msg.spectrum_basis is None
    assert msg.num_frequencies == 2
    assert msg.values[0] == 0.1


def test_pnori_nan():
    # PNORI Positional
    # Format: $PNORI,InstrType,HeadID,BeamCnt,CellCnt,BlankDist,CellSize,CoordSys*CS
    sentence = "$PNORI,4,HEAD1,nan,nan,nan,nan,0*5B"
    msg = PNORI.from_nmea(sentence)
    assert msg.beam_count is None
    assert msg.cell_count is None
    assert msg.blanking_distance is None
    assert msg.cell_size is None


def test_pnors_nan():
    # PNORS Positional
    # Format: $PNORS,MMDDYY,HHMMSS,Error,Status,Battery,SoundSpeed,Heading,Pitch,Roll,
    #         Pressure,Temperature,Analog1,Analog2*CS
    sentence = "$PNORS,102115,090715,0000,00000000,nan,nan,nan,nan,nan,nan,nan,nan,nan*11"
    msg = PNORS.from_nmea(sentence)
    assert msg.battery is None
    assert msg.sound_speed is None


def test_pnorh_nan():
    # PNORH3 Tagged
    sentence = "$PNORH3,DATE=151021,TIME=090715,EC=nan,SC=00000000*02"
    msg = PNORH3.from_nmea(sentence)
    assert msg.error_code is None


def test_pnore_nan():
    # PNORE Positional
    # Format: $PNORE,Date,Time,Basis,Start,Step,Num,E1,E2,...,EN*CS
    sentence = "$PNORE,211015,090715,nan,nan,nan,2,0.1,0.2"
    msg = PNORE.from_nmea(sentence)
    assert msg.spectrum_basis is None
    assert msg.energy_densities[0] == 0.1


def test_pnorf_nan():
    # PNORF Positional
    # Format: $PNORF,Flag,Date,Time,Basis,Start,Step,Num,C1,C2,...,CN*CS
    sentence = "$PNORF,A1,102115,090715,nan,nan,nan,2,0.1,0.2*45"
    msg = PNORF.from_nmea(sentence)
    assert msg.coefficient_flag == "A1"
    assert msg.spectrum_basis is None
    assert msg.coefficients[0] == 0.1
