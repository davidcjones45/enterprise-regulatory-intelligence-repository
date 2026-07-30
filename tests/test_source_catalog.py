from pathlib import Path

from erir.cli import build_parser
from erir.source_catalog import filter_sources, format_source_table, load_sources
from erir.validator import RepositoryValidator

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalog" / "sources"


def test_catalog_records_validate():
    validator = RepositoryValidator(ROOT / "schemas")
    findings = validator.validate_paths([CATALOG])
    assert len(findings) == 8
    assert all(finding.valid for finding in findings), findings


def test_catalog_filters_by_jurisdiction_and_status():
    sources = load_sources(CATALOG)
    colorado = filter_sources(sources, jurisdiction="Colorado", status="effective")
    assert [source["id"] for source in colorado] == ["SRC-US-CO-SB24-205"]
    assert filter_sources(sources, jurisdiction="US-CO") == colorado


def test_catalog_filters_nonbinding_sources():
    sources = load_sources(CATALOG)
    matches = filter_sources(sources, binding_effect="nonbinding")
    assert [source["id"] for source in matches] == [
        "SRC-US-CFPB-CIRCULAR-2022-03",
        "SRC-US-NIST-AI-RMF-1-0",
        "SRC-US-EEOC-AI-ADA",
    ]


def test_source_table_contains_operational_fields():
    table = format_source_table(load_sources(CATALOG))
    assert "JURISDICTION" in table
    assert "SRC-US-TX-HB149" in table
    assert "SRC-US-NYC-LL144-AEDT" in table
    assert "2026-01-01" in table


def test_sources_cli_defaults_to_catalog(capsys):
    args = build_parser().parse_args(["sources", "list", "--jurisdiction", "Texas"])
    assert args.func(args) == 0
    output = capsys.readouterr().out
    assert "SRC-US-TX-HB149" in output
    assert "SRC-US-CO-SB24-205" not in output
