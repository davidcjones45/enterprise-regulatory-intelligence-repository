import json
from pathlib import Path

from erir.integration import build_event, build_grc_package, dispatch_event
from erir.models import load_json

ROOT = Path(__file__).resolve().parents[1]


class FakeResponse:
    status = 202
    def __enter__(self): return self
    def __exit__(self, *_): return False


def test_event_is_cloudevents_compatible_and_can_be_signed():
    event = build_event(load_json(ROOT / "examples" / "valid" / "obligation.json"), event_id="event-123")
    requests = []
    assert event["specversion"] == "1.0"
    assert dispatch_event(event, "https://receiver.example/events", signing_key=b"test-key", sender=lambda request: requests.append(request) or FakeResponse()) == 202
    assert requests[0].get_header("X-erir-signature").startswith("sha256=")
    assert json.loads(requests[0].data)["data"]["record"]["id"] == "OBL-FTC-001"


def test_grc_package_keeps_records_and_trace_relationships():
    records = [load_json(ROOT / "examples" / "valid" / name) for name in ("regulatory_source.json", "obligation.json", "control.json", "evidence.json")]
    package = build_grc_package(records)
    assert package["package_type"] == "erir_grc_import_package"
    assert len(package["records"]) == 4
    assert {item["type"] for item in package["relationships"]} == {"source_supports_obligation", "obligation_addressed_by_control", "control_supported_by_evidence"}
