"""Import CID names and orthopedic procedure–OPM links from the official SIGTAP ZIP."""
import hashlib
import zipfile
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models import Cid, Competencia, Opm, Procedimento, ProcedimentoOpm


SOURCE_URL = "ftp://ftp2.datasus.gov.br/pub/sistemas/tup/downloads/TabelaUnificada_202606_v2610231231.zip"
EXPECTED_SHA256 = "aae352162a1989c6fbfdb95784ba7f0bd9b664eecaa08efee3e7392dc3a6bd51"
EXPECTED_LAYOUTS = {
    "tb_cid_layout.txt": "CO_CID,4,1,4,VARCHAR2\r\nNO_CID,100,5,104,VARCHAR2",
    "rl_procedimento_compativel_layout.txt": "CO_PROCEDIMENTO_PRINCIPAL,10,1,10,VARCHAR2\r\nCO_REGISTRO_PRINCIPAL,2,11,12,VARCHAR2\r\nCO_PROCEDIMENTO_COMPATIVEL,10,13,22,VARCHAR2",
}


def read_official(archive: Path) -> tuple[dict[str, str], list[tuple[str, str, str, int, str, str]]]:
    with zipfile.ZipFile(archive) as package:
        for name, fragment in EXPECTED_LAYOUTS.items():
            if fragment not in package.read(name).decode("ascii"):
                raise ValueError(f"Layout oficial inesperado: {name}")
        cids: dict[str, str] = {}
        for line in package.read("tb_cid.txt").decode("latin-1").splitlines():
            if len(line) < 104:
                raise ValueError("Linha CID incompleta no arquivo oficial")
            code, name = line[:4].strip(), line[4:104].strip()
            if code and name:
                if code in cids and cids[code] != name:
                    raise ValueError(f"CID oficial duplicado: {code}")
                cids[code] = name
        links = []
        for line in package.read("rl_procedimento_compativel.txt").decode("latin-1").splitlines():
            if len(line) < 35:
                raise ValueError("Linha de compatibilidade incompleta no arquivo oficial")
            procedure, registration, opm, opm_registration = line[:10], line[10:12], line[12:22], line[22:24]
            kind, amount, competence = line[24], line[25:29], line[29:35]
            if procedure.startswith("0408") and opm.startswith("07") and kind == "1":
                if not amount.isdigit() or competence != "202606":
                    raise ValueError("Quantidade ou competência inesperada na compatibilidade")
                links.append((procedure, opm, kind, int(amount), registration, opm_registration))
    if not cids or not links:
        raise ValueError("Arquivo SIGTAP sem CIDs ou compatibilidades ortopédicas")
    return cids, links


def import_official(session: Session, archive: Path) -> dict:
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError("SHA-256 do pacote SIGTAP diferente do arquivo oficial conferido")
    cids, links = read_official(archive)
    source = f"SIGTAP DATASUS 2026-06; {SOURCE_URL}; SHA-256 {digest}"
    comp = session.scalar(select(Competencia).where(Competencia.referencia == "2026-06"))
    if comp is None:
        raise ValueError("Importe a planilha da competência 2026-06 primeiro")
    updated = 0
    missing = []
    for cid in session.scalars(select(Cid)):
        description = cids.get(cid.codigo)
        if description is None:
            missing.append(cid.codigo)
        elif cid.descricao != description or cid.fonte_descricao != source:
            cid.descricao = description
            cid.fonte_descricao = source
            updated += 1
    procedures = {row.codigo: row for row in session.scalars(
        select(Procedimento).where(Procedimento.competencia_id == comp.id))}
    existing_opms = {row.codigo: row for row in session.scalars(
        select(Opm).where(Opm.competencia_id == comp.id))}
    existing_links = {(row.procedimento_id, row.opm_id, row.tipo, row.fonte)
                      for row in session.scalars(select(ProcedimentoOpm).where(
                          ProcedimentoOpm.competencia_id == comp.id))}
    added = 0
    missing_pairs = []
    for procedure_code, opm_code, kind, amount, registration, opm_registration in links:
        procedure, item = procedures.get(procedure_code), procedures.get(opm_code)
        if procedure is None or item is None:
            missing_pairs.append([procedure_code, opm_code])
            continue
        opm = existing_opms.get(opm_code)
        if opm is None:
            opm = Opm(competencia_id=comp.id, codigo=opm_code, nome=item.nome,
                      descricao=item.descricao)
            session.add(opm)
            session.flush()
            existing_opms[opm_code] = opm
        key = (procedure.id, opm.id, "compativel", source)
        if key not in existing_links:
            session.add(ProcedimentoOpm(procedimento_id=procedure.id, opm_id=opm.id,
                                       competencia_id=comp.id, tipo="compativel",
                                       limite_quantidade=amount,
                                       regras={"tipo_original": kind, "registro_principal": registration,
                                               "registro_opm": opm_registration}, fonte=source))
            existing_links.add(key)
            added += 1
    return {"source": SOURCE_URL, "sha256": digest, "cids_updated": updated,
            "cids_unmatched": missing, "opms": len(existing_opms),
            "compatibilities_added": added, "compatibilities_unmatched": missing_pairs}
