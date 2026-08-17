#!/bin/sh
set -eu

python -m research.legal_audit \
  --validation-dir research/validation \
  --output /app/results/publication/legal-audit.json
python -m research.regulatory_validation "$@"
python -m research.reliability_report \
  --report /app/results/publication/report.json \
  --output /app/results/publication/calibration-reliability.svg
