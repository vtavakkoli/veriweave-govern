# Product roadmap

This roadmap communicates intended direction, not a binding delivery
commitment. Priorities may change based on security findings, user feedback,
and validated deployment requirements.

## Milestone 1 — Hardened single-tenant pilot

- OIDC authentication and workload identity
- PostgreSQL persistence and schema migrations
- role-based administration
- idempotency, quotas, and rate limits
- structured logs, metrics, and OpenTelemetry traces
- secret-manager integration and key rotation
- backup, restore, retention, and operational runbooks

**Exit criteria:** a controlled pilot can operate without development secrets,
in-memory-only state, or anonymous administrative endpoints.

## Milestone 2 — Governed policy lifecycle

- signed policy bundles and trusted publisher keys
- draft, review, approve, activate, deprecate, and revoke states
- four-eyes approval and separation of duties
- policy diff, validation, rollback, and effective-date controls
- immutable approval evidence linked to each active policy set

**Exit criteria:** every production policy change has accountable approval,
verifiable provenance, and safe rollback.

## Milestone 3 — Enterprise integrations

- ServiceNow, Jira, and BMC Helix review queues
- SharePoint, Confluence, and Git policy synchronization
- SIEM and immutable-object-storage audit export
- API-gateway, agent-platform, and semantic-router adapters
- webhooks and asynchronous review completion

**Exit criteria:** governance decisions and review ownership integrate with
existing enterprise systems without manual copying.

## Milestone 4 — Multi-tenant platform

- tenant isolation and tenant-scoped encryption
- organization, project, environment, and policy namespaces
- delegated administration and fine-grained authorization
- usage metering, operational limits, and audit export boundaries
- migration and disaster-recovery procedures

**Exit criteria:** independent tenants can be operated with tested data,
identity, policy, and audit isolation.

## Milestone 5 — VeriWeave evidence certification

- provenance-robust evidence selection
- counterfactual omitted-evidence checks
- temporal policy replay and supersession detection
- claim-level support and contradiction certificates
- human-validated evaluation corpora and calibrated thresholds

**Exit criteria:** evidence certificates are reproducible, machine-readable,
and evaluated against independently reviewed cases.
