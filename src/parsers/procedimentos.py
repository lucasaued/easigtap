import re

PATTERN = re.compile(r"^\s*(\d{10})\s*-\s*(\S(?:.*\S)?)\s*$", re.DOTALL)


def clean_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("\x00", " ")).strip()


def parse_procedimento(value: object) -> tuple[str, str]:
    text = clean_text(value)
    match = PATTERN.fullmatch(text)
    if not match:
        raise ValueError("Procedimento deve começar com código de 10 dígitos, hífen e nome")
    return match.group(1), clean_text(match.group(2))
