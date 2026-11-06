# VeriWeave Govern architecture

## Product boundary

VeriWeave Govern is a decision-support and enforcement control plane. It does not replace legal counsel, organizational accountability, identity management, model-safety evaluation, or production authorization controls. It creates a deterministic governance gate around AI-agent actions and preserves the evidence used for each decision.

## Request flow

The API captures a single versioned policy snapshot and server evaluation time.
Policy matching and evidence admission feed a deny-over-review-over-allow
reducer. Review produces an external queue identifier; audit stores the complete
decision state and historical replay bindings. The trusted router executes only
a new live allow. See [integration](INTEGRATION.md) for the control flow.

## Design principles

1. **Fail safe:** an unmatched action is routed to review, not silently allowed.
2. **Deterministic enforcement:** policy matching does not depend on an LLM.
3. **Evidence before execution:** allow rules can be escalated when required evidence is missing or weak.
4. **Versioned accountability:** every response includes the active policy-set hash and policy versions.
5. **Tamper evidence:** SHA-256 chaining and optional HMAC authenticate records;
   a protected head/count checkpoint is needed to detect truncation after restart.
6. **Human ownership:** review queues are policy-defined and explicit; external
   workflow systems implement actual human tasks and approvals.
7. **Local-first deployment:** the MVP runs without external model or cloud dependencies.

## Integration path

- **Policy-as-Skill:** import governed skills, required evidence, allowed actions, and review triggers as policy rules.
- **VeriWeave-VITA-PRO:** augment the deterministic evidence adapter with provenance-robust evidence selection and certificates.
- **Identity:** receive tenant, user, agent, and role claims from Keycloak, Entra ID, or an API gateway.
- **Workflow systems:** map review queues to ServiceNow, Jira, BMC Helix, or a customer approval service.
- **Policy repositories:** synchronize approved versions from SharePoint, Confluence, Git, or document-management systems.
- **Audit backends:** export signed records to immutable object storage, SIEM, OpenTelemetry, or a tamper-evident ledger.

## Production-hardening roadmap

- OIDC authentication, tenant isolation, and role-based administration
- PostgreSQL persistence and migrations
- policy approval workflow with four-eyes control
- signed policy bundles and trusted publisher keys
- secret-manager integration and key rotation
- rate limits, idempotency, quotas, and workload identity
- OpenTelemetry traces, metrics, and structured logs
- encrypted fields and retention policies
- external audit anchoring
- independent threat model, penetration test, and supply-chain review
