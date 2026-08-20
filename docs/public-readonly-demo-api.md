# Public Read-Only ERIR Demo API v0.1

This Vercel deployment is a deliberately narrow public reference API for the ROI-Driven Enterprise Architect integrated demo. It packages the existing illustrative records in `examples/valid/` at build time; it does not access a working tree, a ledger, or a source system at runtime.

## Endpoints

- `GET /api/v1/health` returns the contract version and confirms that writes are unavailable.
- `GET /api/v1/trace?ids=<comma-separated IDs>` accepts at most 12 bounded ERIR identifiers, returns directly requested records plus the small connected illustrative trace, and reports unavailable identifiers in `missing_ids`.

Only the five existing illustrative records used by the ROI-EA Northstar reference path are packaged. Record states are returned without reinterpretation. In particular, a proposed source, draft applicability assessment, designed control, or not-assessed evidence remains in that state.

There is no `POST /api/v1/draft-packages` route, no mutation route, no filesystem route, no arbitrary record lookup, no authentication, and no customer storage. To permit the separately deployed ROI-EA browser app to call this API, set `DEMO_ALLOWED_ORIGIN` in Vercel to that one exact HTTPS ROI-EA deployment origin. The API emits `Access-Control-Allow-Origin` only when the request origin matches that exact value; it never emits wildcard CORS.

## Local verification

```powershell
node --test tests/test_public_demo_api.mjs
python -m pytest -q
```

Deploy this branch as a separate Vercel project. Deploy ROI-EA first to obtain its HTTPS origin, then configure `DEMO_ALLOWED_ORIGIN` for this project. Configure ROI-EA with the ERIR HTTPS origin using `?erirApi=https://<erir-demo-host>` or a deployment-specific `demo-config.js` value. This is an illustrative read-only reference service, not legal advice, compliance certification, production authorization, or a comprehensive regulatory repository.
