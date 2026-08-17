#!/bin/sh
set -eu

python -m research.legal_audit \
  --validation-dir research/validation \
  --output /app/results/publication/legal-audit.json
python -m research.regulatory_validation "$@"
python -m research.publication_statistics \
  --predictions /app/results/publication/predictions.csv \
  --output /app/results/publication/statistics.json \
  --samples "${PUBLICATION_BOOTSTRAP_SAMPLES:-10000}" \
  --seed "${PUBLICATION_BOOTSTRAP_SEED:-20260817}"
python -m research.reliability_report \
  --report /app/results/publication/report.json \
  --output /app/results/publication/calibration-reliability.svg
