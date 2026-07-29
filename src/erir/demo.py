from __future__ import annotations

import json
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from .applicability import screen_profile
from .ledger import (
    append_review_disposition,
    connect,
    current_review_dispositions,
    initialize,
    review_history,
)
from .models import load_json

INDEX_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Enterprise Regulatory Intelligence Repository</title>
<style>
:root { color-scheme: light; --navy:#12324a; --panel:#fffaf1; --teal:#176f71; --gold:#a66a25; --text:#173047; --muted:#5d6b72; }
* { box-sizing:border-box } body { margin:0; font:16px/1.5 Arial,sans-serif; color:var(--text); background:linear-gradient(135deg,#f6eedc,#e7d6b7); }
main { max-width:1180px; margin:auto; padding:48px 24px 64px } .eyebrow { color:var(--gold); font-weight:700; letter-spacing:.12em; font-size:.78rem; }
h1 { font-size:clamp(2rem,5vw,3.7rem); line-height:1.04; margin:.3rem 0 1rem } .lede { color:var(--muted); max-width:780px; font-size:1.12rem }
.notice { margin:28px 0; padding:15px 18px; border-left:4px solid var(--gold); background:#fff7e9; color:#314d5d }
.flow { display:grid; grid-template-columns:repeat(auto-fit,minmax(250px,1fr)); gap:16px; margin-top:30px } .card { background:rgba(255,250,241,.96); border:1px solid rgba(23,111,113,.27); border-radius:12px; padding:20px; min-height:210px; color:inherit; text-align:left; cursor:pointer; transition:transform .15s,border-color .15s,background .15s } .card:hover,.card:focus-visible { transform:translateY(-3px); border-color:var(--teal); background:#fffdf8; outline:2px solid transparent } .card.active { border-color:var(--gold); background:#fff1d9; box-shadow:0 0 28px rgba(166,106,37,.14) }
.stage { color:var(--teal); font-weight:700; font-size:.78rem; letter-spacing:.1em; text-transform:uppercase } h2 { font-size:1.2rem; margin:.35rem 0 .75rem } p { margin:.4rem 0 } .tag { display:inline-block; padding:3px 8px; border-radius:999px; background:#dceceb; color:#15585a; font-size:.78rem; font-weight:700 }
.decision { border-color:rgba(166,106,37,.7); box-shadow:0 0 28px rgba(166,106,37,.09) } code { white-space:normal; color:#285c76 } .detail { margin-top:24px; padding:24px; min-height:190px; border-radius:12px; border:1px solid rgba(23,111,113,.35); background:#fffaf1 } .detail h2 { color:var(--teal) } .detail dl { display:grid; grid-template-columns:minmax(150px,220px) 1fr; gap:10px 18px } .detail dt { color:var(--gold); font-weight:bold } .detail dd { margin:0; color:#314d5d; overflow-wrap:anywhere } .footer { color:var(--muted); margin-top:30px; font-size:.9rem }
</style></head><body><main>
<div class="eyebrow">AI AT HUMAN SCALE · DEMONSTRATION</div><h1>Traceable Regulatory Intelligence</h1>
<p class="lede">A read-only view of the operating path from an authoritative source to a human-reviewed applicability screen, mapped control, and supporting evidence.</p>
<div class="notice"><strong>Important:</strong> this is an illustrative demonstration. It is not legal advice, does not determine legal applicability, and preserves human accountability for material conclusions.</div>
<label class="eyebrow" for="scenario">Illustrative scenario</label><select id="scenario"><option value="consumer_claims">Consumer-facing US AI service</option><option value="internal_service">Internal US AI analytics service</option><option value="non_us_service">Non-US consumer AI service</option></select>
<p><a class="tag" id="export-package" href="#">Download evidence package</a></p>
<section class="flow" id="flow" aria-live="polite"></section>
<section class="detail" id="detail" aria-live="polite"><h2>Select a workflow stage</h2><p>Choose any card to inspect its underlying record and the reasoning boundary applied to it.</p></section>
<section class="detail" id="review"><div class="stage">Governed review queue</div><h2>Record a reviewer disposition</h2><p id="review-status">Loading current queue status…</p><label>Reviewer <input id="reviewer" placeholder="Name or role"></label><label>Rationale <textarea id="rationale" rows="3" placeholder="Why is this disposition appropriate?"></textarea></label><div class="actions"><button data-action="approved">Approve screening</button><button data-action="returned">Return for clarification</button><button data-action="rejected">Reject screening</button></div><p class="footer">Demonstration state is held only while this local server runs. A production queue would retain authenticated reviewer identity and append-only events.</p></section>
<section class="detail"><div class="stage">Review history</div><h2>Reconstructable disposition trail</h2><div id="review-history">Loading review events…</div></section>
<p class="footer">The repository separates source facts, normalized obligations, applicability reasoning, controls, and evidence so a reviewer can reconstruct each decision.</p>
</main><script>
const esc=v=>String(v??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const card=(stage,title,body,cls='')=>`<article class="card ${cls}"><div class="stage">${esc(stage)}</div><h2>${esc(title)}</h2>${body}</article>`;
const selected=new URLSearchParams(location.search).get('scenario')||'consumer_claims';
document.querySelector('#scenario').value=selected;
document.querySelector('#scenario').addEventListener('change',event=>location.search=`?scenario=${event.target.value}`);
document.querySelector('#export-package').href=`/api/export?scenario=${selected}`;
fetch(`/api/demo?scenario=${selected}`).then(r=>r.json()).then(d=>{
 const source=d.source, obligation=d.obligation, profile=d.profile, control=d.control, evidence=d.evidence, screen=d.screening;
 document.querySelector('#flow').innerHTML=[
  card('1 · Source',source.title,`<p><span class="tag">${esc(source.legal_status)}</span> ${esc(source.authority)}</p><p>${esc(source.notes)}</p>`),
  card('2 · Normalized obligation',obligation.title,`<p>${esc(obligation.normalized_text)}</p><p><code>${esc(obligation.id)}</code></p>`),
  card('3 · Subject profile',profile.title,`<p>Owner: ${esc(profile.profile_owner)}</p><p>Facts: ${esc(Object.keys(profile.facts).join(', '))}</p>`),
  card('4 · Screening result',screen.screening_decision,`<p><span class="tag">Human review required</span></p><p>${esc(screen.rationale)}</p><p>Matched criteria: ${esc(screen.matched_criteria.length)}</p>`,'decision'),
  card('5 · Control',control.title,`<p>${esc(control.objective)}</p><p>Owner: ${esc(control.owner)}</p>`),
  card('6 · Evidence',evidence.description,`<p>Type: ${esc(evidence.evidence_type)}</p><p>Assessment: ${esc(evidence.assessment_result)}</p>`)
 ].join('');
 const stages=[source,obligation,profile,screen,control,evidence];
 const show=(record,card)=>{document.querySelectorAll('.card').forEach(c=>c.classList.remove('active'));card.classList.add('active');document.querySelector('#detail').innerHTML=`<div class="stage">Record detail</div><h2>${esc(card.querySelector('h2').textContent)}</h2><dl>${Object.entries(record).map(([k,v])=>`<dt>${esc(k.replaceAll('_',' '))}</dt><dd>${esc(Array.isArray(v)||typeof v==='object'?JSON.stringify(v):v)}</dd>`).join('')}</dl>`;};
 document.querySelectorAll('.card').forEach((card,index)=>{card.tabIndex=0;card.setAttribute('role','button');card.addEventListener('click',()=>show(stages[index],card));card.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();show(stages[index],card);}});});
 const reviewStatus=document.querySelector('#review-status');
 const loadReview=()=>fetch('/api/reviews').then(r=>r.json()).then(reviews=>{const item=reviews[selected];reviewStatus.textContent=`Current status: ${item.status}. ${item.reviewer?`Last reviewer: ${item.reviewer}.`:''} ${item.rationale?`Rationale: ${item.rationale}`:''}`;});
 const historyPanel=document.querySelector('#review-history');
 const loadHistory=()=>fetch(`/api/review-history?scenario=${selected}`).then(r=>r.json()).then(events=>{historyPanel.innerHTML=events.length?events.map(event=>`<p><span class="tag">${esc(event.disposition)}</span> ${esc(event.reviewer)} · ${esc(event.reviewed_at)}<br>${esc(event.rationale)}</p>`).join(''):'<p>No reviewer disposition has been recorded for this scenario.</p>';});
 loadReview();loadHistory();
 document.querySelectorAll('#review button').forEach(button=>button.addEventListener('click',()=>{fetch('/api/review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scenario:selected,disposition:button.dataset.action,reviewer:document.querySelector('#reviewer').value,rationale:document.querySelector('#rationale').value})}).then(async response=>{const result=await response.json();if(!response.ok){reviewStatus.textContent=`Review not recorded: ${result.error}`;return;}reviewStatus.textContent=`Recorded: ${result.status} by ${result.reviewer}.`;loadHistory();}).catch(()=>reviewStatus.textContent='Review not recorded.');}));
}).catch(()=>document.querySelector('#flow').innerHTML='<p>Unable to load demonstration records.</p>');
</script></body></html>"""


def build_demo_payload(repository_root: Path, profile_name: str = "subject_profile") -> dict[str, Any]:
    records = {
        path.stem: load_json(path)
        for path in (repository_root / "examples" / "valid").glob("*.json")
    }
    return {
        "source": records["regulatory_source"],
        "obligation": records["obligation"],
        "profile": records[profile_name],
        "screening": screen_profile(records[profile_name], records["applicability_rule"]),
        "control": records["control"],
        "evidence": records["evidence"],
    }


def build_demo_scenarios(repository_root: Path) -> list[dict[str, Any]]:
    profiles = (
        ("consumer_claims", "Consumer-facing US AI service", "subject_profile"),
        ("internal_service", "Internal US AI analytics service", "subject_profile_internal_service"),
        ("non_us_service", "Non-US consumer AI service", "subject_profile_non_us_service"),
    )
    return [
        {"id": scenario_id, "label": label, "payload": build_demo_payload(repository_root, profile_name)}
        for scenario_id, label, profile_name in profiles
    ]


class DemoReviewQueue:
    """Local SQLite-backed review workflow for the demonstration interface."""

    def __init__(self, database: Path, schema_file: Path, scenario_ids: list[str]):
        self.database = database
        self.scenario_ids = scenario_ids
        initialize(database, schema_file)

    def snapshot(self) -> dict[str, dict[str, Any]]:
        with connect(self.database) as connection:
            current = current_review_dispositions(connection)
        return {
            scenario_id: {
                "status": current.get(scenario_id, {}).get("disposition", "pending"),
                "reviewer": current.get(scenario_id, {}).get("reviewer"),
                "rationale": current.get(scenario_id, {}).get("rationale"),
                "updated_at": current.get(scenario_id, {}).get("reviewed_at"),
            }
            for scenario_id in self.scenario_ids
        }

    def record(self, scenario_id: str, disposition: str, reviewer: str, rationale: str) -> dict[str, Any]:
        if scenario_id not in self.scenario_ids:
            raise ValueError("Unknown demonstration scenario.")
        if disposition not in {"approved", "returned", "rejected"}:
            raise ValueError("Unsupported review disposition.")
        if not reviewer.strip() or len(rationale.strip()) < 10:
            raise ValueError("Reviewer and a rationale of at least 10 characters are required.")
        with connect(self.database) as connection:
            review = append_review_disposition(
                connection,
                scenario_id=scenario_id,
                disposition=disposition,
                reviewer=reviewer.strip(),
                rationale=rationale.strip(),
            )
        return {
            "status": review["disposition"],
            "reviewer": review["reviewer"],
            "rationale": review["rationale"],
            "updated_at": review["reviewed_at"],
        }

    def history(self, scenario_id: str) -> list[dict[str, Any]]:
        if scenario_id not in self.scenario_ids:
            raise ValueError("Unknown demonstration scenario.")
        with connect(self.database) as connection:
            return review_history(connection, scenario_id)


def make_handler(repository_root: Path) -> type[BaseHTTPRequestHandler]:
    scenario_payloads = {
        scenario["id"]: scenario["payload"] for scenario in build_demo_scenarios(repository_root)
    }
    scenarios = json.dumps(build_demo_scenarios(repository_root)).encode("utf-8")
    reviews = DemoReviewQueue(
        repository_root / "demo-review.db",
        repository_root / "sql" / "schema.sql",
        list(scenario_payloads),
    )

    class DemoHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            request = urlsplit(self.path)
            if request.path == "/":
                self._respond(200, "text/html; charset=utf-8", INDEX_HTML.encode("utf-8"))
            elif request.path == "/api/demo":
                scenario = parse_qs(request.query).get("scenario", ["consumer_claims"])[0]
                response = json.dumps(
                    scenario_payloads.get(scenario, scenario_payloads["consumer_claims"])
                ).encode("utf-8")
                self._respond(200, "application/json; charset=utf-8", response)
            elif request.path == "/api/scenarios":
                self._respond(200, "application/json; charset=utf-8", scenarios)
            elif request.path == "/api/reviews":
                self._respond(200, "application/json; charset=utf-8", json.dumps(reviews.snapshot()).encode("utf-8"))
            elif request.path == "/api/review-history":
                scenario = parse_qs(request.query).get("scenario", ["consumer_claims"])[0]
                try:
                    history = reviews.history(scenario)
                except ValueError as exc:
                    self._respond(400, "application/json; charset=utf-8", json.dumps({"error": str(exc)}).encode("utf-8"))
                    return
                self._respond(200, "application/json; charset=utf-8", json.dumps(history).encode("utf-8"))
            elif request.path == "/api/export":
                scenario = parse_qs(request.query).get("scenario", ["consumer_claims"])[0]
                if scenario not in scenario_payloads:
                    self._respond(400, "application/json; charset=utf-8", b'{"error":"Unknown demonstration scenario."}')
                    return
                package = {
                    "package_type": "regulatory_intelligence_evidence_package",
                    "scenario_id": scenario,
                    "exported_at": datetime.now(UTC).isoformat(),
                    "disclaimer": "Illustrative demonstration package only. Not legal advice or a legal applicability determination.",
                    "trace": scenario_payloads[scenario],
                    "current_review": reviews.snapshot()[scenario],
                    "review_history": reviews.history(scenario),
                }
                filename = f"erir-evidence-package-{scenario}.json"
                self._respond(
                    200,
                    "application/json; charset=utf-8",
                    json.dumps(package, indent=2).encode("utf-8"),
                    {"Content-Disposition": f'attachment; filename="{filename}"'},
                )
            else:
                self._respond(404, "text/plain; charset=utf-8", b"Not found")

        def do_POST(self) -> None:
            if urlsplit(self.path).path != "/api/review":
                self._respond(404, "text/plain; charset=utf-8", b"Not found")
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                request = json.loads(self.rfile.read(length).decode("utf-8"))
                item = reviews.record(
                    request.get("scenario", ""),
                    request.get("disposition", ""),
                    request.get("reviewer", ""),
                    request.get("rationale", ""),
                )
            except (ValueError, json.JSONDecodeError) as exc:
                self._respond(400, "application/json; charset=utf-8", json.dumps({"error": str(exc)}).encode("utf-8"))
                return
            self._respond(200, "application/json; charset=utf-8", json.dumps(item).encode("utf-8"))

        def _respond(
            self, status: int, content_type: str, body: bytes, headers: dict[str, str] | None = None
        ) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            for name, value in (headers or {}).items():
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: Any) -> None:
            return

    return DemoHandler


def serve_demo(repository_root: Path, port: int) -> None:
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(repository_root))
    print(f"Demonstration interface available at http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
