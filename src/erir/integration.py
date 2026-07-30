from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from collections.abc import Callable, Iterable, Mapping
from datetime import UTC, datetime
from typing import Any
from urllib.request import Request, urlopen

CONTRACT_VERSION = "1.0"


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_event(record: Mapping[str, Any], *, event_type: str = "erir.record.upserted", event_id: str | None = None) -> dict[str, Any]:
    """Create a CloudEvents-compatible event without transmitting it."""
    return {"specversion": "1.0", "id": event_id or str(uuid.uuid4()), "type": event_type, "source": "erir://local", "subject": str(record["id"]), "time": utc_now(), "datacontenttype": "application/json", "data": {"contract_version": CONTRACT_VERSION, "record": dict(record)}}


def dispatch_event(event: Mapping[str, Any], endpoint: str, *, signing_key: bytes | None = None, sender: Callable[[Request], Any] = urlopen) -> int:
    """POST a generic event; callers control the endpoint and optional signing key."""
    payload = json.dumps(event, sort_keys=True, separators=(",", ":")).encode("utf-8")
    headers = {"Content-Type": "application/cloudevents+json", "X-ERIR-Contract-Version": CONTRACT_VERSION, "X-ERIR-Content-SHA256": hashlib.sha256(payload).hexdigest()}
    if signing_key is not None:
        headers["X-ERIR-Signature"] = "sha256=" + hmac.new(signing_key, payload, hashlib.sha256).hexdigest()
    with sender(Request(endpoint, data=payload, headers=headers, method="POST")) as response:
        return getattr(response, "status", 200)


def build_grc_package(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Produce a vendor-neutral record package and explicit relationship list."""
    items = [dict(record) for record in records]
    relationships: list[dict[str, str]] = []
    for record in items:
        record_id, record_type = str(record["id"]), record["record_type"]
        if record_type == "obligation":
            relationships.append({"type": "source_supports_obligation", "from": str(record["source_id"]), "to": record_id})
        elif record_type == "control":
            relationships.extend({"type": "obligation_addressed_by_control", "from": obligation_id, "to": record_id} for obligation_id in record["obligation_ids"])
        elif record_type == "evidence":
            relationships.append({"type": "control_supported_by_evidence", "from": str(record["control_id"]), "to": record_id})
        elif record_type == "applicability_assessment":
            relationships.append({"type": "obligation_assessed_for", "from": str(record["obligation_id"]), "to": record_id})
    return {"package_type": "erir_grc_import_package", "contract_version": CONTRACT_VERSION, "generated_at": utc_now(), "records": items, "relationships": relationships}
