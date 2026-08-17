# VeriWeave Govern — Scientific Governance Benchmark Edition

The research extension evaluates deterministic runtime AI governance rather
than adding an LLM to the final authorization path.

## Experimental layers

### GovernBench-v1

- five synthetic domains with adversarial and temporal cases;
- 2,000 cases per seed and 30 independent seeds by default;
- learned evidence calibration;
- RBAC, ABAC, deterministic language-style proxy and VeriWeave;
- false-allow/deny/review, macro-F1, GASR, Brier, ECE, AUROC and AUPRC;
- six ablations, counterfactuals, governance certificates and temporal replay.

Run:

```bash
make research
```

The committed `results/research-v1/` reference run is synthetic/oracle-labelled.
It demonstrates reproducibility and controlled component evaluation; it is not
evidence of real-world regulatory effectiveness.

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
- an actual local Ollama edge-model baseline (`gemma4:e2b` by default);
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

Prepare Ollama on the host:

```bash
ollama pull gemma4:e2b
ollama list
```

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

See:

- `docs/SCIENTIFIC_EVALUATION.md`
- `docs/HUMAN_EVALUATION.md`
- `research/validation/README.md`
- `research/validation/LEGAL_SNAPSHOT_2026-08-17.md`
- `research/policy_baselines/README.md`
