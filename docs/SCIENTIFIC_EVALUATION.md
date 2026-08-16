# Scientific evaluation protocol

## Research question

Can deterministic runtime governance with calibrated evidence gates, deny precedence, human escalation, temporal replay, and tamper-evident audit reduce unsafe authorization decisions without relying on an LLM for the final decision?

## Hypotheses

- **H1 Safety:** lower false-allow rate than RBAC/ABAC-style baselines.
- **H2 Robustness:** lower Governance Attack Success Rate (GASR) under adversarial evidence/actions.
- **H3 Evidence:** learned calibration is measurable with Brier, ECE, AUROC and AUPRC instead of relying only on fixed hand-tuned weights.
- **H4 Replay:** immutable versioned inputs reproduce historical decisions.
- **H5 Human complementarity:** human + VeriWeave is the target operating model; this project does not claim to replace accountable human governance.

Default experiment: **30 independent seeds × 2,000 cases/seed** across public administration, healthcare, financial services, software-engineering agents, and enterprise-office agents. Categories include low-risk allow, missing/weak evidence, protected-data exfiltration, high-impact review, policy conflict, OOD actions, adversarial evidence, and temporal policy evolution.

Adversarial families: stale evidence, forged-signature metadata, citation laundering, evidence flooding, contradictory evidence, policy-version downgrade, and tool substitution. GASR is unsafe allows divided by attacked cases whose oracle decision is review/deny.

Aggregate metrics use bootstrap 95% confidence intervals across seed-level results. Treat false-allow rate, GASR, and calibration as first-class safety metrics rather than optimizing accuracy alone.

Built-in baselines: RBAC, ABAC, deterministic language-style proxy, VeriWeave. The proxy is **not an actual LLM result**. OPA and Cedar numbers may only be published when their official engines, exact versions, policies, commands, and raw run artifacts are captured.

Synthetic results are not enough for external-validity claims. A paper should add independently annotated organizational cases under `HUMAN_EVALUATION.md`, report inter-rater agreement, and keep those results separate from the synthetic benchmark.
