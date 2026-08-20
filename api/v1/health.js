"use strict";

const { allowConfiguredOrigin, json, onlyGet } = require("./_demo-records");

module.exports = (request, response) => {
  allowConfiguredOrigin(request, response);
  if (!onlyGet(request, response)) return;
  return json(response, 200, {
    ok: true,
    contract_version: "1.0",
    mode: "public_read_only_demo",
    writes: "not_available",
  });
};
