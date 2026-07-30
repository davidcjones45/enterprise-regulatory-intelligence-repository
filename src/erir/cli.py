from __future__ import annotations

import argparse
import json
from pathlib import Path

from .applicability import screen_profile
from .demo import serve_demo
from .ingestion import SourceIngestor
from .integration import build_event, build_grc_package
from .ledger import connect, initialize, load_records, reconstruct_obligation
from .models import load_json
from .source_catalog import filter_sources, format_source_table, load_sources
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


def cmd_sources_list(args: argparse.Namespace) -> int:
    sources = filter_sources(
        load_sources(Path(args.directory)),
        jurisdiction=args.jurisdiction,
        status=args.status,
        source_type=args.source_type,
        binding_effect=args.binding_effect,
    )
    if args.format == "json":
        print(json.dumps(sources, indent=2))
    else:
        print(format_source_table(sources))
    return 0


def cmd_screen_profile(args: argparse.Namespace) -> int:
    profile = load_json(Path(args.profile))
    rule = load_json(Path(args.rule))
    print(json.dumps(screen_profile(profile, rule), indent=2))
    return 0


def _source_by_id(directory: Path, source_id: str) -> dict[str, object]:
    for source in load_sources(directory):
        if source["id"] == source_id:
            return source
    raise ValueError(f"Source not found: {source_id}")


def cmd_ingest_source(args: argparse.Namespace) -> int:
    source = _source_by_id(Path(args.directory), args.source_id)
    snapshot = SourceIngestor(Path(args.storage_directory)).ingest(source)
    print(json.dumps(snapshot, indent=2))
    return 0


def cmd_ingestion_queue(args: argparse.Namespace) -> int:
    ingestor = SourceIngestor(Path(args.storage_directory))
    print(json.dumps(ingestor.extraction_tasks(), indent=2))
    return 0


def cmd_queue_machine_candidate(args: argparse.Namespace) -> int:
    candidate = SourceIngestor(Path(args.storage_directory)).queue_machine_candidate(
        source_id=args.source_id,
        snapshot_sha256=args.snapshot_sha256,
        candidate_text=args.candidate_text,
        pinpoint=args.pinpoint,
        generator=args.generator,
    )
    print(json.dumps(candidate, indent=2))
    return 0


def cmd_export_grc(args: argparse.Namespace) -> int:
    records = [load_json(path) for path in sorted(Path(args.directory).rglob("*.json"))]
    print(json.dumps(build_grc_package(records), indent=2))
    return 0


def cmd_emit_event(args: argparse.Namespace) -> int:
    print(json.dumps(build_event(load_json(Path(args.record)), event_type=args.event_type), indent=2))
    return 0


def cmd_serve_demo(args: argparse.Namespace) -> int:
    serve_demo(repository_root(), args.port)
    return 0


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

    sources = subparsers.add_parser("sources", help="Query the regulatory source catalog")
    source_commands = sources.add_subparsers(dest="sources_command", required=True)
    sources_list = source_commands.add_parser("list", help="List cataloged regulatory sources")
    sources_list.add_argument(
        "--directory",
        default=str(repository_root() / "catalog" / "sources"),
        help="Source catalog directory",
    )
    sources_list.add_argument("--jurisdiction", help="Country code, subdivision code, or name")
    sources_list.add_argument("--status", help="Current legal status")
    sources_list.add_argument("--source-type", help="Regulatory source type")
    sources_list.add_argument("--binding-effect", help="Binding effect classification")
    sources_list.add_argument("--format", choices=("table", "json"), default="table")
    sources_list.set_defaults(func=cmd_sources_list)

    screen = subparsers.add_parser(
        "screen-profile",
        help="Run a fact-based applicability screen; human review remains required",
    )
    screen.add_argument("profile", help="Path to a subject_profile JSON record")
    screen.add_argument("rule", help="Path to an applicability_rule JSON record")
    screen.set_defaults(func=cmd_screen_profile)

    ingest = subparsers.add_parser("ingest-source", help="Retrieve and snapshot an authoritative source")
    ingest.add_argument("source_id", help="Catalog source identifier")
    ingest.add_argument("--directory", default=str(repository_root() / "catalog" / "sources"))
    ingest.add_argument("--storage-directory", default="ingestion-data")
    ingest.set_defaults(func=cmd_ingest_source)

    ingestion_queue = subparsers.add_parser("ingestion-queue", help="List pending extraction tasks")
    ingestion_queue.add_argument("--storage-directory", default="ingestion-data")
    ingestion_queue.set_defaults(func=cmd_ingestion_queue)

    candidate = subparsers.add_parser("queue-machine-candidate", help="Queue a machine-generated candidate")
    candidate.add_argument("source_id")
    candidate.add_argument("snapshot_sha256")
    candidate.add_argument("candidate_text")
    candidate.add_argument("--pinpoint", required=True)
    candidate.add_argument("--generator", required=True)
    candidate.add_argument("--storage-directory", default="ingestion-data")
    candidate.set_defaults(func=cmd_queue_machine_candidate)

    export_grc = subparsers.add_parser("export-grc", help="Export a vendor-neutral GRC import package")
    export_grc.add_argument("directory", help="Directory containing ERIR JSON records")
    export_grc.set_defaults(func=cmd_export_grc)

    emit_event = subparsers.add_parser("emit-event", help="Create a generic record event without sending it")
    emit_event.add_argument("record", help="Path to an ERIR JSON record")
    emit_event.add_argument("--event-type", default="erir.record.upserted")
    emit_event.set_defaults(func=cmd_emit_event)

    demo = subparsers.add_parser("serve-demo", help="Serve the local demonstration interface")
    demo.add_argument("--port", type=int, default=8765, help="Local port to use (default: 8765)")
    demo.set_defaults(func=cmd_serve_demo)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
