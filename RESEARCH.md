# VeriWeave Govern — Scientific Governance Benchmark Edition

The research extension evaluates deterministic runtime AI governance rather
than adding an LLM to the final authorization path.

## Experimental layers

### GovernBench-v1

- five synthetic domains with adversarial and temporal cases;
- 2,000 cases per seed and 30 independent seeds by default;
- learned evidence calibration;
- RBAC, ABAC and VeriWeave deterministic comparisons;
- false-allow/deny/review, macro-F1, GASR, Brier, ECE, AUROC and AUPRC;
- six ablations, counterfactuals, governance certificates and temporal replay.

Run:

```bash
make research
```

The synthetic GovernBench layer does **not** report a deterministic language-style
proxy as an LLM baseline. Real LLM evaluation is intentionally isolated in the
EU/Austria publication-validation layer, where the configured Ollama model is
actually invoked through `/api/chat`.

The committed `results/research-v1/` reference run predates this change and is
synthetic/oracle-labelled. It demonstrates reproducibility and controlled
component evaluation; it is not evidence of real-world regulatory effectiveness.

### EU/Austria publication validation

The publication layer adds a separate **150-case regulation-grounded expert
validation set**:

- 50 public-administration actions;
- 50 enterprise IT / DevOps actions;
- 50 data-handling / AI-governance actions;
- a snapshot-versioned registry of official EU/Austrian primary-law sources;
- machine-checkable legal-source and temporal-applicability audit;
- two blind independent-annotation sheets;
- Cohen's kappa and an adjudication workflow;
- real OPA/Rego 1.17.0 and Cedar 4.12.0 executables;
- an actual Ollama LLM baseline (`gemma4:31b-cloud` by default);
- per-domain metrics, raw predictions and calibration reliability data;
- a real HTTP load matrix for service-level latency/throughput reporting.

The legal snapshot is dated **2026-08-17**. It explicitly incorporates
Regulation (EU) 2026/1744: relevant Article 6(2)/Annex III Chapter III
Sections 1–3 benchmark cases are evaluated only after the amended
**2 December 2027** application date and are marked future-effective at the
snapshot. The source registry also reflects the amended Article 4 AI-literacy
wording. See `research/validation/LEGAL_SNAPSHOT_2026-08-17.md`.

Before a publication run, the legal audit verifies partition size, domain and
label balance, unique case IDs, official-source provenance, source verification
and application dates, and temporal consistency:

```bash
make publication-verify
```

Verify the intended model is available through the host Ollama service:

```bash
ollama list
ollama run gemma4:31b-cloud
```

The publication pipeline itself never executes `ollama pull`. It calls the host
Ollama HTTP API directly and performs a real model invocation in preflight.

Then run all external comparators:

```bash
make publication
```

The Docker runner uses `http://host.docker.internal:11434` by default. Override
`OLLAMA_BASE_URL` or `OLLAMA_MODEL` when needed.

For the complete engineering/publication benchmark package:

```bash
make publication-suite
```

For a larger load study, for example approximately 100,000 service requests:

```bash
LOAD_MATRIX_REQUESTS_PER_LEVEL=25000 make publication-load
```

Publication results remain explicitly provisional until **two genuinely
independent blind annotation sheets** and all adjudicated labels are complete.
The repository does not generate, infer or simulate annotator answers and does
not report provisional researcher labels as human ground truth.

The first publication run generates:

```text
results/publication/
├── legal-audit.json
├── report.html
├── report.json
├── calibration-reliability.svg
├── predictions.csv
├── external-details.jsonl
├── annotator-a.csv
├── annotator-b.csv
└── adjudication.csv
```

`external-details.jsonl` records the actual Ollama model name with each LLM
result. `results/pipeline-summary.json` also records the configured model and
real-model preflight latency.

See:

- `docs/SCIENTIFIC_EVALUATION.md`
- `docs/HUMAN_EVALUATION.md`
- `research/validation/README.md`
- `research/validation/LEGAL_SNAPSHOT_2026-08-17.md`
- `research/policy_baselines/README.md`
