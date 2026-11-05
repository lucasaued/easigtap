"""Read and validate the supplied workbook without changing its source data."""
from collections import Counter
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
import re
from openpyxl import load_workbook
from src.parsers.cids import parse_cids
from src.parsers.procedimentos import clean_text, parse_procedimento

REQUIRED = {"Procedimento", "Descrição", "CID", "CID Secundário", "Qtd Máxima"}


def canonical_header(value: object) -> str:
    # Some supplied headers already contain U+FFFD. Keep their raw spelling in attributes.
    value = clean_text(value).casefold().replace("�", "")
    result = re.sub(r"[^a-z0-9]", "", value.translate(str.maketrans("ãáâàéêíóôõúç", "aaaaeeiooouc")))
    return {"descrio": "descricao", "cidsecundrio": "cidsecundario", "qtdmxima": "qtdmaxima"}.get(result, result)


@dataclass
class Record:
    line: int
    code: str
    name: str
    description: str | None
    original: str
    attributes: dict
    cids: dict[str, list[str]]


@dataclass
class Inspection:
    path: str
    sha256: str
    sheet: str
    sheets: list[str]
    headers: list[str]
    rows: int = 0
    records: list[Record] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    warnings: list[dict] = field(default_factory=list)
    empty_fields: Counter = field(default_factory=Counter)

    def report(self) -> dict:
        return {
            "file": self.path, "sha256": self.sha256, "sheet": self.sheet,
            "sheets": self.sheets, "headers": self.headers,
            "counts": {"rows": self.rows, "valid_procedures": len(self.records),
                       "skipped_rows": self.rows - len(self.records),
                       "cid_links": sum(len(codes) for rec in self.records for codes in rec.cids.values()),
                       "errors": len(self.errors), "warnings": len(self.warnings)},
            "empty_fields": dict(self.empty_fields),
            "errors": self.errors, "warnings": self.warnings,
        }


def inspect_workbook(path: Path, sheet: str | None = None) -> Inspection:
    digest = sha256(path.read_bytes()).hexdigest()
    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        sheets = workbook.sheetnames
        if sheet is None:
            if len(sheets) != 1:
                raise ValueError("Informe --sheet para planilhas com mais de uma aba")
            sheet = sheets[0]
        if sheet not in sheets:
            raise ValueError(f"Aba inexistente: {sheet}")
        rows = workbook[sheet].iter_rows(values_only=True)
        headers = [clean_text(v) for v in next(rows)]
        canonical = {canonical_header(v): i for i, v in enumerate(headers)}
        missing = [v for v in REQUIRED if canonical_header(v) not in canonical]
        if missing:
            raise ValueError(f"Colunas essenciais ausentes: {', '.join(sorted(missing))}")
        result = Inspection(str(path), digest, sheet, sheets, headers)
        seen: dict[str, int] = {}
        for line, values in enumerate(rows, start=2):
            if all(v is None for v in values):
                continue
            result.rows += 1
            data = {headers[i]: values[i] if i < len(values) else None for i in range(len(headers))}
            for key, value in data.items():
                if value is None or str(value).strip() == "":
                    result.empty_fields[key] += 1
            def get(key: str):
                i = canonical[canonical_header(key)]
                return values[i] if i < len(values) else None
            raw_identification = get("Procedimento")
            original = str(raw_identification) if raw_identification is not None else ""
            try:
                code, name = parse_procedimento(original)
            except ValueError as exc:
                result.errors.append({"line": line, "field": "Procedimento", "message": str(exc)})
                continue
            if code in seen:
                result.errors.append({"line": line, "field": "Procedimento", "message": f"Código {code} duplicado; primeira linha {seen[code]}"})
                continue
            seen[code] = line
            cids = {}
            for key, kind in (("CID", "principal"), ("CID Secundário", "secundario")):
                codes, errors = parse_cids(get(key))
                cids[kind] = codes
                result.errors.extend({"line": line, "field": key, "message": error} for error in errors)
            if any("�" in str(v) for v in data.values() if v is not None):
                result.warnings.append({"line": line, "message": "Texto contém caractere de substituição U+FFFD; origem preservada"})
            description = get("Descrição")
            result.records.append(Record(line, code, name, str(description) if description is not None else None,
                                         original, {k: str(v) if v is not None else None for k, v in data.items()
                                                    if canonical_header(k) not in {canonical_header("Procedimento"), canonical_header("Descrição"), canonical_header("CID"), canonical_header("CID Secundário")}}, cids))
        return result
    finally:
        workbook.close()
