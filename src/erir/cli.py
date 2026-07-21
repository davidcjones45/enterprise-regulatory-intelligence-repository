from __future__ import annotations

import argparse
from pathlib import Path
import json

from .ledger import connect, initialize, load_records, reconstruct_obligation
from .models import load_json
from .validator import RepositoryValidator


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def cmd_validate(args: argparse.Namespace) -> int:
    validator = RepositoryValidator(repository_root() / "schemas")
    findings = validator.validate_paths([Path(value) for value in args.paths])
    invalid = 0
    for finding in findings:
        status = "VALID" if finding.valid else "INVALID"
        print(f"{status}: {finding.file} [{finding.schema or 'no schema'}]")
        for message in finding.messages:
            print(f"  - {message}")
        invalid += int(not finding.valid)
    print(f"\nValidated {len(findings)} file(s); {invalid} invalid.")
    return 1 if invalid else 0


def cmd_init_ledger(args: argparse.Namespace) -> int:
    database = Path(args.database)
    initialize(database, repository_root() / "sql" / "schema.sql")
    print(f"Initialized ledger: {database}")
    return 0


def cmd_load_examples(args: argparse.Namespace) -> int:
    database = Path(args.database)
    directory = Path(args.directory)
    records = [load_json(path) for path in sorted(directory.rglob("*.json"))]
    with connect(database) as connection:
        count = load_records(connection, records)
    print(f"Loaded {count} record(s) into {database}")
    return 0


def cmd_reconstruct(args: argparse.Namespace) -> int:
    with connect(Path(args.database)) as connection:
        rows = reconstruct_obligation(connection, args.obligation_id)
    print(json.dumps(rows, indent=2))
    return 0 if rows else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="erir",
        description="Enterprise Regulatory Intelligence Repository tools",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="Validate JSON records")
    validate.add_argument("paths", nargs="+")
    validate.set_defaults(func=cmd_validate)

    init_ledger = subparsers.add_parser("init-ledger", help="Create a SQLite evidence ledger")
    init_ledger.add_argument("database")
    init_ledger.set_defaults(func=cmd_init_ledger)

    load_examples = subparsers.add_parser("load-examples", help="Load JSON records into the ledger")
    load_examples.add_argument("database")
    load_examples.add_argument("directory")
    load_examples.set_defaults(func=cmd_load_examples)

    reconstruct = subparsers.add_parser("reconstruct", help="Reconstruct an obligation trace")
    reconstruct.add_argument("database")
    reconstruct.add_argument("obligation_id")
    reconstruct.set_defaults(func=cmd_reconstruct)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
