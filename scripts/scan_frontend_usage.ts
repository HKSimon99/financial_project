#!/usr/bin/env node
/**
 * Recursively scans TS/JS source files and records which fields are referenced.
 * Writes to {os.tmpdir()}/frontend_usage.csv with `path,field` columns.
 */

// Declare require/process for compilation without @types/node.
declare const require: any;
declare const process: any;

const fs = require("fs");
const path = require("path");
const os = require("os");

const roots = process.argv.slice(2);
if (roots.length === 0) {
  roots.push("apps", "packages");
}

const seen = new Set<string>();

async function scanFile(filePath: string) {
  const content = await fs.promises.readFile(filePath, "utf8");
  const regexes = [
    /\.([A-Za-z_][A-Za-z0-9_]*)/g, // dot access e.g. obj.field
    /\[['"]([A-Za-z_][A-Za-z0-9_]*)['"]\]/g, // bracket access e.g. obj['field']
  ];
  for (const re of regexes) {
    let match: RegExpExecArray | null;
    while ((match = re.exec(content)) !== null) {
      const key = `${filePath},${match[1]}`;
      seen.add(key);
    }
  }
}

async function walk(dir: string) {
  const entries = await fs.promises.readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === "node_modules" || entry.name.startsWith(".")) continue;
      await walk(fullPath);
    } else if (/\.(ts|tsx|js|jsx)$/.test(entry.name)) {
      await scanFile(fullPath);
    }
  }
}

async function main() {
  for (const dir of roots) {
    if (fs.existsSync(dir)) {
      await walk(dir);
    }
  }
  const lines = ["path,field", ...Array.from(seen)];
  const outFile = path.join(os.tmpdir(), "frontend_usage.csv");
  await fs.promises.writeFile(outFile, lines.join("\n") + "\n");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
