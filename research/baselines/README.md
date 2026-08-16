# External policy-engine baselines

The built-in benchmark always runs RBAC, ABAC, a deterministic language-style proxy, and VeriWeave. OPA and Cedar comparative claims should use their **official engines**.

- `opa/policy.rego` is a minimal authorization baseline; capture a pinned OPA version and raw output.
- `cedar/policies.cedar` is an authorization-only Cedar baseline; use official `cedar-policy-cli` and capture the exact version.

OPA/Cedar have different semantics from VeriWeave's evidence-aware three-way governance contract. Do not force a misleading one-to-one comparison. Report supported capabilities and unsupported governance requirements explicitly.

`research.baselines.external_json_baseline()` accepts an adapter executable that consumes one GovernBench case as JSON stdin and returns `{"decision":"allow|review|deny"}`. Missing engines are reported unavailable rather than silently mocked.
