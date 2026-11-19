"""Read-only checks for the supplied workbook loaded into an isolated PostgreSQL database."""
import os

import pytest
from sqlalchemy import create_engine, text


@pytest.mark.postgres
def test_imported_workbook_in_postgres():
    url = os.getenv("EASIGTAP_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Defina EASIGTAP_TEST_DATABASE_URL para o banco de teste")
    if not url.startswith("postgresql+"):
        pytest.fail("O teste exige uma URL SQLAlchemy de PostgreSQL")
    engine = create_engine(url)
    with engine.connect() as connection:
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "0002_cid_normalization_status"
        assert set(connection.execute(text("SELECT extname FROM pg_extension WHERE extname IN ('unaccent', 'pg_trgm')")).scalars()) == {"unaccent", "pg_trgm"}
        indexes = set(connection.execute(text("SELECT indexname FROM pg_indexes WHERE schemaname='public'")).scalars())
        assert {"ix_procedimentos_nome_search", "ix_cids_descricao_search"} <= indexes
        assert connection.execute(text("SELECT count(*) FROM procedimentos")).scalar_one() == 4984
        assert connection.execute(text("SELECT count(*) FROM cids")).scalar_one() == 7895
        assert dict(connection.execute(text("SELECT tipo, count(*) FROM procedimento_cid GROUP BY tipo")).all()) == {"principal": 71238, "secundario": 362}
        assert connection.execute(text("SELECT count(*) FROM procedimento_cid WHERE codigo_original IS NULL")).scalar_one() == 0
        assert connection.execute(text("SELECT count(*) FROM procedimento_cid pc LEFT JOIN procedimentos p ON p.id=pc.procedimento_id LEFT JOIN cids c ON c.id=pc.cid_id WHERE p.id IS NULL OR c.id IS NULL")).scalar_one() == 0
        assert connection.execute(text("SELECT count(*) FROM procedimentos WHERE sigtap_search(nome) LIKE '%femur%' ")).scalar_one() > 0
        assert connection.execute(text("SELECT status FROM competencias WHERE referencia='2026-06'")).scalar_one() == "importado_com_pendencias"
