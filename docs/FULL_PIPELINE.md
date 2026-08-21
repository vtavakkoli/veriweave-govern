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
7. real Ollama `gemma4:31b-cloud` baseline through the host Ollama `/api/chat` endpoint
8. VeriWeave comparison
9. publication statistics with bootstrap confidence intervals and paired tests
10. calibration reliability diagram
11. multi-concurrency service load matrix
12. artifact verification and `pipeline-summary.json`

The synthetic GovernBench stage no longer reports the deterministic `llm-proxy` as an LLM baseline. The real LLM comparison is performed only in the regulation-grounded publication-validation stage, where all 150 cases are sent to the configured Ollama model.

The pipeline does **not** download or pull an Ollama model. It checks the host Ollama API at `http://host.docker.internal:11434` and performs a real `/api/chat` probe before any benchmark stage starts. A failed model invocation fails the pipeline.

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

## Existing Ollama model on the host

Default configuration:

```text
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=gemma4:31b-cloud
OLLAMA_PROBE_TIMEOUT=120
```

No `ollama pull` is executed. The preflight first inspects `/api/tags` and then performs an actual `/api/chat` request with `OLLAMA_MODEL`. This makes it explicit in the logs and `pipeline-summary.json` that a real model invocation succeeded before publication evaluation begins.

If you prefer another already available model, override it before the Compose command:

```powershell
$env:OLLAMA_MODEL = "gemma4:31b"
docker compose --profile pipeline up --build --abort-on-container-exit --exit-code-from pipeline pipeline
```

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

`pipeline-summary.json` records stage status, elapsed time, the configured Ollama model, the real-model preflight latency, and whether every expected artifact exists. `external-details.jsonl` records the configured Ollama model with each model decision so the publication artifact identifies the actual model used.

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
