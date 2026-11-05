"""Initial SIGTAP data schema and accent insensitive search."""
from alembic import op
from src.database.models import Base

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    Base.metadata.create_all(bind)
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE FUNCTION sigtap_search(text) RETURNS text LANGUAGE sql IMMUTABLE PARALLEL SAFE AS $$ SELECT lower(public.unaccent('public.unaccent'::regdictionary, $1)) $$")
    op.execute("CREATE INDEX ix_procedimentos_nome_search ON procedimentos USING gin (sigtap_search(nome) gin_trgm_ops)")
    op.execute("CREATE INDEX ix_cids_descricao_search ON cids USING gin (sigtap_search(descricao) gin_trgm_ops)")


def downgrade():
    op.execute("DROP INDEX ix_cids_descricao_search")
    op.execute("DROP INDEX ix_procedimentos_nome_search")
    op.execute("DROP FUNCTION sigtap_search(text)")
    Base.metadata.drop_all(op.get_bind())
