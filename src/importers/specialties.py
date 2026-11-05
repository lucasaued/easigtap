import csv
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.database.models import Competencia, Especialidade, EspecialidadeProcedimento, Procedimento

VALID_NAMES = {"Traumatologia", "Ortopedia"}


def import_specialties(session: Session, path: Path) -> int:
    """Import only explicitly reviewed classifications from a CSV file."""
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        required = {"competencia", "codigo_procedimento", "especialidade", "fonte_validacao"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Cabeçalhos inválidos no CSV de especialidades")
        count = 0
        for line, row in enumerate(reader, start=2):
            ref, code, name, source = (row[key].strip() for key in
                                       ("competencia", "codigo_procedimento", "especialidade", "fonte_validacao"))
            if name not in VALID_NAMES or not source:
                raise ValueError(f"Linha {line}: especialidade ou fonte de validação inválida")
            competencia = session.scalar(select(Competencia).where(Competencia.referencia == ref))
            if not competencia:
                raise ValueError(f"Linha {line}: competência inexistente")
            proc = session.scalar(select(Procedimento).where(Procedimento.competencia_id == competencia.id,
                                                            Procedimento.codigo == code))
            if not proc:
                raise ValueError(f"Linha {line}: procedimento inexistente")
            spec = session.scalar(select(Especialidade).where(Especialidade.nome == name))
            if spec is None:
                spec = Especialidade(nome=name)
                session.add(spec)
                session.flush()
            link = session.get(EspecialidadeProcedimento, (spec.id, proc.id))
            if link is None:
                session.add(EspecialidadeProcedimento(especialidade_id=spec.id, procedimento_id=proc.id, fonte=source))
                count += 1
        return count
