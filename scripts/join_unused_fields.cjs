#!/usr/bin/env node

const fs = require("fs");
const os = require("os");
const path = require("path");

const TMP = os.tmpdir();

function readCsv(file) {
  if (!fs.existsSync(file)) return [];
  const raw = fs.readFileSync(file, "utf8").trim();
  if (!raw) return [];
  const lines = raw.split(/\r?\n/);
  if (lines.length && /^path,field$/i.test(lines[0])) lines.shift();
  return lines.filter(Boolean).map((line) => {
    const [p, f] = line.split(",");
    return { path: p, field: f };
  });
}

const apiFields = readCsv(path.join(TMP, "api_fields.csv"));
const frontendUsage = readCsv(path.join(TMP, "frontend_usage.csv"));

const used = new Set(frontendUsage.map((r) => r.field));
const unused = apiFields.filter((r) => !used.has(r.field));

const outLines = ["path,field", ...unused.map((r) => `${r.path},${r.field}`)];
const outFile = path.join(TMP, "unused.csv");
fs.writeFileSync(outFile, outLines.join("\n") + "\n");

console.log(`${outFile} written with ${unused.length} unused fields`);
