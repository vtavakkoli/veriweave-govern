# Full Docker Compose publication pipeline

This profile runs the complete VeriWeave publication workflow through one Docker Compose service.

## What it runs

The `pipeline` service executes, in order:

1. GovernBench synthetic evaluation (default: 30 seeds × 2,000 cases)
2. end-to-end service benchmark
3. EU/Austria legal-source audit
4. 150-case publication validation
5. real OPA/Rego baseline
6. real Cedar baseline
7. local Ollama `gemma4:e2b` baseline
8. VeriWeave comparison
9. publication statistics with bootstrap confidence intervals and paired tests
10. calibration reliability diagram
11. multi-concurrency service load matrix
12. artifact verification and `pipeline-summary.json`

The pipeline does **not** download or pull an Ollama model. It only checks that the configured model already exists on the host. Docker reaches the host Ollama service through `http://host.docker.internal:11434` by default.

## One Docker Compose pipeline command

From PowerShell:

```powershell
docker compose --profile pipeline up --build --abort-on-container-exit --exit-code-from pipeline pipeline
```

`--abort-on-container-exit` stops `govern` and `opa` when the pipeline container finishes. To remove the stopped containers afterward:

```powershell
docker compose --profile pipeline down --volumes --remove-orphans
```

For a one-command PowerShell wrapper that also performs cleanup in `finally`:

```powershell
.\scripts\run-full-pipeline.ps1
```

## Existing local Ollama model

Default configuration:

```text
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=gemma4:e2b
```

No `ollama pull` is executed. If the model is missing, the preflight fails clearly and lists the models visible to the Ollama API.

## Main artifacts

```text
results/
├── pipeline-summary.json
├── benchmark-report.html
├── benchmark-results.json
├── load-matrix.html
├── load-matrix.json
├── research-v1/
│   ├── report.html
│   ├── report.json
│   └── baseline-runs.csv
└── publication/
    ├── legal-audit.json
    ├── report.html
    ├── report.json
    ├── statistics.html
    ├── statistics.json
    ├── predictions.csv
    ├── external-details.jsonl
    ├── calibration-reliability.svg
    ├── annotator-a.csv
    ├── annotator-b.csv
    └── adjudication.csv
```

`pipeline-summary.json` records stage status, elapsed time, the configured Ollama model, and whether every expected artifact exists.

## Useful overrides

PowerShell example for a faster development run:

```powershell
$env:GOVERNBENCH_SEEDS = "3"
$env:GOVERNBENCH_CASES = "300"
$env:LOAD_MATRIX_REQUESTS_PER_LEVEL = "1000"
$env:PUBLICATION_BOOTSTRAP_SAMPLES = "1000"
docker compose --profile pipeline up --build --abort-on-container-exit --exit-code-from pipeline pipeline
```

For the intended publication run, keep the defaults: 30 × 2,000 GovernBench cases, 10,000 bootstrap samples, and 10,000 load requests per concurrency level at `1,4,16,32`.

## Human-validation boundary

The pipeline can generate and evaluate the regulation-grounded dataset, but it cannot fabricate human validation. Until both blind annotator sheets and all adjudicated labels are completed, the publication report remains marked `provisional-regulation-grounded` / `DRAFT — HUMAN VALIDATION REQUIRED`.
