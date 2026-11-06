# Evidence admission and trust boundary

The default HTTP adapter is **demo-metadata**: it scores caller-supplied
authority, current/signed flags and text features. It does not verify a digital
signature, identify a real ticket owner or establish document truth. The
synthetic logistic model in `research/calibration.py` is separate. Its reported
ECE 0.2253 rules out interpreting its score as a calibrated probability.

## Authenticated connector mode

Set `GOVERN_EVIDENCE_TRUST_CONFIG` to a protected JSON configuration file. It
contains `sources` and `keys`. An illustrative schema is:

```json
{
  "sources": {
    "change-system": {
      "authority": 95,
      "versions": ["1"],
      "evidence_types": ["change_ticket"],
      "key_ids": ["connector-2026"]
    }
  },
  "keys": {"connector-2026": "REPLACE_WITH_A_SECRET_FROM_YOUR_SECRET_STORE"}
}
```

Do not commit real keys. Protect this configuration with the same controls as
the governor host. The reference mechanism uses HMAC-SHA256, a symmetric MAC;
it is not an asymmetric signature, a PKI implementation or proof of
nonrepudiation. A malicious holder of the MAC key is inside the trusted boundary.

A trusted connector retrieves the actual artifact using its service identity,
normalizes its type/source/version/content/status, binds it to the request scope,
and creates an attestation. The governor does not accept a planner's `signed=true`
flag as that attestation. The attestation includes a key ID, timezone-aware
issuance/expiry, tenant, agent, action, resource and `request_scope_hash(request)`.
The scope digest also binds purpose and context; request IDs and evidence lists
are excluded. The HMAC covers the canonical JSON returned by
`attestation_payload(item)` (the whole item except the HMAC field).

Admission requires all of the following:

- configured source, approved source version and authorized evidence type;
- key authorized for that source and a valid HMAC over all covered fields;
- issuance <= the captured evaluation time < expiry;
- matching tenant, agent, action, resource, purpose and context;
- current status, sufficient heuristic quality and no reported contradiction.

Authority comes from source configuration in this mode. The item's own
authority field is authenticated but cannot elevate that configured authority.
Duplicate evidence identifiers are rejected by request validation. An absent or
rejected required type produces review; a contradiction also produces review
unless a matched deny takes precedence. Source conflicts must be identified by
connectors or upstream controls; this adapter does not infer contradictions from
arbitrary natural-language documents or reconcile two independent data systems.

The MAC establishes configured provenance and byte integrity. It does not
establish substantive truth, legal correctness, exhaustive revocation checking,
or an independent assessment of artifact quality. Evidence is assessed using
the supplied version/status snapshot and bounded attestation lifetime; revocation
between collection and execution requires deployment-specific controls.

## Replay and concurrency

Every live decision captures one policy snapshot and one server evaluation time.
The audit payload records normalized inputs, effective outcome, rules, evidence
assessments, policy hash, evaluator version and evidence-verifier fingerprint.
The fingerprint covers source configuration and key fingerprints, never raw keys.

`POST /v1/replay` loads the original content-addressed policy archive and the
recorded time. It compares the complete recomputed outcome with the recorded
outcome without executing a tool or appending a new authorization. Missing or
corrupt policy archives, incompatible evaluator/verifier configuration, audit
integrity failure and a requested wrong policy version produce HTTP 409. Legacy
records without this state are not silently replayed with current configuration.
Key rotation requires preserving the historical verifier in a protected replay
environment; the reference service fails explicitly when it is unavailable.

The JSONL audit writer supports one process, including concurrent threads. HMAC
authenticates records, but does not detect removal of an intact suffix after
restart. Export `ledger.checkpoint()` and protect its head and record count
outside the mutable store, then pass both to `verify`. Without that external
anchor an intact prefix can verify; host/key compromise and distributed storage
integrity are outside these experiments.

For Docker Compose, the optional override mounts a host trust file as a secret:

```bash
GOVERN_EVIDENCE_TRUST_FILE=/protected/evidence-trust.json \
  docker compose -f docker-compose.yml -f docker-compose.attested.yml up --build govern
```

The base Compose profile remains the labelled demonstration mode. Its data
volume retains both audit records and policy archives. Protect the externally
stored checkpoints and keep the secret file out of the repository.
