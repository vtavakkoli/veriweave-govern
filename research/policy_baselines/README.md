# External publication baselines

The publication profile adds three independent comparator paths to the 150-case EU/Austria validation set.

| Baseline | Pinned/default component | Role |
|---|---|---|
| OPA/Rego | Open Policy Agent 1.17.0 | General-purpose policy-as-code comparison |
| Cedar | `cedar-policy-cli` 4.12.0 | Authorization-policy comparison |
| Ollama | `gemma3n:e2b` | Actual local edge-LLM decision baseline |

The OPA and Cedar policies deliberately use the same small structured fact set: prohibition status, protected external disclosure, impact, unknown-action state, and evidence completeness. They are not presented as full replicas of VeriWeave's evidence calibration or human-review model.

Cedar has a binary authorization result, so the adapter evaluates two policies. A match on `deny.cedar` maps to `deny`; otherwise a match on `allow.cedar` maps to `allow`; if neither policy matches, the tri-state benchmark result is `review`.

The Ollama baseline receives case facts plus paraphrased summaries from the verified official-source registry. It never receives the provisional benchmark label, provisional rationale, or VeriWeave decision. Structured JSON output is requested with temperature zero for repeatability. Model output can still vary across model/runtime versions, so publication artifacts should record the Ollama and model versions used.

Before the full run:

```bash
ollama pull gemma3n:e2b
ollama list
```

The Docker publication runner reaches the host Ollama service through `http://host.docker.internal:11434`.
