from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def connect(database: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize(database: Path, schema_file: Path) -> None:
    with connect(database) as connection:
        connection.executescript(schema_file.read_text(encoding="utf-8"))


def canonical_json(record: dict[str, Any]) -> str:
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def record_hash(record: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(record).encode("utf-8")).hexdigest()


def append_record(
    connection: sqlite3.Connection,
    record: dict[str, Any],
    *,
    actor: str = "reference-loader",
) -> str:
    event_id = str(uuid.uuid4())
    occurred_at = datetime.now(UTC).isoformat()
    payload = canonical_json(record)
    digest = record_hash(record)
    record_id = record["id"]
    record_type = record["record_type"]

    connection.execute(
        """
        INSERT INTO ledger_event
            (event_id, occurred_at, event_type, record_type, record_id, actor, payload_json, payload_sha256)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (event_id, occurred_at, "record.observed", record_type, record_id, actor, payload, digest),
    )
    connection.execute(
        """
        INSERT INTO current_record (record_type, record_id, payload_json, payload_sha256, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(record_type, record_id) DO UPDATE SET
            payload_json = excluded.payload_json,
            payload_sha256 = excluded.payload_sha256,
            updated_at = excluded.updated_at
        """,
        (record_type, record_id, payload, digest, occurred_at),
    )
    return event_id


def load_records(connection: sqlite3.Connection, records: Iterable[dict[str, Any]]) -> int:
    count = 0
    with connection:
        for record in records:
            append_record(connection, record)
            count += 1
    return count


def append_review_disposition(
    connection: sqlite3.Connection,
    *,
    scenario_id: str,
    disposition: str,
    reviewer: str,
    rationale: str,
) -> dict[str, Any]:
    """Append a human review disposition and update its current projection."""
    reviewed_at = datetime.now(UTC).isoformat()
    review = {
        "record_type": "applicability_review",
        "id": str(uuid.uuid4()),
        "scenario_id": scenario_id,
        "disposition": disposition,
        "reviewer": reviewer,
        "rationale": rationale,
        "reviewed_at": reviewed_at,
    }
    previous = connection.execute(
        "SELECT payload_sha256 FROM ledger_event ORDER BY sequence_no DESC LIMIT 1"
    ).fetchone()
    payload = canonical_json(review)
    digest = record_hash(review)
    with connection:
        connection.execute(
            """
            INSERT INTO ledger_event
                (event_id, occurred_at, event_type, record_type, record_id, actor, payload_json,
                 payload_sha256, previous_event_sha256)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                review["id"],
                reviewed_at,
                "review.disposition_recorded",
                "applicability_review",
                scenario_id,
                reviewer,
                payload,
                digest,
                previous["payload_sha256"] if previous else None,
            ),
        )
        connection.execute(
            """
            INSERT INTO current_record (record_type, record_id, payload_json, payload_sha256, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(record_type, record_id) DO UPDATE SET
                payload_json = excluded.payload_json,
                payload_sha256 = excluded.payload_sha256,
                updated_at = excluded.updated_at
            """,
            ("applicability_review", scenario_id, payload, digest, reviewed_at),
        )
    return review


def current_review_dispositions(connection: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    rows = connection.execute(
        "SELECT record_id, payload_json FROM current_record WHERE record_type = 'applicability_review'"
    ).fetchall()
    return {row["record_id"]: json.loads(row["payload_json"]) for row in rows}


def review_history(connection: sqlite3.Connection, scenario_id: str) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT occurred_at, actor, payload_json, payload_sha256, previous_event_sha256
        FROM ledger_event
        WHERE event_type = 'review.disposition_recorded' AND record_id = ?
        ORDER BY sequence_no
        """,
        (scenario_id,),
    ).fetchall()
    return [
        {
            **json.loads(row["payload_json"]),
            "event_hash": row["payload_sha256"],
            "previous_event_hash": row["previous_event_sha256"],
        }
        for row in rows
    ]


def reconstruct_obligation(connection: sqlite3.Connection, obligation_id: str) -> list[dict[str, Any]]:
    rows = connection.execute(
        Path(__file__).resolve().parents[2].joinpath("sql", "reconstruct_obligation.sql")
        .read_text(encoding="utf-8"),
        {"obligation_id": obligation_id},
    ).fetchall()
    return [dict(row) for row in rows]
