#!/usr/bin/env bash
# Runs the API field usage analysis pipeline with robust paths.
set -euo pipefail

TMPDIR="$(node -e "console.log(require('os').tmpdir())")"

# Compile TS -> JS into OS temp
pnpm exec tsc scripts/scan_frontend_usage.ts \
  --target ES2019 --module commonjs --lib ES2019,DOM \
  --skipLibCheck --outDir "$TMPDIR" >"$TMPDIR/scan_frontend_usage.log"

# Find the emitted JS (tsc may or may not create a 'scripts/' subfolder)
OUT_A="$TMPDIR/scripts/scan_frontend_usage.js"
OUT_B="$TMPDIR/scan_frontend_usage.js"

if [ -f "$OUT_A" ]; then
  node "$OUT_A"
elif [ -f "$OUT_B" ]; then
  node "$OUT_B"
else
  echo "Could not find compiled scanner in:"
  echo "  $OUT_A"
  echo "  $OUT_B"
  echo "Compilation log:"
  cat "$TMPDIR/scan_frontend_usage.log" || true
  exit 1
fi

# Join API fields with frontend usage
node scripts/join_unused_fields.cjs

echo "Report written to $TMPDIR/unused.csv"
