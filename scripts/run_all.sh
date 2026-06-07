#!/usr/bin/env bash
# Run the full VNVC → FHIR mapping pipeline (docs folder only)
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Extracting mapping from docs/*.xlsx"
python3 scripts/extract_mapping.py

echo "==> Generating interactive HTML report"
python3 scripts/visualize_mapping.py

echo ""
echo "Outputs:"
echo "  output/vnvc_fhir_model.json       — structured data extracted from docs/"
echo "  output/vnvc_mapping_report.html — interactive report (open in browser)"
