"""Tests for ORM models."""


import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from adcp_recorder.db.models import (
    ParseError,
    PnoraData,
    PnorbData,
    Pnorc12,
    Pnorc34,
    PnorcDf100,
    PnoreData,
    PnorfData,
    Pnorh,
    Pnori,
    Pnori12,
    Pnors12,
    Pnors34,
    PnorsDf100,
    PnorwData,
    PnorwdData,
    RawLine,
)


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("duckdb:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_raw_line_roundtrip(session: Session):
    raw = RawLine(
        raw_sentence="$PNORI,4,Test*2E", parse_status="OK", record_type="PNORI", checksum_valid=True
    )
    session.add(raw)
    session.commit()
    session.refresh(raw)

    assert raw.line_id is not None
    assert raw.parse_status == "OK"

    statement = select(RawLine).where(RawLine.line_id == raw.line_id)
    results = session.exec(statement)
    db_raw = results.one()
    assert db_raw.raw_sentence == "$PNORI,4,Test*2E"


def test_parse_error_roundtrip(session: Session):
    error = ParseError(
        raw_sentence="$PNORI,4*FF",
        error_type="CHECKSUM_FAILED",
        error_message="Invalid checksum",
        attempted_prefix="PNORI",
        checksum_expected="2E",
        checksum_actual="FF",
    )
    session.add(error)
    session.commit()
    session.refresh(error)
    assert error.error_id is not None
    assert error.error_type == "CHECKSUM_FAILED"


def test_pnori_roundtrip(session: Session):
    config = Pnori(
        original_sentence="$PNORI,4,Test*2E",
        instrument_type_name="Test",
        instrument_type_code=4,
        head_id="TEST-001",
        beam_count=4,
        cell_count=100,
        blanking_distance=0.5,
        cell_size=1.0,
        coord_system_name="ENU",
        coord_system_code=0,
        checksum="2E",
    )
    session.add(config)
    session.commit()
    session.refresh(config)
    assert config.config_id is not None
    assert config.head_id == "TEST-001"


def test_pnori12_roundtrip(session: Session):
    config = Pnori12(
        data_format=101,
        original_sentence="$PNORI1,4,Test*2E",
        instrument_type_name="Test",
        instrument_type_code=4,
        head_id="TEST-001",
        beam_count=4,
        cell_count=100,
        blanking_distance=0.5,
        cell_size=1.0,
        coord_system_name="ENU",
        coord_system_code=0,
        checksum="2E",
    )
    session.add(config)
    session.commit()
    session.refresh(config)
    assert config.data_format == 101


def test_pnors_df100_roundtrip(session: Session):
    data = PnorsDf100(
        original_sentence="$PNORS,...",
        measurement_date="190126",
        measurement_time="234500",
        battery=12.5,
        temperature=15.2,
    )
    session.add(data)
    session.commit()
    session.refresh(data)
    assert data.record_id is not None
    assert data.battery == 12.5


def test_pnors12_roundtrip(session: Session):
    data = Pnors12(
        data_format=101,
        original_sentence="$PNORS1,...",
        measurement_date="190126",
        measurement_time="234500",
        battery=12.5,
        heading=180.0,
    )
    session.add(data)
    session.commit()
    session.refresh(data)
    assert data.record_id is not None


def test_pnors34_roundtrip(session: Session):
    data = Pnors34(
        data_format=103,
        original_sentence="$PNORS3,...",
        measurement_date="190126",
        measurement_time="234500",
        battery=12.5,
    )
    session.add(data)
    session.commit()
    session.refresh(data)
    assert data.record_id is not None


def test_pnorc_df100_roundtrip(session: Session):
    data = PnorcDf100(
        original_sentence="$PNORC,...",
        measurement_date="190126",
        measurement_time="234500",
        cell_index=1,
        speed=1.5,
    )
    session.add(data)
    session.commit()
    session.refresh(data)
    assert data.cell_index == 1


def test_pnorc12_roundtrip(session: Session):
    data = Pnorc12(
        data_format=101,
        original_sentence="$PNORC1,...",
        measurement_date="190126",
        measurement_time="234500",
        cell_index=1,
        vel1=0.5,
    )
    session.add(data)
    session.commit()
    session.refresh(data)
    assert data.vel1 == 0.5


def test_pnorc34_roundtrip(session: Session):
    data = Pnorc34(
        data_format=103,
        original_sentence="$PNORC3,...",
        measurement_date="190126",
        measurement_time="234500",
        cell_index=1,
        speed=1.2,
    )
    session.add(data)
    session.commit()
    session.refresh(data)
    assert data.speed == pytest.approx(1.2)


def test_pnorh_roundtrip(session: Session):
    data = Pnorh(
        data_format=103,
        original_sentence="$PNORH3,...",
        measurement_date="190126",
        measurement_time="234500",
        status_code="00000000",
    )
    session.add(data)
    session.commit()
    session.refresh(data)
    assert data.status_code == "00000000"


def test_pnore_data_roundtrip(session: Session):
    data = PnoreData(
        sentence_type="PNORE",
        original_sentence="$PNORE,...",
        measurement_date="190126",
        measurement_time="234500",
        spectrum_basis=1,
        num_frequencies=10,
        energy_densities=[1.0, 2.0, 3.0],
    )
    session.add(data)
    session.commit()
    session.refresh(data)
    assert data.energy_densities == [1.0, 2.0, 3.0]


def test_pnorw_data_roundtrip(session: Session):
    data = PnorwData(
        sentence_type="PNORW",
        original_sentence="$PNORW,...",
        measurement_date="190126",
        measurement_time="234500",
        hm0=1.5,
    )
    session.add(data)
    session.commit()
    session.refresh(data)
    assert data.hm0 == 1.5


def test_pnorb_data_roundtrip(session: Session):
    data = PnorbData(
        sentence_type="PNORB",
        original_sentence="$PNORB,...",
        measurement_date="190126",
        measurement_time="234500",
        spectrum_basis=1,
        processing_method=1,
        hmo=1.2,
    )
    session.add(data)
    session.commit()
    session.refresh(data)
    assert data.hmo == pytest.approx(1.2)


def test_pnorf_data_roundtrip(session: Session):
    data = PnorfData(
        sentence_type="PNORF",
        original_sentence="$PNORF,...",
        measurement_date="190126",
        measurement_time="234500",
        coefficient_flag="A1",
        spectrum_basis=1,
        num_frequencies=5,
        coefficients=[0.1, 0.2, 0.3],
    )
    session.add(data)
    session.commit()
    session.refresh(data)
    assert data.coefficients == [0.1, 0.2, 0.3]


def test_pnorwd_data_roundtrip(session: Session):
    data = PnorwdData(
        sentence_type="PNORWD",
        original_sentence="$PNORWD,...",
        measurement_date="190126",
        measurement_time="234500",
        direction_type="MD",
        spectrum_basis=1,
        num_frequencies=5,
        values=[10.0, 20.0, 30.0],
    )
    session.add(data)
    session.commit()
    session.refresh(data)
    assert data.values == [10.0, 20.0, 30.0]


def test_pnora_data_roundtrip(session: Session):
    data = PnoraData(
        sentence_type="PNORA",
        original_sentence="$PNORA,...",
        measurement_date="190126",
        measurement_time="234500",
        altimeter_distance=10.5,
    )
    session.add(data)
    session.commit()
    session.refresh(data)
    assert data.altimeter_distance == 10.5
