import assert from "node:assert/strict";
import test from "node:test";
import { createRequire } from "node:module";
import { existsSync } from "node:fs";

const require = createRequire(import.meta.url);
const health = require("../api/v1/health.js");
const trace = require("../api/v1/trace.js");

function response() {
  return {
    headers: {}, statusCode: null, body: null,
    status(code) { this.statusCode = code; return this; },
    setHeader(name, value) { this.headers[name.toLowerCase()] = value; },
    json(body) { this.body = body; return this; },
  };
}

test("public demo health is read-only", () => {
  const res = response();
  health({ method: "GET", query: {} }, res);
  assert.equal(res.statusCode, 200);
  assert.equal(res.body.mode, "public_read_only_demo");
  assert.equal(res.body.writes, "not_available");
});

test("public API emits CORS only for the one configured ROI-EA demo origin", () => {
  const prior = process.env.DEMO_ALLOWED_ORIGIN;
  process.env.DEMO_ALLOWED_ORIGIN = "https://roi-demo.example.vercel.app";
  let res = response();
  health({ method: "GET", query: {}, headers: { origin: "https://roi-demo.example.vercel.app" } }, res);
  assert.equal(res.headers["access-control-allow-origin"], "https://roi-demo.example.vercel.app");
  assert.equal(res.headers.vary, "Origin");
  res = response();
  health({ method: "GET", query: {}, headers: { origin: "https://untrusted.example" } }, res);
  assert.equal(res.headers["access-control-allow-origin"], undefined);
  if (prior === undefined) delete process.env.DEMO_ALLOWED_ORIGIN;
  else process.env.DEMO_ALLOWED_ORIGIN = prior;
});

test("public trace returns an illustrative record chain without changing record states", () => {
  const res = response();
  trace({ method: "GET", query: { ids: "CTL-CLAIMS-001" } }, res);
  assert.equal(res.statusCode, 200);
  assert.deepEqual(res.body.records.map((record) => record.id), ["SRC-FTC-2026-001", "OBL-FTC-001", "APP-FTC-001", "CTL-CLAIMS-001", "EVD-CLAIMS-001"]);
  assert.equal(res.body.records.find((record) => record.id === "APP-FTC-001").approval_status, "draft");
  assert.equal(res.body.records.find((record) => record.id === "EVD-CLAIMS-001").assessment_result, "not_assessed");
  assert.match(res.body.disclaimer, /do not establish legal applicability/i);
});

test("public trace explicitly reports missing IDs and rejects invalid or unbounded queries", () => {
  let res = response();
  trace({ method: "GET", query: { ids: "CTL-CLAIMS-001,CTL-NOT-FOUND" } }, res);
  assert.equal(res.statusCode, 200);
  assert.deepEqual(res.body.missing_ids, ["CTL-NOT-FOUND"]);

  res = response();
  trace({ method: "GET", query: { ids: "../secrets" } }, res);
  assert.equal(res.statusCode, 400);
  assert.match(res.body.error, /invalid/i);
});

test("public demo exposes no draft-package route and rejects writes to read endpoints", () => {
  assert.equal(existsSync(new URL("../api/v1/draft-packages.js", import.meta.url)), false);
  const res = response();
  trace({ method: "POST", query: { ids: "CTL-CLAIMS-001" } }, res);
  assert.equal(res.statusCode, 405);
  assert.equal(res.headers.allow, "GET");
});
