from pathlib import Path

import pytest
from openpyxl import Workbook
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from src.database.models import Base, Cid, Competencia, Procedimento, ProcedimentoCid
from src.importers.persist import persist
from src.importers.sigtap_excel import inspect_workbook


HEADERS = ["Procedimento", "Descrição", "CID", "CID Secundário", "Qtd Máxima"]


def workbook(tmp_path: Path, rows: list[list], headers=HEADERS) -> Path:
    book = Workbook()
    sheet = book.active
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    path = tmp_path / "input.xlsx"
    book.save(path)
    return path


def test_bad_workbooks(tmp_path):
    invalid = tmp_path / "invalid.xlsx"
    invalid.write_text("invalid", encoding="utf-8")
    with pytest.raises(ValueError, match="XLSX inválido"):
        inspect_workbook(invalid)
    with pytest.raises(ValueError, match="Colunas essenciais ausentes"):
        inspect_workbook(workbook(tmp_path, [], headers=["Procedimento"]))
    with pytest.raises(ValueError, match="Cabeçalhos duplicados"):
        inspect_workbook(workbook(tmp_path, [], headers=HEADERS + ["CID"]))


def test_duplicate_procedures_and_cid_origins(tmp_path):
    path = workbook(tmp_path, [
        ["0408040122 - FÊMUR", "Descrição", "S72.0, S720, M", "S72.0", 1],
        ["0408040122 - FÊMUR REPETIDO", None, "S720", None, 1],
        ["123 - INVÁLIDO", None, None, None, 1],
    ])
    inspected = inspect_workbook(path)
    assert inspected.rows == 3
    assert len(inspected.records) == 1
    assert inspected.records[0].cids == {"principal": ["S720"], "secundario": ["S720"]}
    assert inspected.records[0].cid_origins["principal"] == {"S720": "S72.0"}
    assert len(inspected.errors) == 3

    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        with session.begin():
            persist(session, inspected, "2026-06", "Operador")
        assert session.scalar(select(func.count()).select_from(Cid)) == 1
        assert session.scalars(select(ProcedimentoCid.codigo_original).order_by(ProcedimentoCid.tipo)).all() == ["S72.0", "S72.0"]
        assert session.scalar(select(Competencia.status)) == "importado_com_pendencias"
        assert session.scalar(select(Competencia.origem))["validacao_oficial"] is False


def test_transaction_rollback_and_conflicting_file(tmp_path):
    path = workbook(tmp_path, [["0408040122 - FÊMUR", None, "S720", None, 1]])
    inspected = inspect_workbook(path)
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        with pytest.raises(RuntimeError):
            with session.begin():
                persist(session, inspected, "2026-06", "Operador")
                raise RuntimeError("falha simulada")
        assert session.scalar(select(func.count()).select_from(Competencia)) == 0
        assert session.scalar(select(func.count()).select_from(Procedimento)) == 0
        session.rollback()
        with session.begin():
            persist(session, inspected, "2026-06", "Operador")
        with session.begin():
            assert persist(session, inspected, "2026-06", "Operador")["status"] == "already_imported"
        other = workbook(tmp_path, [["0408040122 - FÊMUR MODIFICADO", None, "S720", None, 1]])
        with pytest.raises(ValueError, match="já importada"):
            with session.begin():
                persist(session, inspect_workbook(other), "2026-06", "Operador")
        assert session.scalar(select(func.count()).select_from(Competencia)) == 1
