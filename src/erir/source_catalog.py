from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .models import load_json


def load_sources(directory: Path) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for path in sorted(directory.rglob("*.json")):
        record = load_json(path)
        if not isinstance(record, dict) or record.get("record_type") != "regulatory_source":
            raise ValueError(f"Catalog file is not a regulatory source: {path}")
        sources.append(record)
    return sources


def filter_sources(
    sources: Iterable[dict[str, Any]],
    *,
    jurisdiction: str | None = None,
    status: str | None = None,
    source_type: str | None = None,
    binding_effect: str | None = None,
) -> list[dict[str, Any]]:
    jurisdiction_query = jurisdiction.casefold() if jurisdiction else None

    def matches(source: dict[str, Any]) -> bool:
        jurisdiction_values = {
            value.casefold()
            for item in source.get("jurisdictions", [])
            for value in (
                item.get("country_code"),
                item.get("subdivision_code"),
                item.get("name"),
            )
            if value
        }
        return (
            (jurisdiction_query is None or jurisdiction_query in jurisdiction_values)
            and (status is None or source.get("legal_status") == status)
            and (source_type is None or source.get("source_type") == source_type)
            and (binding_effect is None or source.get("binding_effect") == binding_effect)
        )

    return sorted(
        (source for source in sources if matches(source)),
        key=lambda source: (source["jurisdictions"][0]["name"], source["title"]),
    )


def jurisdiction_label(source: dict[str, Any]) -> str:
    return ", ".join(
        jurisdiction.get("subdivision_code") or jurisdiction["country_code"]
        for jurisdiction in source["jurisdictions"]
    )


def format_source_table(sources: Iterable[dict[str, Any]]) -> str:
    rows = [
        (
            source["id"],
            jurisdiction_label(source),
            source["legal_status"],
            source["source_type"],
            source.get("effective_date") or "-",
            source["title"],
        )
        for source in sources
    ]
    headers = ("ID", "JURISDICTION", "STATUS", "TYPE", "EFFECTIVE", "TITLE")
    if not rows:
        return "No regulatory sources matched."

    widths = [max(len(str(row[index])) for row in [headers, *rows]) for index in range(len(headers))]
    return "\n".join(
        "  ".join(str(value).ljust(widths[index]) for index, value in enumerate(row)).rstrip()
        for row in [headers, *rows]
    )
