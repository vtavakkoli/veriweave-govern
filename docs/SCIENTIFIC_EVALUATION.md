# Scientific evaluation protocol

## Research question

Can deterministic runtime governance with calibrated evidence gates, deny
precedence, human escalation, temporal replay and tamper-evident audit reduce
unsafe authorization decisions without relying on an LLM for the final
decision?

## Hypotheses

- **H1 Safety:** lower false-allow rate than RBAC/ABAC-style baselines.
- **H2 Robustness:** lower Governance Attack Success Rate (GASR) under
  adversarial evidence/actions.
- **H3 Evidence:** evidence trust is measurable with Brier, ECE, AUROC, AUPRC
  and a reliability curve rather than only fixed heuristic weights.
- **H4 Replay:** immutable versioned inputs reproduce historical decisions.
- **H5 External policy comparison:** the tri-state governance model can be
  compared reproducibly with independently executed OPA/Rego and Cedar policy
  engines.
- **H6 Human complementarity:** human + VeriWeave is the target operating
  model; this project does not claim to replace accountable human governance.

## GovernBench synthetic experiment

Default experiment: **30 independent seeds × 2,000 cases/seed** across public
administration, healthcare, financial services, software-engineering agents and
enterprise-office agents. Categories include low-risk allow, missing/weak
evidence, protected-data exfiltration, high-impact review, policy conflict, OOD
actions, adversarial evidence and temporal policy evolution.

Adversarial families include stale evidence, forged-signature metadata, citation
laundering, evidence flooding, contradictory evidence, policy-version downgrade
and tool substitution. GASR is unsafe allows divided by attacked cases whose
oracle decision is review/deny.

Aggregate metrics use bootstrap 95% confidence intervals across seed-level
results. False-allow rate, GASR and calibration are first-class safety metrics.

The built-in deterministic language-style proxy is **not an actual LLM result**.

## EU/Austria regulation-grounded validation

The publication benchmark is separate from synthetic training and contains 150
curated cases across three domains. Its official-source registry is snapshot
versioned and records legal applicability dates so current and future-effective
Austrian requirements are not silently mixed.

The case bank is stored as six reviewable 25-case CSV partitions. It contains
provisional researcher hypotheses. Two blind annotators receive worksheets that
omit provisional labels/rationales and system predictions. Report Cohen's kappa
before adjudication. Publish final performance against this set only after all
150 adjudicated labels are complete.

The publication profile executes:

- RBAC;
- ABAC;
- VeriWeave with a calibrator trained on a separate synthetic seed;
- OPA/Rego 1.17.0;
- Cedar 4.11.0;
- an actual Ollama model, default `gemma3n:e2b`.

OPA and Cedar are deliberately coarse structured-policy baselines; their exact
policies are versioned under `research/policy_baselines/`. The LLM receives case
facts and official-source summaries, but never provisional labels or VeriWeave
predictions.

## Calibration interpretation

The evidence model exposes a score that is used for thresholded trust
acceptance. The repository reports Brier score, ECE, AUROC/AUPRC and reliability
bins. Do not describe the score as a perfectly calibrated real-world
probability without separate empirical calibration data.

## Reproduction

```bash
make research
make publication
```

Capture the Git commit, Docker image versions, OPA/Cedar versions, Ollama
version/model digest, raw reports and completed annotation/adjudication files for
the paper artifact.
