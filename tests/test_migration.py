"""Exercise the data-preserving part of revision 0002 on an existing database."""
import importlib.util
from pathlib import Path

from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, text

from src.database.models import Base


def test_existing_cid_variants_are_merged():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE procedimento_cid DROP COLUMN codigo_original"))
        connection.execute(text("INSERT INTO competencias (id, referencia, arquivo, sha256, importado_em, status, origem) VALUES (1, '2026-06', 'a.xlsx', 'abc', CURRENT_TIMESTAMP, 'validado', '{}')"))
        connection.execute(text("INSERT INTO procedimentos (id, competencia_id, codigo, nome, identificacao_original, atributos, linha_origem) VALUES (1, 1, '0408040122', 'Teste', '0408040122 - Teste', '{}', 2)"))
        connection.execute(text("INSERT INTO cids (id, codigo) VALUES (1, 'S72.0'), (2, 'S720')"))
        connection.execute(text("INSERT INTO procedimento_cid (procedimento_id, cid_id, tipo, competencia_id) VALUES (1, 1, 'principal', 1), (1, 2, 'principal', 1), (1, 2, 'secundario', 1)"))
        spec = importlib.util.spec_from_file_location("migration_0002", Path("alembic/versions/0002_cid_normalization_status.py"))
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        assert connection.execute(text("SELECT codigo FROM cids")).scalars().all() == ["S720"]
        assert connection.execute(text("SELECT tipo, codigo_original FROM procedimento_cid ORDER BY tipo")).all() == [
            ("principal", "S720"), ("secundario", "S720")]
        assert connection.execute(text("SELECT status FROM competencias")).scalar_one() == "validado_tecnicamente"
