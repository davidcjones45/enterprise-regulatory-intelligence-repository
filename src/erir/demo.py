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
:root{color-scheme:light;--navy:#12324a;--panel:#fffaf1;--teal:#176f71;--gold:#a66a25;--text:#173047;--muted:#5d6b72;--line:rgba(23,111,113,.27);--soft:#f8f1e4}
*{box-sizing:border-box}body{margin:0;font:16px/1.5 Arial,sans-serif;color:var(--text);background:linear-gradient(135deg,#f6eedc,#e7d6b7)}
main{max-width:1220px;margin:auto;padding:42px 24px 64px}.eyebrow,.stage{color:var(--gold);font-weight:800;letter-spacing:.12em;font-size:.76rem;text-transform:uppercase}
h1{font-size:clamp(2rem,5vw,3.6rem);line-height:1.04;margin:.3rem 0 1rem}h2{font-size:1.18rem;line-height:1.25;margin:.35rem 0 .65rem}p{margin:.4rem 0}.lede{color:var(--muted);max-width:800px;font-size:1.1rem}
.notice{margin:24px 0 18px;padding:14px 18px;border-left:4px solid var(--gold);background:#fff7e9;color:#314d5d;border-radius:0 8px 8px 0}
.toolbar{display:flex;gap:14px;align-items:end;justify-content:space-between;flex-wrap:wrap;margin:18px 0}.scenario-control{display:grid;gap:6px;min-width:min(360px,100%)}select,input,textarea{font:inherit;color:var(--text);background:#fff;border:1px solid #b9c8cb;border-radius:7px;padding:9px 11px}select:focus-visible,input:focus-visible,textarea:focus-visible,button:focus-visible,a:focus-visible{outline:3px solid rgba(23,111,113,.28);outline-offset:2px}
.tag,.status{display:inline-flex;align-items:center;gap:5px;padding:4px 9px;border-radius:999px;background:#dceceb;color:#15585a;font-size:.76rem;font-weight:800;line-height:1.2}.status.warning{background:#f6e6c7;color:#79501e}.status.attention{background:#f3dfdf;color:#7d3030}.status.neutral{background:#e9edf0;color:#465964}
.trace-shell{margin:22px 0 14px;padding:16px 18px;background:rgba(255,250,241,.9);border:1px solid var(--line);border-radius:12px}.trace-shell h2{margin:0 0 10px;font-size:.98rem}.trace-strip{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:7px}.trace-step{min-height:42px;padding:7px 9px;border:1px solid #becbca;border-radius:7px;background:#fffdf8;color:var(--navy);font:700 .78rem/1.25 Arial,sans-serif;cursor:pointer;text-align:center}.trace-step:hover{border-color:var(--teal);background:#f3f9f8}
.attention{display:grid;grid-template-columns:minmax(170px,.7fr) 2fr;gap:18px;align-items:start;margin:0 0 22px;padding:16px 18px;border:1px solid var(--line);border-left:4px solid var(--teal);border-radius:10px;background:#f7fbfa}.attention h2{margin:2px 0}.attention-list{display:flex;gap:8px;flex-wrap:wrap;align-items:center}.attention-note{grid-column:2;color:var(--muted);font-size:.88rem;margin-top:-8px}
.flow{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;align-items:start;margin-top:22px}.card{background:rgba(255,250,241,.97);border:1px solid var(--line);border-radius:12px;padding:20px;color:inherit;text-align:left;cursor:pointer;transition:transform .15s,border-color .15s,background .15s;min-width:0}.card:hover,.card:focus-visible{transform:translateY(-2px);border-color:var(--teal);background:#fffdf8}.card.active{border-color:var(--gold);background:#fff1d9;box-shadow:0 0 24px rgba(166,106,37,.12)}.card-header{display:flex;justify-content:space-between;gap:10px;align-items:start}.card h2{font-size:1.25rem;margin:.35rem 0 .55rem}.card-desc{color:#314d5d}.card-meta{display:flex;gap:7px;flex-wrap:wrap;margin:.7rem 0 .55rem}.record-id{display:block;margin-top:.8rem;padding-top:.65rem;border-top:1px solid rgba(23,111,113,.18);color:#285c76;font:700 .78rem/1.3 ui-monospace,SFMono-Regular,Consolas,monospace}.decision{border-color:rgba(166,106,37,.58)}
.detail{margin-top:22px;padding:22px;min-height:170px;border-radius:12px;border:1px solid rgba(23,111,113,.35);background:#fffaf1}.detail h2{color:var(--teal)}.detail dl{display:grid;grid-template-columns:minmax(160px,220px) 1fr;gap:9px 18px}.detail dt{color:var(--gold);font-weight:800}.detail dd{margin:0;color:#314d5d;overflow-wrap:anywhere}.canonical{display:inline-block;margin-left:7px;color:#66757c;font:600 .73rem/1.2 ui-monospace,SFMono-Regular,Consolas,monospace}
.review-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.review-grid label{display:grid;gap:6px}.review-grid .full{grid-column:1/-1}.actions{display:flex;gap:9px;flex-wrap:wrap;margin-top:14px}.actions button{padding:9px 12px;border-radius:7px;border:1px solid var(--teal);background:var(--teal);color:#fff;font-weight:800;cursor:pointer}.actions button:nth-child(n+2){background:#fff;color:var(--navy);border-color:#b9c8cb}.footer{color:var(--muted);margin-top:26px;font-size:.88rem}
@media(max-width:900px){.flow{grid-template-columns:repeat(2,minmax(0,1fr))}.trace-strip{grid-template-columns:repeat(3,minmax(0,1fr))}.attention{grid-template-columns:1fr}.attention-note{grid-column:1;margin-top:0}}
@media(max-width:620px){main{padding:28px 16px 48px}.flow,.review-grid{grid-template-columns:1fr}.trace-strip{grid-template-columns:repeat(2,minmax(0,1fr))}.detail dl{grid-template-columns:1fr}.detail dd{margin-bottom:7px}}
@media(prefers-reduced-motion:reduce){*{transition:none!important;scroll-behavior:auto!important}.card:hover{transform:none}}
</style></head><body><main>
<div class="eyebrow">AI AT HUMAN SCALE · DEMONSTRATION</div><h1>Traceable Regulatory Intelligence</h1>
<p class="lede">A read-only view of the operating path from an authoritative source to a human-reviewed applicability screen, mapped control, and supporting evidence.</p>
<div class="notice"><strong>Demonstration boundary:</strong> illustrative records only. This is not legal advice, does not determine legal applicability or compliance, and requires authoritative-source verification and accountable human review before reliance.</div>
<div class="toolbar"><label class="scenario-control"><span class="eyebrow">Illustrative scenario</span><select id="scenario"><option value="consumer_claims">Consumer-facing US AI service</option><option value="internal_service">Internal US AI analytics service</option><option value="non_us_service">Non-US consumer AI service</option></select></label><a class="tag" id="export-package" href="#">Download evidence package</a></div>
<section class="trace-shell" aria-label="Regulatory intelligence trace"><h2>Source-to-evidence trace</h2><div class="trace-strip" id="trace-strip"></div></section>
<section class="attention" id="attention" aria-live="polite"><div><div class="stage">Repository attention</div><h2>Current review state</h2></div><div class="attention-list" id="attention-list"></div><p class="attention-note">These indicators summarize recorded state only. They do not establish legal applicability, compliance, control effectiveness, or approval.</p></section>
<section class="flow" id="flow" aria-live="polite"></section>
<section class="detail" id="detail" aria-live="polite"><h2>Select a trace stage</h2><p>Choose a card or trace step to inspect the complete underlying record and its reasoning boundary.</p></section>
<section class="detail" id="review"><div class="stage">Governed review queue</div><h2>Record a reviewer disposition</h2><p id="review-status">Loading current queue status…</p><div class="review-grid"><label>Reviewer<input id="reviewer" placeholder="Name or role"></label><label class="full">Rationale<textarea id="rationale" rows="3" placeholder="Why is this disposition appropriate?"></textarea></label></div><div class="actions"><button data-action="approved">Approve screening</button><button data-action="returned">Return for clarification</button><button data-action="rejected">Reject screening</button></div><p class="footer">Demonstration state is held only while this local server runs. A production queue would retain authenticated reviewer identity and append-only events.</p></section>
<section class="detail"><div class="stage">Review history</div><h2>Reconstructable disposition trail</h2><div id="review-history">Loading review events…</div></section>
<p class="footer">The repository separates source facts, normalized obligations, applicability reasoning, controls, and evidence so a reviewer can reconstruct each decision.</p>
</main><script>
const esc=v=>String(v??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const humanize=v=>String(v??'').trim().replaceAll('_',' ').replace(/\b\w/g,c=>c.toUpperCase());
const status=(value,tone='neutral',symbol='○')=>`<span class="status ${tone}"><span aria-hidden="true">${symbol}</span>${esc(humanize(value))}</span>`;
const recordId=record=>record?.id||record?.rule_id||record?.screening_id||'';
const canonicalValue=value=>{
 if(Array.isArray(value)||value&&typeof value==='object')return esc(JSON.stringify(value));
 const raw=String(value??'—');
 return raw.includes('_')?`${esc(humanize(raw))}<span class="canonical">[${esc(raw)}]</span>`:esc(raw);
};
const card=(stage,title,description,statuses,id,cls='')=>`<article class="card ${cls}"><div class="card-header"><div class="stage">${esc(stage)}</div></div><h2>${esc(title)}</h2><div class="card-meta">${statuses.join('')}</div><p class="card-desc">${esc(description)}</p>${id?`<code class="record-id">${esc(id)}</code>`:''}</article>`;
const selected=new URLSearchParams(location.search).get('scenario')||'consumer_claims';
document.querySelector('#scenario').value=selected;
document.querySelector('#scenario').addEventListener('change',event=>location.search=`?scenario=${event.target.value}`);
document.querySelector('#export-package').href=`/api/export?scenario=${selected}`;
fetch(`/api/demo?scenario=${selected}`).then(r=>r.json()).then(d=>{
 const source=d.source,obligation=d.obligation,profile=d.profile,control=d.control,evidence=d.evidence,screen=d.screening;
 const stages=[source,obligation,profile,screen,control,evidence];
 const stageDefs=[
  {label:'Source',title:'Authoritative source record',description:`${source.title}. ${source.authority}.`,statuses:[status(source.legal_status,'warning','△'),status(source.review_status,source.review_status==='unreviewed'?'attention':'neutral',source.review_status==='unreviewed'?'!':'○')],id:source.id},
  {label:'Obligation',title:'Normalized obligation',description:obligation.normalized_text,statuses:[status(obligation.binding_status,'warning','△'),status(obligation.review_status,'neutral','○')],id:obligation.id},
  {label:'Profile',title:'Subject profile',description:`${profile.title}. Owner: ${profile.profile_owner}.`,statuses:[status('Facts recorded','neutral','○')],id:profile.id},
  {label:'Screening',title:'Applicability screen',description:screen.rationale,statuses:[status(screen.screening_decision,screen.screening_decision==='potentially_applies'?'warning':'neutral','△'),status(screen.human_review_required?'Human review required':'Review state recorded',screen.human_review_required?'attention':'neutral',screen.human_review_required?'!':'○')],id:recordId(screen),cls:'decision'},
  {label:'Control',title:control.title,description:control.objective,statuses:[status(control.status,'neutral','○'),status(control.control_type,'neutral','○')],id:control.id},
  {label:'Evidence',title:'Validation evidence',description:evidence.description,statuses:[status(evidence.evidence_type,'neutral','○'),status(evidence.assessment_result,evidence.assessment_result==='not_assessed'?'attention':'neutral',evidence.assessment_result==='not_assessed'?'!':'○')],id:evidence.id}
 ];
 document.querySelector('#trace-strip').innerHTML=stageDefs.map((item,index)=>`<button type="button" class="trace-step" data-stage-index="${index}">${index+1}. ${esc(item.label)}</button>`).join('');
 document.querySelector('#flow').innerHTML=stageDefs.map((item,index)=>card(`${index+1} · ${item.label}`,item.title,item.description,item.statuses,item.id,item.cls||'')).join('');
 const attention=[];
 if(source.review_status==='unreviewed')attention.push(status('Source unreviewed','attention','!'));
 if(screen.human_review_required)attention.push(status('Human review required','attention','!'));
 if(evidence.assessment_result==='not_assessed')attention.push(status('Evidence not assessed','attention','!'));
 if(!attention.length)attention.push(status('No flagged demo-state exceptions','neutral','○'));
 document.querySelector('#attention-list').innerHTML=attention.join('');
 const show=(record,cardNode)=>{
  document.querySelectorAll('.card').forEach(c=>c.classList.remove('active'));
  cardNode.classList.add('active');
  document.querySelector('#detail').innerHTML=`<div class="stage">Record detail</div><h2>${esc(cardNode.querySelector('h2').textContent)}</h2><dl>${Object.entries(record).map(([k,v])=>`<dt>${esc(humanize(k))}</dt><dd>${canonicalValue(v)}</dd>`).join('')}</dl>`;
  cardNode.scrollIntoView({block:'nearest',behavior:'smooth'});
 };
 const cards=[...document.querySelectorAll('.card')];
 cards.forEach((cardNode,index)=>{cardNode.tabIndex=0;cardNode.setAttribute('role','button');cardNode.addEventListener('click',()=>show(stages[index],cardNode));cardNode.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();show(stages[index],cardNode);}});});
 document.querySelectorAll('.trace-step').forEach(button=>button.addEventListener('click',()=>cards[Number(button.dataset.stageIndex)]?.click()));
 const reviewStatus=document.querySelector('#review-status');
 const loadReview=()=>fetch('/api/reviews').then(r=>r.json()).then(reviews=>{const item=reviews[selected];reviewStatus.textContent=`Current status: ${humanize(item.status)}. ${item.reviewer?`Last reviewer: ${item.reviewer}.`:''} ${item.rationale?`Rationale: ${item.rationale}`:''}`;});
 const historyPanel=document.querySelector('#review-history');
 const loadHistory=()=>fetch(`/api/review-history?scenario=${selected}`).then(r=>r.json()).then(events=>{historyPanel.innerHTML=events.length?events.map(event=>`<p>${status(event.disposition,'neutral','○')} ${esc(event.reviewer)} · ${esc(event.reviewed_at)}<br>${esc(event.rationale)}</p>`).join(''):'<p>No reviewer disposition has been recorded for this scenario.</p>';});
 loadReview();loadHistory();
 document.querySelectorAll('#review button').forEach(button=>button.addEventListener('click',()=>{fetch('/api/review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scenario:selected,disposition:button.dataset.action,reviewer:document.querySelector('#reviewer').value,rationale:document.querySelector('#rationale').value})}).then(async response=>{const result=await response.json();if(!response.ok){reviewStatus.textContent=`Review not recorded: ${result.error}`;return;}reviewStatus.textContent=`Recorded: ${humanize(result.status)} by ${result.reviewer}.`;loadHistory();}).catch(()=>reviewStatus.textContent='Review not recorded.');}));
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
