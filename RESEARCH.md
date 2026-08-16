# VeriWeave Govern — Scientific Governance Benchmark Edition

The research extension evaluates deterministic runtime AI governance rather than adding an LLM to the authorization path.

## Included

- GovernBench-v1: five domains, adversarial and temporal cases, 2,000 cases/seed.
- 30-seed experiments with bootstrap 95% confidence intervals.
- learned evidence calibration instead of relying only on fixed heuristic weights.
- RBAC, ABAC, language-style proxy, VeriWeave, and external OPA/Cedar baseline contracts.
- false-allow/deny/review, macro-F1, GASR, Brier, ECE, AUROC and AUPRC.
- six ablations, counterfactuals, governance certificates and temporal replay.
- human-evaluation protocol and annotation scorer.
- EU AI Act, NIST AI RMF and ISO/IEC 42001 high-level technical crosswalks.
- consulting assessment workflow and VGRI readiness indicator.

Run the reference experiment:

```bash
make research
```

The committed `results/research-v1/` reference run is synthetic/oracle-labelled and is intentionally marked as such. It demonstrates reproducibility and experimental infrastructure; it is not a substitute for independently annotated real organizational cases.
