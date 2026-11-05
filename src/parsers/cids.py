import re
from src.parsers.procedimentos import clean_text

CID_PATTERN = re.compile(r"^[A-Z][0-9]{2}(?:\.?[0-9A-Z]{1,4})?$", re.IGNORECASE)


def parse_cids(value: object) -> tuple[list[str], list[str]]:
    result: list[str] = []
    errors: list[str] = []
    seen: set[str] = set()
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
        elif code.upper() not in seen:
            result.append(code)
            seen.add(code.upper())
    return result, errors
