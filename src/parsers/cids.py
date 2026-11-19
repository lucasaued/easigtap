import re
from src.parsers.procedimentos import clean_text

CID_PATTERN = re.compile(r"^[A-Z][0-9]{2}(?:\.?[0-9A-Z]{1,4})?$", re.IGNORECASE)


def canonical_cid(code: str) -> str:
    """Normalize notation for lookup; this does not verify an official CID."""
    return code.upper().replace(".", "")


def parse_cids_with_origins(value: object) -> tuple[dict[str, str], list[str]]:
    result: dict[str, str] = {}
    errors: list[str] = []
    if value is None:
        return result, errors
    for raw in str(value).split(","):
        code = clean_text(raw)
        if not code:
            if str(value).strip():
                errors.append("CID vazio na lista")
            continue
        if not CID_PATTERN.fullmatch(code):
            errors.append(f"CID malformado: {code}")
            continue
        result.setdefault(canonical_cid(code), code)
    return result, errors


def parse_cids(value: object) -> tuple[list[str], list[str]]:
    origins, errors = parse_cids_with_origins(value)
    return list(origins), errors
