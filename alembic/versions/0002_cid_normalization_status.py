"""Preserve original CID notation and distinguish technical from official validation."""

from alembic import op
import sqlalchemy as sa

revision = "0002_cid_normalization_status"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"]: column for column in inspector.get_columns("procedimento_cid")}
    if "codigo_original" not in columns:
        op.add_column("procedimento_cid", sa.Column("codigo_original", sa.String(12), nullable=True))
    status_column = next(column for column in inspector.get_columns("competencias") if column["name"] == "status")
    if status_column["type"].length is not None and status_column["type"].length < 40:
        with op.batch_alter_table("competencias") as batch:
            batch.alter_column("status", existing_type=status_column["type"], type_=sa.String(40), existing_nullable=False)

    bind.execute(sa.text("UPDATE competencias SET status = 'validado_tecnicamente' WHERE status = 'validado'"))
    bind.execute(sa.text("UPDATE competencias SET status = 'importado_com_pendencias' WHERE status = 'parcial'"))
    bind.execute(sa.text("""
        UPDATE procedimento_cid SET codigo_original = (
            SELECT codigo FROM cids WHERE cids.id = procedimento_cid.cid_id
        ) WHERE codigo_original IS NULL
    """))

    rows = bind.execute(sa.text("SELECT id, codigo FROM cids ORDER BY id")).all()
    groups = {}
    for cid_id, code in rows:
        groups.setdefault(code.upper().replace(".", ""), []).append((cid_id, code))
    for canonical, variants in groups.items():
        target_id, _ = next(((cid_id, code) for cid_id, code in variants if code == canonical), variants[0])
        for source_id, _ in variants:
            if source_id == target_id:
                continue
            links = bind.execute(sa.text("""
                SELECT procedimento_id, tipo FROM procedimento_cid WHERE cid_id = :source_id
            """), {"source_id": source_id}).all()
            for procedure_id, kind in links:
                params = {"procedure_id": procedure_id, "kind": kind,
                          "source_id": source_id, "target_id": target_id}
                duplicate = bind.execute(sa.text("""
                    SELECT 1 FROM procedimento_cid
                    WHERE procedimento_id = :procedure_id AND tipo = :kind AND cid_id = :target_id
                """), params).first()
                if duplicate:
                    bind.execute(sa.text("""
                        DELETE FROM procedimento_cid
                        WHERE procedimento_id = :procedure_id AND tipo = :kind AND cid_id = :source_id
                    """), params)
                else:
                    bind.execute(sa.text("""
                        UPDATE procedimento_cid SET cid_id = :target_id
                        WHERE procedimento_id = :procedure_id AND tipo = :kind AND cid_id = :source_id
                    """), params)
            bind.execute(sa.text("DELETE FROM cids WHERE id = :id"), {"id": source_id})
        bind.execute(sa.text("UPDATE cids SET codigo = :code WHERE id = :id"),
                     {"code": canonical, "id": target_id})


def downgrade():
    raise RuntimeError("Esta migração preserva a grafia original dos CIDs, mas a fusão de variantes não pode ser desfeita sem ambiguidade")
