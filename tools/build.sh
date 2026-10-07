#!/usr/bin/env bash
# Build and validate the L1 knowledge graph.
#
#   SMART_KG=../smart-kg tools/build.sh
#
# 1. checks the committed English text still matches the PDF (needs pdfplumber)
# 2. builds build/measles.l1.kg.json, failing on any non-verbatim quote
# 2b. L1 coverage QA report (REQ-03), failing on any unaccounted normative sentence;
#     REQUIRE_SIGNOFF=1 also fails while an exclusion awaits sign-off
# 3. tier 2: smart-kg tools/validate.mjs (ontology licensing)
# 4. tier 1: smart-kg shapes/recommendation-graph.schema.json via ajv, if npx is available
set -euo pipefail
cd "$(dirname "$0")/.."
SMART_KG="${SMART_KG:-../smart-kg}"
OUT=build/measles.l1.kg.json

python3 -I tools/extract_text.py l1/source/WER9217.pdf | diff -q - l1/source/WER9217.en.txt \
  || { echo "l1/source/WER9217.en.txt is stale: re-run tools/extract_text.py" >&2; exit 1; }
python3 -I tools/build_l1.py l1/measles-position-paper-2017.l1.yaml "$OUT"
python3 -I tools/coverage.py l1/measles-position-paper-2017.l1.yaml l1/coverage-exclusions.yaml \
  build/coverage-report.md ${REQUIRE_SIGNOFF:+--require-signoff}
node "$SMART_KG/tools/validate.mjs" "$PWD/$OUT"
if command -v npx >/dev/null; then
  npx --yes -p ajv-cli@5 -p ajv-formats@2 ajv validate --spec=draft2020 -c ajv-formats \
    -s "$SMART_KG/shapes/recommendation-graph.schema.json" -d "$OUT"
fi
