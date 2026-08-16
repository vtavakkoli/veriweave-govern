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
- evidence monotonic safety (removing sole required evidence cannot become more permissive);
- fail-safe review for unknown/unregistered actions;
- temporal replay against archived policy state rather than today's policy;
- counterfactual traceability for evidence removal and context changes.

These are software invariants, not legal proofs of compliance. Formal verification of the complete implementation/policy corpus remains a separate research direction.
