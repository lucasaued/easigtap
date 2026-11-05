from pathlib import Path
import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from src.database.models import Base, Competencia, Opm, Procedimento, ProcedimentoCid, ProcedimentoOpm
from src.importers.persist import persist
from src.importers.sigtap_excel import inspect_workbook
from src.parsers.cids import parse_cids
from src.parsers.procedimentos import parse_procedimento


def test_procedure_parser():
    assert parse_procedimento("0408040122 - EPIFISIODESE - FÊMUR") == ("0408040122", "EPIFISIODESE - FÊMUR")
    assert parse_procedimento("  0101010010 -  NOME  ")[0] == "0101010010"
    with pytest.raises(ValueError):
        parse_procedimento("123 - INVÁLIDO")


def test_cid_parser():
    assert parse_cids("S720, S721, S720, S72.2")[0] == ["S720", "S721", "S72.2"]
    assert parse_cids(None) == ([], [])
    assert parse_cids("M, S720")[0] == ["S720"]
    assert parse_cids("M, S720")[1]


def test_real_workbook_and_idempotence():
    path = Path("data/raw/Sigtap - UGPIA.xlsx")
    if not path.exists():
        pytest.skip("Planilha real não disponível")
    inspected = inspect_workbook(path)
    assert inspected.rows == 4984
    assert len(inspected.records) == 4984
    assert sum(len(rec.cids["principal"]) for rec in inspected.records) == 71238
    assert sum(len(rec.cids["secundario"]) for rec in inspected.records) == 362
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        with session.begin():
            first = persist(session, inspected, "2026-06", "Teste da planilha")
        with session.begin():
            repeated = persist(session, inspected, "2026-06", "Teste da planilha")
        with session.begin():
            second = persist(session, inspected, "2026-07", "Teste de histórico")
        assert first["procedures"] == 4984
        assert repeated["status"] == "already_imported"
        assert second["procedures"] == 4984
        assert session.scalar(select(func.count()).select_from(Procedimento)) == 9968
        assert session.scalar(select(func.count()).select_from(Competencia)) == 2
        assert session.scalar(select(func.count()).select_from(ProcedimentoCid)) == first["cid_links"] * 2
        assert session.scalar(select(func.count()).select_from(ProcedimentoCid).where(ProcedimentoCid.tipo == "secundario")) == 724
        assert session.scalar(select(func.count()).select_from(Opm)) == 0
        assert session.scalar(select(func.count()).select_from(ProcedimentoOpm)) == 0
