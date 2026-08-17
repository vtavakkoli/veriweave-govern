# External publication baselines

The publication profile adds three independent comparator paths to the 150-case EU/Austria validation set.

| Baseline | Pinned/default component | Role |
|---|---|---|
| OPA/Rego | Open Policy Agent 1.17.0 | General-purpose policy-as-code comparison |
| Cedar | `cedar-policy-cli` 4.12.0 | Authorization-policy comparison |
| Ollama | `gemma4:e2b` | Actual local edge-LLM decision baseline |

The OPA and Cedar policies deliberately use the same small structured fact set:
prohibition status, protected external disclosure, impact, unknown-action state,
and evidence completeness. They are not presented as full replicas of
VeriWeave's evidence calibration or human-review model. Their purpose is to
provide reproducible policy-engine comparators rather than artificially weak
straw-man baselines.

Cedar has a binary authorization result, so the adapter evaluates two policies.
A match on `deny.cedar` maps to `deny`; otherwise a match on `allow.cedar` maps
to `allow`; if neither policy matches, the tri-state benchmark result is
`review`.

The Ollama baseline receives case facts plus paraphrased summaries from the
versioned official-source registry. It never receives the provisional benchmark
label, provisional rationale, prohibition metadata, adjudicated label or
VeriWeave decision. Structured JSON output is requested with temperature zero
for repeatability. Model output can still vary across model/runtime versions, so
publication artifacts should record the Ollama version, exact model tag/digest,
hardware, and evaluation date used.

Default host endpoint and model:

```text
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=gemma4:e2b
```

Before the full run:

```bash
ollama pull gemma4:e2b
ollama list
```

Then execute the publication profile:

```bash
make publication
```

The Docker publication runner reaches the host Ollama service through
`http://host.docker.internal:11434`. Override the environment values when a
different model or network arrangement is required.

## Publication fairness rules

For a defensible comparison:

1. keep the same 150-case frozen input set for every method;
2. do not expose researcher/adjudicated labels to any comparator;
3. use the same legal-source snapshot for the local LLM prompt;
4. record baseline availability failures rather than silently replacing failed
   calls with another model;
5. report model/runtime versions and exact policy-engine versions;
6. use adjudicated ground truth for the final paper only after human validation
   is complete;
7. report overall and per-domain metrics rather than only the best aggregate
   score.

The deterministic `llm-proxy` used in synthetic GovernBench is **not** an LLM
baseline and must remain clearly separated from this actual Ollama experiment.
