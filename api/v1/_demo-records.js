"use strict";

// This public-demo snapshot is packaged from ERIR's versioned illustrative
// example records at build time. It is deliberately read-only and does not
// turn any record status into a legal, compliance, evidence-acceptance, or
// authorization conclusion.
const records = [
  require("../../examples/valid/regulatory_source.json"),
  require("../../examples/valid/obligation.json"),
  require("../../examples/valid/applicability_assessment.json"),
  require("../../examples/valid/control.json"),
  require("../../examples/valid/evidence.json"),
];

const MAX_IDS = 12;
const ID_PATTERN = /^[A-Z][A-Z0-9_-]{2,63}$/;

function json(response, status, body) {
  response.status(status).setHeader("Content-Type", "application/json; charset=utf-8");
  response.setHeader("Cache-Control", "public, max-age=300");
  return response.json(body);
}

function allowConfiguredOrigin(request, response) {
  const configured = process.env.DEMO_ALLOWED_ORIGIN;
  const origin = request.headers?.origin;
  if (configured && origin === configured) {
    response.setHeader("Access-Control-Allow-Origin", configured);
    response.setHeader("Vary", "Origin");
  }
}

function onlyGet(request, response) {
  if (request.method === "GET") return true;
  response.setHeader("Allow", "GET");
  json(response, 405, { error: "Method not allowed. This public ERIR demo API is read-only." });
  return false;
}

function parseIds(value) {
  if (typeof value !== "string" || !value.trim()) {
    return { error: "Query parameter 'ids' is required." };
  }
  if (value.length > 1024) return { error: "Query parameter 'ids' is too long." };
  const ids = [...new Set(value.split(",").map((item) => item.trim()).filter(Boolean))];
  if (!ids.length) return { error: "At least one ERIR identifier is required." };
  if (ids.length > MAX_IDS) return { error: `At most ${MAX_IDS} ERIR identifiers may be requested.` };
  if (ids.some((id) => !ID_PATTERN.test(id))) return { error: "One or more ERIR identifiers are invalid." };
  return { ids };
}

function trace(ids) {
  const byId = new Map(records.map((record) => [record.id, record]));
  const selected = new Map(ids.filter((id) => byId.has(id)).map((id) => [id, byId.get(id)]));
  const add = (id) => { if (byId.has(id)) selected.set(id, byId.get(id)); };

  let changed = true;
  while (changed) {
    const before = selected.size;
    for (const record of [...selected.values()]) {
      if (record.record_type === "obligation") add(record.source_id);
      if (record.record_type === "applicability_assessment") add(record.obligation_id);
      if (record.record_type === "control") record.obligation_ids.forEach(add);
      if (record.record_type === "evidence") add(record.control_id);
    }
    for (const record of records) {
      if (record.source_id && selected.has(record.source_id)) add(record.id);
      if (record.obligation_id && selected.has(record.obligation_id)) add(record.id);
      if (record.control_id && selected.has(record.control_id)) add(record.id);
      if (record.obligation_ids?.some((id) => selected.has(id))) add(record.id);
    }
    changed = selected.size !== before;
  }

  return {
    contract_version: "1.0",
    mode: "public_read_only_demo",
    disclaimer: "Illustrative ERIR reference records only. Record identifiers and statuses do not establish legal applicability, compliance, effective controls, accepted evidence, or organizational authorization.",
    records: records.filter((record) => selected.has(record.id)),
    missing_ids: ids.filter((id) => !byId.has(id)),
  };
}

module.exports = { MAX_IDS, allowConfiguredOrigin, json, onlyGet, parseIds, trace };
