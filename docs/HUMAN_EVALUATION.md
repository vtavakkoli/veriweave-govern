# Human evaluation protocol

Use this protocol to collect real validation without fabricating human results.

Target 10–20 practitioners across AI governance, security/architecture, compliance/risk and software engineering. Use 50–100 sanitized cases spanning domains and risk categories. Each case should receive at least two independent annotations; a representative subset should receive three or more.

Recommended conditions: human-only; human + VeriWeave decision trace/certificate; optional actual LLM advisory output. Never silently substitute the deterministic language-style proxy for an LLM study.

Measure decision (`allow|review|deny`), duration, confidence (1–5), optional explanation usefulness, missed violations, and inter-rater agreement. Use `research/human-annotations-template.csv`, then run:

```bash
python -m research.human_eval research/human-annotations.csv
```

The scorer reports annotation count, mean duration/confidence, and mean pairwise Cohen's kappa. Preserve any adjudication procedure used to create gold labels.

Use sanitized/synthetic cases unless approvals permit otherwise. Do not put citizen, patient, employee, client-secret or other protected data in the public repository.
