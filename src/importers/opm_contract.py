"""Contract for a future official OPM compatibility importer."""
from dataclasses import dataclass


@dataclass(frozen=True)
class OfficialOpmRelation:
    competencia: str
    procedimento_codigo: str
    opm_codigo: str
    opm_nome: str
    tipo: str
    fonte: str
    limite_quantidade: int | None = None
    pendencia: str | None = None

    def validate(self) -> None:
        if not all((self.competencia, self.procedimento_codigo, self.opm_codigo,
                    self.opm_nome, self.tipo, self.fonte)):
            raise ValueError("Relação OPM exige identificação, tipo e fonte oficial")
        if self.limite_quantidade is not None and self.limite_quantidade < 0:
            raise ValueError("Limite de OPM não pode ser negativo")
