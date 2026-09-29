from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from erir.demo import INDEX_HTML, build_demo_scenarios

SCENARIO_PAYLOADS = {
    scenario["id"]: scenario["payload"] for scenario in build_demo_scenarios(ROOT)
}
SCENARIO_LIST = [
    {"id": scenario["id"], "label": scenario["label"]}
    for scenario in build_demo_scenarios(ROOT)
]


def _pending_reviews() -> dict[str, dict[str, object]]:
    return {
        scenario_id: {
            "status": "pending",
            "reviewer": None,
            "rationale": None,
            "updated_at": None,
        }
        for scenario_id in SCENARIO_PAYLOADS
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        request = urlsplit(self.path)
        query = parse_qs(request.query)
        route = query.get("route", [""])[0]

        if route == "root" or request.path in {"/", "/api/index.py"}:
            self._respond(200, "text/html; charset=utf-8", INDEX_HTML.encode("utf-8"))
            return

        if route == "demo":
            scenario = query.get("scenario", ["consumer_claims"])[0]
            payload = SCENARIO_PAYLOADS.get(
                scenario,
                SCENARIO_PAYLOADS["consumer_claims"],
            )
            self._json(200, payload)
            return

        if route == "scenarios":
            self._json(200, SCENARIO_LIST)
            return

        if route == "reviews":
            self._json(200, _pending_reviews())
            return

        if route == "review-history":
            scenario = query.get("scenario", ["consumer_claims"])[0]
            if scenario not in SCENARIO_PAYLOADS:
                self._json(400, {"error": "Unknown demonstration scenario."})
                return
            self._json(200, [])
            return

        if route == "export":
            scenario = query.get("scenario", ["consumer_claims"])[0]
            if scenario not in SCENARIO_PAYLOADS:
                self._json(400, {"error": "Unknown demonstration scenario."})
                return
            package = {
                "package_type": "regulatory_intelligence_evidence_package",
                "scenario_id": scenario,
                "exported_at": datetime.now(UTC).isoformat(),
                "disclaimer": (
                    "Illustrative demonstration package only. Not legal advice "
                    "or a legal applicability determination."
                ),
                "trace": SCENARIO_PAYLOADS[scenario],
                "current_review": _pending_reviews()[scenario],
                "review_history": [],
                "public_demo_mode": "read_only",
            }
            body = json.dumps(package, indent=2).encode("utf-8")
            self._respond(
                200,
                "application/json; charset=utf-8",
                body,
                {
                    "Content-Disposition": (
                        f'attachment; filename="erir-evidence-package-{scenario}.json"'
                    )
                },
            )
            return

        self._respond(404, "text/plain; charset=utf-8", b"Not found")

    def do_POST(self) -> None:
        request = urlsplit(self.path)
        query = parse_qs(request.query)
        route = query.get("route", [""])[0]
        if route == "review":
            self._json(
                405,
                {
                    "error": (
                        "The public Vercel demonstration is read-only. "
                        "Run erir serve-demo locally to record reviewer dispositions."
                    )
                },
            )
            return
        self._respond(404, "text/plain; charset=utf-8", b"Not found")

    def _json(self, status: int, payload: object) -> None:
        self._respond(
            status,
            "application/json; charset=utf-8",
            json.dumps(payload).encode("utf-8"),
        )

    def _respond(
        self,
        status: int,
        content_type: str,
        body: bytes,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return
