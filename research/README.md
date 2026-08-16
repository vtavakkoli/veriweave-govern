# GovernBench research layer

`research/` is separated from the production authorization path. It evaluates scientific claims without making runtime authorization depend on stochastic research code.

Implemented: GovernBench-v1 across five domains; 2,000 cases/seed; 30 independent seeds; learned evidence calibration; RBAC/ABAC/language-style/VeriWeave baselines; OPA/Cedar external-baseline contracts; accuracy, macro-F1, false-allow/deny/review, GASR, Brier, ECE, AUROC/AUPRC; six ablations; counterfactual governance certificates; temporal replay; synthetic scalability profiling; and a human-annotation scorer.

Run:

```bash
python -m research.experiments --seeds 30 --cases 2000 --output results/research-v1
```

Fast development run:

```bash
python -m research.experiments --seeds 3 --cases 300 --output results/research-quick
```

**Scientific boundary:** GovernBench-v1 is synthetic and oracle-labelled. It is appropriate for reproducibility, regression, ablation, attack testing, and methodology development. It must not be represented as human-validated real-world effectiveness. Use `docs/HUMAN_EVALUATION.md` for the external-validation stage.
