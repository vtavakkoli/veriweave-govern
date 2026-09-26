# IEEE Access paper result snapshot

This directory records the aggregate values reported in the IEEE Access
submission:

**VeriWeave Govern: Evidence-Gated Deterministic Runtime Governance for
Enterprise AI Agents**

The machine-readable summary is in
[`paper-results.json`](paper-results.json).

## Provenance

The values in this directory are a **reporting manifest transcribed from the
submission manuscript**. They are not a replacement for raw predictions,
annotation workbooks, benchmark logs, or generated service reports.

The older file
[`../research-v1/reference-metrics.json`](../research-v1/reference-metrics.json)
is intentionally preserved because it belongs to a distinct earlier synthetic
reference run. In particular, its calibration values should not be treated as
the exact Table 8 values of the IEEE Access submission.

The paper-reported GovernBench calibration profile is:

| Metric | Paper value |
|---|---:|
| AUROC | 0.9840 |
| AUPRC | 0.9896 |
| Brier score | 0.1226 |
| Expected Calibration Error | 0.2253 |
| Selected threshold | 0.7600 |

Fresh reruns can vary if configuration, software, dependency versions, or
generated benchmark realizations differ. For reproducibility, preserve the Git
commit, container/tool versions, policy hashes, seeds, source-snapshot date and
raw outputs used for any new run.
