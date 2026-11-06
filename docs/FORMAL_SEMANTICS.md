# Formal decision semantics

Model the decision as

\[
D(a,P_t,E_t,C_t)\rightarrow\{ALLOW,REVIEW,DENY\}
\]

where `a` is the action, `P_t` the versioned policy set, `E_t` the evidence set, and `C_t` the execution context.

Safety precedence is

\[
DENY > REVIEW > ALLOW.
\]

For a rule with required evidence types `R`, an allow is not permitted when `R - type(V(E_t))` is non-empty, where `V` is the evidence verifier/calibrator.

Properties covered by repository tests and research experiments:

- deterministic replay for identical versioned inputs;
- deny dominance under conflicting permissive/prohibitive controls;
- typed-support monotonicity with matched rules, review/conflict conditions and
  remaining admission statuses held fixed;
- fail-safe review for unknown/unregistered actions;
- temporal replay against archived policy state rather than today's policy;
- counterfactual traceability for evidence removal and context changes.

These are software invariants, not legal proofs of compliance. Formal verification of the complete implementation/policy corpus remains a separate research direction.

Unrestricted monotonicity over raw evidence is not claimed. Removing a conflict
or changing duplicate-sensitive quality scores changes verifier state and may
change review to allow. The conditional property concerns typed sufficiency
after those assessments are fixed.

The service captures one policy snapshot and server time per decision. Replay
binds normalized inputs to the original archived policy, evaluator version and
verifier configuration; unavailable historical state fails explicitly.
See [evidence admission](EVIDENCE_ADMISSION.md) for the distinct demo and
authenticated adapters and the conditional trust assumptions.
