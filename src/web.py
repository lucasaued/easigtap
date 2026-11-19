"""Local consultor for the supplied SIGTAP workbook."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from sqlalchemy import create_engine, func, or_, select
from sqlalchemy.orm import Session

from src.config import database_url
from src.database.models import Cid, Competencia, Opm, Procedimento, ProcedimentoCid, ProcedimentoOpm
from src.parsers.cids import canonical_cid


ROOT = Path(__file__).resolve().parent.parent / "web"
COMPETENCIA = "2026-06"


def active_competencia(session: Session) -> Competencia:
    value = session.scalar(select(Competencia).where(Competencia.referencia == COMPETENCIA))
    if value is None:
        raise RuntimeError("Importe a planilha da competência 2026-06 antes de abrir o aplicativo")
    return value


def procedure_json(row: Procedimento) -> dict:
    return {"codigo": row.codigo, "nome": row.nome, "descricao": row.descricao,
            "linha": row.linha_origem}


def search_procedures(session: Session, query: str, scope: str, limit: int = 60) -> list[dict]:
    comp = active_competencia(session)
    stmt = select(Procedimento).where(Procedimento.competencia_id == comp.id,
                                     ~Procedimento.codigo.startswith("07"))
    if scope == "ortopedia":
        stmt = stmt.where(Procedimento.codigo.startswith("0408"))
    if query:
        normalized = query.strip().lower()
        stmt = stmt.where(or_(Procedimento.codigo.contains(normalized.replace(".", "")),
                              func.sigtap_search(Procedimento.nome).contains(func.sigtap_search(normalized)),
                              func.sigtap_search(Procedimento.descricao).contains(func.sigtap_search(normalized))))
    return [procedure_json(row) for row in session.scalars(stmt.order_by(Procedimento.codigo).limit(limit))]


def search_cids(session: Session, query: str, scope: str, limit: int = 60) -> list[dict]:
    comp = active_competencia(session)
    normalized = canonical_cid(query.strip())
    if not query.strip():
        return []
    stmt = (select(Cid.codigo, Cid.descricao, func.count(func.distinct(Procedimento.id)))
            .join(ProcedimentoCid, ProcedimentoCid.cid_id == Cid.id)
            .join(Procedimento, Procedimento.id == ProcedimentoCid.procedimento_id)
            .where(Procedimento.competencia_id == comp.id,
                   or_(Cid.codigo.startswith(normalized),
                       func.sigtap_search(Cid.descricao).contains(func.sigtap_search(query.strip()))),
                   ~Procedimento.codigo.startswith("07")))
    if scope == "ortopedia":
        stmt = stmt.where(Procedimento.codigo.startswith("0408"))
    return [{"codigo": code, "descricao": description, "procedimentos": count}
            for code, description, count in session.execute(
                stmt.group_by(Cid.codigo, Cid.descricao).order_by(Cid.codigo).limit(limit))]


def search_items(session: Session, query: str, procedure_code: str, cid_code: str,
                 limit: int = 60) -> list[dict]:
    comp = active_competencia(session)
    normalized_cid = canonical_cid(cid_code)
    if not procedure_code or not normalized_cid:
        raise ValueError("Selecione um procedimento e um CID antes de buscar itens OPM")
    relation = session.scalar(select(ProcedimentoCid.procedimento_id)
                              .join(Procedimento, Procedimento.id == ProcedimentoCid.procedimento_id)
                              .join(Cid, Cid.id == ProcedimentoCid.cid_id)
                              .where(Procedimento.competencia_id == comp.id,
                                     Procedimento.codigo == procedure_code,
                                     Cid.codigo == normalized_cid).limit(1))
    if relation is None:
        raise ValueError("O CID selecionado não está relacionado ao procedimento")
    stmt = (select(Opm, ProcedimentoOpm.limite_quantidade)
            .join(ProcedimentoOpm, ProcedimentoOpm.opm_id == Opm.id)
            .join(Procedimento, Procedimento.id == ProcedimentoOpm.procedimento_id)
            .where(Procedimento.competencia_id == comp.id,
                   Procedimento.codigo == procedure_code,
                   ProcedimentoOpm.competencia_id == comp.id,
                   ProcedimentoOpm.tipo == "compativel"))
    if query:
        normalized = query.strip().lower()
        stmt = stmt.where(or_(Opm.codigo.contains(normalized.replace(".", "")),
                              func.sigtap_search(Opm.nome).contains(func.sigtap_search(normalized))))
    return [{"codigo": opm.codigo, "nome": opm.nome, "descricao": opm.descricao,
             "qtd_maxima_item": amount, "origem_relacao": "SIGTAP 2026-06"}
            for opm, amount in session.execute(stmt.order_by(Opm.codigo).limit(limit))]


def procedure_detail(session: Session, code: str) -> dict | None:
    comp = active_competencia(session)
    row = session.scalar(select(Procedimento).where(Procedimento.competencia_id == comp.id,
                                                  Procedimento.codigo == code,
                                                  ~Procedimento.codigo.startswith("07")))
    if row is None:
        return None
    cids = session.execute(select(Cid.codigo, Cid.descricao, Cid.fonte_descricao,
                                  ProcedimentoCid.tipo, ProcedimentoCid.codigo_original)
                           .join(ProcedimentoCid, ProcedimentoCid.cid_id == Cid.id)
                           .where(ProcedimentoCid.procedimento_id == row.id)
                           .order_by(ProcedimentoCid.tipo, Cid.codigo)).all()
    return {**procedure_json(row), "cids": [{"codigo": code, "descricao": description,
                                               "fonte_descricao": source, "tipo": kind,
                                               "grafia_original": original}
                                              for code, description, source, kind, original in cids],
            "competencia": comp.referencia, "status_dados": comp.status,
            "origem": comp.origem.get("descricao"), "atributos": row.atributos}


def procedures_for_cid(session: Session, code: str, scope: str, limit: int = 60) -> list[dict]:
    comp = active_competencia(session)
    normalized = canonical_cid(code)
    stmt = (select(Procedimento, ProcedimentoCid.tipo)
            .join(ProcedimentoCid, ProcedimentoCid.procedimento_id == Procedimento.id)
            .join(Cid, Cid.id == ProcedimentoCid.cid_id)
            .where(Procedimento.competencia_id == comp.id, Cid.codigo == normalized,
                   ~Procedimento.codigo.startswith("07")))
    if scope == "ortopedia":
        stmt = stmt.where(Procedimento.codigo.startswith("0408"))
    return [{**procedure_json(row), "tipo_cid": kind} for row, kind in session.execute(
        stmt.order_by(Procedimento.codigo).limit(limit))]


class Handler(BaseHTTPRequestHandler):
    engine = None

    def respond(self, status: int, body: bytes, content_type: str):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = {key: value[0] for key, value in parse_qs(parsed.query).items()}
        if path.startswith("/api/"):
            try:
                with Session(self.engine) as session:
                    query = params.get("q", "").strip()[:120]
                    scope = params.get("scope", "ortopedia")
                    if scope not in {"ortopedia", "todos"}:
                        raise ValueError("Escopo inválido")
                    if path == "/api/procedimentos":
                        result = search_procedures(session, query, scope)
                    elif path == "/api/cids":
                        result = search_cids(session, query, scope)
                    elif path == "/api/itens":
                        result = search_items(session, query, params.get("procedimento", ""),
                                              params.get("cid", ""))
                    elif path.startswith("/api/procedimentos/"):
                        result = procedure_detail(session, path.rsplit("/", 1)[-1])
                        if result is None:
                            self.respond(404, '{"erro":"Procedimento não encontrado"}'.encode("utf-8"), "application/json; charset=utf-8")
                            return
                    elif path.startswith("/api/cids/") and path.endswith("/procedimentos"):
                        result = procedures_for_cid(session, path.split("/")[3], scope)
                    else:
                        self.respond(404, '{"erro":"Rota não encontrada"}'.encode("utf-8"), "application/json; charset=utf-8")
                        return
                self.respond(200, json.dumps(result, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")
            except ValueError as exc:
                self.respond(400, json.dumps({"erro": str(exc)}, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")
            except Exception as exc:
                self.log_error("API: %s", exc)
                self.respond(500, b'{"erro":"Erro ao consultar os dados"}', "application/json; charset=utf-8")
            return
        files = {"/": ("index.html", "text/html"), "/app.js": ("app.js", "text/javascript"),
                 "/style.css": ("style.css", "text/css")}
        if path not in files:
            self.respond(404, b"Not found", "text/plain")
            return
        filename, mime = files[path]
        self.respond(200, (ROOT / filename).read_bytes(), f"{mime}; charset=utf-8")


def main():
    parser = argparse.ArgumentParser(description="Consultor local eaSIGTAP")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    Handler.engine = create_engine(database_url(), pool_pre_ping=True)
    with Session(Handler.engine) as session:
        active_competencia(session)
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"eaSIGTAP em http://{args.host}:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
