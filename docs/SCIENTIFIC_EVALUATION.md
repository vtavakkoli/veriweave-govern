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
- **H6 Real LLM comparison:** regulation-grounded cases can be evaluated against
  an actually invoked Ollama model rather than a deterministic language proxy.
- **H7 Human complementarity:** human + VeriWeave is the target operating
  model; this project does not claim to replace accountable human governance.
- **H8 External validity:** performance on the regulation-grounded EU/Austria
  set remains strong when final evaluation uses independently annotated and
  adjudicated labels rather than generator/oracle labels.

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

GovernBench reports RBAC, ABAC and VeriWeave. The former deterministic
`llm-proxy` has been removed from this stage so it cannot be mistaken for an
actual LLM result. Real LLM comparison is isolated in publication validation.

## EU/Austria regulation-grounded validation

The publication benchmark is separate from synthetic training and contains 150
curated cases across three domains. Its official-source registry is snapshot
versioned at **2026-08-17** and records legal applicability dates so current and
future-effective requirements are not silently mixed.

The source snapshot incorporates Regulation (EU) 2026/1744. Consequently,
Article 6(2)/Annex III Chapter III Sections 1–3 cases are evaluated only after
the amended **2 December 2027** application date and are explicitly marked as
future-effective at the 2026-08-17 snapshot. The source registry also reflects
the amended Article 4 AI-literacy wording. Current GDPR and Austrian-law cases
remain separate from those temporal AI Act scenarios.

Before evaluation, `research.legal_audit` checks the case partitions, label
balance, unique IDs, primary-law source provenance, source verification and
application dates, and each case's temporal consistency. The publication run
fails closed on a hard audit error.

The case bank is stored as six reviewable 25-case CSV partitions. It contains
provisional researcher hypotheses. Two blind annotators receive worksheets that
omit provisional labels/rationales, prohibition metadata and system predictions.
Report final Cohen's kappa before adjudication only after both independent
worksheets are complete. Publish final performance against this set only after
all 150 adjudicated labels are complete.

The publication profile executes:

- RBAC;
- ABAC;
- VeriWeave with a calibrator trained on a separate synthetic seed;
- OPA/Rego 1.17.0;
- Cedar 4.12.0;
- a real Ollama model, default `gemma4:31b-cloud`.

OPA and Cedar are deliberately coarse structured-policy baselines; their exact
policies are versioned under `research/policy_baselines/`. The LLM receives case
facts and official-source summaries, but never provisional/adjudicated labels,
provisional rationales, prohibition metadata or VeriWeave predictions.

The Docker pipeline reaches the host Ollama API through
`http://host.docker.internal:11434`. Before any experimental stage, preflight
performs a real `/api/chat` invocation using `OLLAMA_MODEL`. The pipeline does
not silently substitute a proxy or another model if that call fails.

## Publication statistical analysis

`research.publication_statistics` reads the frozen row-level predictions and
produces:

- case-level bootstrap 95% confidence intervals for accuracy, macro-F1 and
  false-allow rate;
- paired bootstrap 95% confidence intervals for the accuracy difference between
  VeriWeave and each comparator;
- exact two-sided McNemar tests on paired correctness outcomes;
- Holm-Bonferroni adjusted p-values across baseline comparisons;
- per-domain metrics.

The default is **10,000 bootstrap resamples** with fixed seed `20260817`. This
resampling is intentionally deterministic for artifact reproducibility.

When adjudicated labels are incomplete, these statistics are automatically
marked `provisional-regulation-grounded` and are development diagnostics only.
The final paper should use the `human-adjudicated` statistics generated after
all 150 adjudications exist. Report effect sizes/confidence intervals together
with p-values rather than relying on significance alone.

## Calibration interpretation

The evidence model exposes a score that is used for thresholded trust
acceptance. The repository reports Brier score, ECE, AUROC/AUPRC, reliability
bins and a publication-ready SVG reliability diagram. Do not describe the score
as a perfectly calibrated real-world probability without separate empirical
calibration data.

## Service-level performance

The engineering smoke benchmark is complemented by a Docker service load matrix.
By default it executes at least 10,000 requests per concurrency level for
concurrency 1, 4, 16 and 32, producing at least 40,000 real API requests. This is
reported separately from GovernBench's in-process scalability profile.

Increase `LOAD_MATRIX_REQUESTS_PER_LEVEL` to 25,000 for an approximately
100,000-request publication run.

## Reproduction

Confirm the intended Ollama model is callable on the host:

```bash
ollama list
ollama run gemma4:31b-cloud
```

Run the complete artifact:

```bash
make research
make publication-suite
```

Capture the Git commit, Docker image versions, OPA/Cedar versions, Ollama
version/model tag or digest, execution service/hardware information, raw reports,
`legal-audit.json`, publication statistics, load-matrix artifacts and completed
annotation/adjudication files for the paper artifact.
