import argparse
import json
from pathlib import Path
import re
from src.importers.sigtap_excel import inspect_workbook


def main():
    parser = argparse.ArgumentParser(description="Inspeção e importação de dados SIGTAP")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("inspect-sigtap", "import-sigtap"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--file", type=Path, required=True)
        cmd.add_argument("--sheet")
        cmd.add_argument("--report", type=Path)
        if name == "import-sigtap":
            cmd.add_argument("--competencia", required=True, help="YYYY-MM, confirmada pelo operador")
            cmd.add_argument("--origem", default="Planilha fornecida ao projeto")
    specialty = sub.add_parser("import-specialties")
    specialty.add_argument("--file", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "import-specialties":
        from src.database.session import make_session_factory
        from src.importers.specialties import import_specialties
        try:
            with make_session_factory().begin() as session:
                count = import_specialties(session, args.file)
            print(json.dumps({"specialty_links_added": count}))
        except (OSError, ValueError, RuntimeError) as exc:
            parser.exit(1, f"Erro: {exc}\n")
        return
    if args.command == "import-sigtap" and (not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", args.competencia)):
        parser.error("--competencia deve estar no formato YYYY-MM")
    try:
        inspection = inspect_workbook(args.file, args.sheet)
        report = inspection.report()
        if args.command == "import-sigtap":
            from src.database.session import make_session_factory
            from src.importers.persist import persist
            with make_session_factory().begin() as session:
                report["import"] = persist(session, inspection, args.competencia, args.origem)
            report["competencia"] = args.competencia
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(1, f"Erro: {exc}\n")


if __name__ == "__main__":
    main()
