"use strict";

const { allowConfiguredOrigin, json, onlyGet, parseIds, trace } = require("./_demo-records");

module.exports = (request, response) => {
  allowConfiguredOrigin(request, response);
  if (!onlyGet(request, response)) return;
  const parsed = parseIds(request.query?.ids);
  if (parsed.error) return json(response, 400, { error: parsed.error });
  return json(response, 200, trace(parsed.ids));
};
