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

The publication layer adds a separate 150-case regulation-grounded set:

- 50 public-administration actions;
- 50 enterprise IT / DevOps actions;
- 50 data-handling / AI-governance actions;
- a snapshot-versioned registry of official EU/Austrian legal sources;
- two blind independent-annotation sheets;
- Cohen's kappa and an adjudication workflow;
- real OPA/Rego and Cedar executables;
- an actual local Ollama edge-model baseline (`gemma3n:e2b` by default);
- per-domain metrics and calibration reliability data.

Prepare Ollama on the host:

```bash
ollama pull gemma3n:e2b
```

Then run all external comparators:

```bash
make publication
```

The Docker runner uses `http://host.docker.internal:11434` by default. Override
`OLLAMA_BASE_URL` or `OLLAMA_MODEL` when needed.

Publication results remain explicitly provisional until both blind annotation
sheets and all adjudicated labels are complete. The repository does not invent
human-study outcomes.

See:

- `docs/SCIENTIFIC_EVALUATION.md`
- `docs/HUMAN_EVALUATION.md`
- `research/validation/README.md`
- `research/policy_baselines/README.md`
