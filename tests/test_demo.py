import json
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.request import urlopen

from erir.demo import (
    INDEX_HTML,
    DemoReviewQueue,
    build_demo_payload,
    build_demo_scenarios,
    make_handler,
)

ROOT = Path(__file__).resolve().parents[1]


def test_demo_payload_preserves_human_review_boundary():
    payload = build_demo_payload(ROOT)
    assert payload["screening"]["screening_decision"] == "potentially_applies"
    assert payload["screening"]["human_review_required"] is True
    assert payload["screening"]["legal_conclusion"] is False
    assert payload["control"]["id"] == "CTL-CLAIMS-001"


def test_demo_page_exposes_only_local_demo_endpoint():
    assert "/api/demo" in INDEX_HTML
    assert "not legal advice" in INDEX_HTML


def test_demo_server_serves_the_trace_and_api():
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ROOT))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urlopen(f"http://127.0.0.1:{server.server_port}/api/demo", timeout=3) as response:
            payload = response.read().decode("utf-8")
        with urlopen(f"http://127.0.0.1:{server.server_port}/", timeout=3) as response:
            page = response.read().decode("utf-8")
    finally:
        server.shutdown()
        thread.join(timeout=3)
        server.server_close()
    assert '"human_review_required": true' in payload
    assert "Traceable Regulatory Intelligence" in page


def test_export_package_contains_trace_and_review_history(tmp_path):
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ROOT))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urlopen(
            f"http://127.0.0.1:{server.server_port}/api/export?scenario=consumer_claims", timeout=3
        ) as response:
            package = json.loads(response.read().decode("utf-8"))
            disposition = response.headers["Content-Disposition"]
    finally:
        server.shutdown()
        thread.join(timeout=3)
        server.server_close()
    assert package["package_type"] == "regulatory_intelligence_evidence_package"
    assert package["trace"]["screening"]["human_review_required"] is True
    assert "consumer_claims" in disposition


def test_demo_scenarios_show_bounded_different_outcomes():
    scenarios = build_demo_scenarios(ROOT)
    decisions = {scenario["id"]: scenario["payload"]["screening"]["screening_decision"] for scenario in scenarios}
    assert decisions == {
        "consumer_claims": "potentially_applies",
        "internal_service": "undetermined",
        "non_us_service": "undetermined",
    }


def test_review_queue_persists_accountable_review(tmp_path):
    queue = DemoReviewQueue(tmp_path / "review.db", ROOT / "sql" / "schema.sql", ["consumer_claims"])
    item = queue.record("consumer_claims", "approved", "Compliance Manager", "Facts are complete for the demonstration screen.")
    assert item["status"] == "approved"
    assert item["reviewer"] == "Compliance Manager"
    restarted_queue = DemoReviewQueue(tmp_path / "review.db", ROOT / "sql" / "schema.sql", ["consumer_claims"])
    assert restarted_queue.snapshot()["consumer_claims"]["status"] == "approved"
    history = restarted_queue.history("consumer_claims")
    assert len(history) == 1
    assert history[0]["reviewer"] == "Compliance Manager"
    assert history[0]["event_hash"]
