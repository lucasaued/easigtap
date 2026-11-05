from sqlalchemy import select
from sqlalchemy.orm import Session
from src.database.models import Cid, Competencia, Procedimento, ProcedimentoCid
from src.importers.sigtap_excel import Inspection


def persist(session: Session, inspection: Inspection, referencia: str, origem: str) -> dict:
    """Caller owns the transaction; an exception leaves all changes uncommitted."""
    existing = session.scalar(select(Competencia).where(Competencia.referencia == referencia,
                                                        Competencia.sha256 == inspection.sha256))
    if existing:
        return {"status": "already_imported", "competencia_id": existing.id, "procedures": 0, "cid_links": 0}
    if session.scalar(select(Competencia.id).where(Competencia.referencia == referencia)) is not None:
        raise ValueError("Competência já importada com outro arquivo; nenhuma alteração realizada")
    competencia = Competencia(referencia=referencia, arquivo=inspection.path,
                              sha256=inspection.sha256, status="parcial" if inspection.errors else "validado",
                              origem={"descricao": origem, "aba": inspection.sheet})
    session.add(competencia)
    session.flush()
    codes = {code for rec in inspection.records for values in rec.cids.values() for code in values}
    cids = {cid.codigo: cid for cid in session.scalars(select(Cid).where(Cid.codigo.in_(codes)))} if codes else {}
    for code in codes - cids.keys():
        cid = Cid(codigo=code)
        session.add(cid)
        cids[code] = cid
    session.flush()
    link_count = 0
    for rec in inspection.records:
        procedure = Procedimento(competencia_id=competencia.id, codigo=rec.code, nome=rec.name,
                                descricao=rec.description, identificacao_original=rec.original,
                                atributos=rec.attributes, linha_origem=rec.line)
        session.add(procedure)
        session.flush()
        for kind, values in rec.cids.items():
            for code in values:
                session.add(ProcedimentoCid(procedimento_id=procedure.id, cid_id=cids[code].id,
                                           tipo=kind, competencia_id=competencia.id))
                link_count += 1
    return {"status": competencia.status, "competencia_id": competencia.id,
            "procedures": len(inspection.records), "cid_links": link_count}
