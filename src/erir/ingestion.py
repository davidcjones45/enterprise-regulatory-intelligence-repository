from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")


def _source_key(source_id: str) -> str:
    return source_id.casefold().replace("/", "-")


def _default_open(url: str):
    return urlopen(Request(url, headers={"User-Agent": "ERIR-source-ingestion/0.2.1"}), timeout=30)


class SourceIngestor:
    """Stores immutable retrieval snapshots and queues changed source material for review."""

    def __init__(self, storage_directory: Path, opener: Callable[[str], Any] = _default_open):
        self.storage_directory = storage_directory
        self.opener = opener

    def ingest(self, source: Mapping[str, Any]) -> dict[str, Any]:
        source_id = str(source["id"])
        official_url = str(source["official_url"])
        with self.opener(official_url) as response:
            content = response.read()
            content_type = response.headers.get_content_type()
            status_code = getattr(response, "status", 200)

        content_sha256 = hashlib.sha256(content).hexdigest()
        source_key = _source_key(source_id)
        document_path = self.storage_directory / "documents" / source_key / f"{content_sha256}.bin"
        document_path.parent.mkdir(parents=True, exist_ok=True)
        if not document_path.exists():
            document_path.write_bytes(content)

        snapshot_path = self.storage_directory / "snapshots" / f"{source_key}.json"
        snapshots: list[dict[str, Any]] = _read_json(snapshot_path, [])
        prior_hash = snapshots[-1]["content_sha256"] if snapshots else None
        change_type = "new" if prior_hash is None else "unchanged" if prior_hash == content_sha256 else "changed"
        snapshot = {
            "source_id": source_id,
            "official_url": official_url,
            "retrieved_at": utc_now(),
            "content_sha256": content_sha256,
            "content_type": content_type,
            "status_code": status_code,
            "content_path": str(document_path.relative_to(self.storage_directory)),
            "change_type": change_type,
        }
        snapshots.append(snapshot)
        _write_json(snapshot_path, snapshots)

        if change_type != "unchanged":
            self._enqueue_extraction_task(snapshot)
        return snapshot

    def _enqueue_extraction_task(self, snapshot: Mapping[str, Any]) -> None:
        queue_path = self.storage_directory / "queues" / "extraction.json"
        tasks: list[dict[str, Any]] = _read_json(queue_path, [])
        task_id = f"TASK-{snapshot['source_id']}-{snapshot['content_sha256'][:12]}"
        if any(task["id"] == task_id for task in tasks):
            return
        tasks.append(
            {
                "id": task_id,
                "status": "pending_human_review",
                "source_id": snapshot["source_id"],
                "snapshot_sha256": snapshot["content_sha256"],
                "source_url": snapshot["official_url"],
                "queued_at": utc_now(),
                "reason": f"authoritative source content {snapshot['change_type']}",
            }
        )
        _write_json(queue_path, tasks)

    def extraction_tasks(self) -> list[dict[str, Any]]:
        return _read_json(self.storage_directory / "queues" / "extraction.json", [])

    def queue_machine_candidate(
        self,
        *,
        source_id: str,
        snapshot_sha256: str,
        candidate_text: str,
        pinpoint: str,
        generator: str,
    ) -> dict[str, Any]:
        queue_path = self.storage_directory / "queues" / "machine-candidates.json"
        candidates: list[dict[str, Any]] = _read_json(queue_path, [])
        candidate = {
            "id": f"CAND-{source_id}-{snapshot_sha256[:12]}-{len(candidates) + 1:04d}",
            "status": "pending_human_review",
            "candidate_text": candidate_text,
            "pinpoint": pinpoint,
            "provenance": {
                "generator": generator,
                "generated_at": utc_now(),
                "source_id": source_id,
                "snapshot_sha256": snapshot_sha256,
            },
        }
        candidates.append(candidate)
        _write_json(queue_path, candidates)
        return candidate
