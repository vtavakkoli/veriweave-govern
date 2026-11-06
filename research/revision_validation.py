"""Reviewer-requested implementation experiments, independent of the GovernBench oracle.

All tickets, keys, policies and faults below are researcher-authored fixtures.
They test mechanics; they are not independent organizational evidence validation.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import hmac
import json
import platform
import statistics
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path

import yaml

from app.audit import AuditLedger
from app.engine import GovernanceEngine, ReplayError
from app.evidence import (
    EvidenceVerifier,
    TrustedEvidenceSource,
    attestation_payload,
    request_scope_hash,
)
from app.models import EvaluationRequest, EvidenceAttestation, EvidenceItem
from app.policy import PolicyStore
from research.metrics import exact_binomial_interval

FIXTURE_KEY = "public-research-fixture-only-never-use-in-deployment"
FIXTURE_TIME = datetime(2026, 11, 6, tzinfo=UTC)


def fixture_verifier() -> EvidenceVerifier:
    return EvidenceVerifier(
        {"change-system": TrustedEvidenceSource(95, ("1",), ("change_ticket",), ("test",))},
        {"test": FIXTURE_KEY},
    )


def fixture_request() -> EvaluationRequest:
    return EvaluationRequest(
        request_id="fixture-request", tenant_id="research", agent_id="deployment-agent",
        action="deploy", resource="test-service", purpose="authorized research fixture",
        context={"environment": "test", "impact": "low"},
    )


def signed_fixture(
    request: EvaluationRequest, *, evidence_id: str = "change-001",
    now: datetime = FIXTURE_TIME,
) -> EvidenceItem:
    item = EvidenceItem(
        evidence_id=evidence_id, source_id="change-system", source_version="1",
        evidence_type="change_ticket", authority=95, current=True, signed=True,
        content="Change policy section 4 records approval, successful tests and a rollback owner.",
        attestation=EvidenceAttestation(
            key_id="test", issued_at=now - timedelta(hours=1), expires_at=now + timedelta(hours=1),
            tenant_id=request.tenant_id, agent_id=request.agent_id, action=request.action,
            resource=request.resource, request_hash=request_scope_hash(request), signature="",
        ),
    )
    item.attestation.signature = hmac.new(
        FIXTURE_KEY.encode(), attestation_payload(item), hashlib.sha256,
    ).hexdigest()
    return item


def evidence_experiment() -> list[dict[str, object]]:
    request = fixture_request()
    verifier = fixture_verifier()
    good = signed_fixture(request)
    rows = []

    def check(name: str, item: EvidenceItem, expected: bool, **kwargs) -> None:
        assessment = verifier.assess(
            [item], request=kwargs.get("request", request),
            evaluated_at=kwargs.get("evaluated_at", FIXTURE_TIME),
        )[0]
        rows.append({"case": name, "accepted": assessment.accepted,
                     "expected": expected, "passed": assessment.accepted == expected,
                     "reasons": assessment.reasons})

    check("authenticated-current-scoped-ticket", good, True)
    for field, value in (
        ("content", "Forged policy section claims approval without an actual approved change record."),
        ("source_id", "agent-self-asserted"), ("source_version", "old"),
        ("evidence_type", "risk_assessment"), ("authority", 100), ("current", False),
    ):
        item = good.model_copy(deep=True)
        setattr(item, field, value)
        check(f"modified-{field}", item, False)
    no_attestation = good.model_copy(update={"attestation": None})
    check("signed-boolean-without-authenticator", no_attestation, False)
    for value in ("0" * 64, "not-a-mac", "invalid-\u2603"):
        item = good.model_copy(deep=True)
        item.attestation.signature = value
        check(f"invalid-mac-{len(value)}", item, False)
    item = good.model_copy(deep=True)
    item.attestation.key_id = "unknown"
    check("unknown-signing-key", item, False)
    check("expired-authenticated-ticket", good, False, evaluated_at=FIXTURE_TIME + timedelta(hours=2))
    check("future-issued-ticket", good, False, evaluated_at=FIXTURE_TIME - timedelta(hours=2))
    changed_request = request.model_copy(update={"context": {"environment": "production"}})
    check("approval-reused-with-different-context", good, False, request=changed_request)
    other_tenant = request.model_copy(update={"tenant_id": "another-tenant"})
    check("cross-tenant-approval-reuse", good, False, request=other_tenant)
    item = good.model_copy(deep=True)
    item.metadata["contradiction"] = True
    # Even an authentic connector may report a conflict; it must remain review-only.
    item.attestation.signature = hmac.new(
        FIXTURE_KEY.encode(), attestation_payload(item), hashlib.sha256,
    ).hexdigest()
    check("authenticated-conflict", item, False)
    return rows


def audit_experiment(root: Path) -> list[dict[str, object]]:
    rows = []
    faults = (
        "modification", "deletion-middle", "deletion-tail", "insertion", "reordering",
        "policy-hash", "invalid-hmac", "missing-hmac", "malformed-json", "rehash-without-key",
    )
    for fault in faults:
        path = root / f"audit-{fault}.jsonl"
        ledger = AuditLedger(path, FIXTURE_KEY)
        for sequence in range(4):
            ledger.append({"sequence": sequence, "policy_set_hash": "a" * 64})
        checkpoint = ledger.checkpoint()
        records = [json.loads(line) for line in path.read_text().splitlines()]
        if fault in {"modification", "rehash-without-key"}:
            records[1]["payload"]["sequence"] = 900
        elif fault == "deletion-middle":
            del records[1]
        elif fault == "deletion-tail":
            records.pop()
        elif fault == "insertion":
            records.insert(1, copy.deepcopy(records[0]))
        elif fault == "reordering":
            records[1], records[2] = records[2], records[1]
        elif fault == "policy-hash":
            records[1]["payload"]["policy_set_hash"] = "b" * 64
        elif fault == "invalid-hmac":
            records[1]["signature"] = "0" * 64
        elif fault == "missing-hmac":
            records[1]["signature"] = None
        if fault == "rehash-without-key":
            previous = "0" * 64
            for record in records:
                record["previous_hash"] = previous
                body = {k: record[k] for k in ("record_id", "created_at", "previous_hash", "payload")}
                canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), default=str)
                record["record_hash"] = hashlib.sha256((previous + canonical).encode()).hexdigest()
                previous = record["record_hash"]
        path.write_text("\n".join(json.dumps(record) for record in records) + "\n")
        if fault == "malformed-json":
            path.write_text(path.read_text() + "{not-json\n")
        result = ledger.verify(
            expected_head_hash=checkpoint["head_hash"], expected_records=checkpoint["records"],
        )
        rows.append({"case": fault, "detected": not result["valid"],
                     "passed": not result["valid"], "verification": result})

    # An intact HMAC prefix cannot prove the absence of a deleted suffix after restart.
    path = root / "restart-truncation.jsonl"
    ledger = AuditLedger(path, FIXTURE_KEY)
    ledger.append({"sequence": 1})
    ledger.append({"sequence": 2})
    checkpoint = ledger.checkpoint()
    path.write_text(path.read_text().splitlines()[0] + "\n")
    restarted = AuditLedger(path, FIXTURE_KEY)
    unanchored = restarted.verify()["valid"]
    anchored = restarted.verify(
        expected_head_hash=checkpoint["head_hash"], expected_records=checkpoint["records"],
    )["valid"]
    rows.append({"case": "restart-truncation-protected-checkpoint", "detected": not anchored,
                 "unanchored_prefix_valid": unanchored, "passed": unanchored and not anchored})
    return rows


def write_policy(root: Path, decision: str, rules: int = 1, required: bool = False) -> None:
    root.mkdir(parents=True, exist_ok=True)
    document = {
        "id": "revision-fixture", "name": "Reviewer implementation test", "version": decision,
        "rules": [
            {"id": f"rule-{i:05d}", "decision": decision,
             "when": [{"field": "action", "operator": "eq", "value": "deploy" if i == 0 else f"other-{i}"}],
             "required_evidence": ["change_ticket"] if required else [],
             "reason": f"fixture rule {i}"} for i in range(rules)
        ],
    }
    (root / "policy.yaml").write_text(yaml.safe_dump(document))


def replay_experiment(root: Path) -> list[dict[str, object]]:
    policy_dir, archive = root / "policies", root / "snapshots"
    write_policy(policy_dir, "allow")
    store = PolicyStore(policy_dir, archive)
    engine = GovernanceEngine(store, EvidenceVerifier(), AuditLedger(root / "replay.jsonl", FIXTURE_KEY))
    request = fixture_request()
    original = engine.evaluate(request)
    rows = []
    for decision in ("review", "deny"):
        write_policy(policy_dir, decision)
        store.reload()
        live = engine.evaluate(request)
        replayed = engine.replay(original.audit.record_id)
        rows.append({"case": f"live-{decision}-historical-allow", "live": str(live.decision),
                     "historical": replayed["decision"], "passed": live.decision == decision
                     and replayed["decision"] == "allow" and replayed["reproduced"]})
    # Reload both ledger and policy store from disk to avoid an in-memory-only replay test.
    restarted = GovernanceEngine(
        PolicyStore(policy_dir, archive), EvidenceVerifier(), AuditLedger(root / "replay.jsonl", FIXTURE_KEY),
    )
    rows.append({"case": "historical-replay-after-restart",
                 "passed": restarted.replay(original.audit.record_id)["reproduced"]})

    def failure(name: str, callback) -> None:
        try:
            callback()
            rows.append({"case": name, "passed": False})
        except ReplayError as exc:
            rows.append({"case": name, "passed": True, "reason": str(exc)})

    failure("incorrect-policy-version", lambda: engine.replay(original.audit.record_id, store.policy_set_hash))
    historical = archive / f"{original.policy_set_hash}.json"
    contents = historical.read_text()
    historical.unlink()
    failure("missing-historical-policy", lambda: engine.replay(original.audit.record_id))
    historical.write_text(contents.replace("fixture rule 0", "tampered fixture"))
    failure("corrupt-historical-policy", lambda: engine.replay(original.audit.record_id))
    historical.write_text(contents)
    engine.evidence_verifier = fixture_verifier()
    failure("historical-verifier-unavailable", lambda: engine.replay(original.audit.record_id))
    return rows


def concurrent_snapshot_experiment(root: Path, requests: int = 200) -> dict[str, object]:
    policy_dir = root / "concurrent-policies"
    write_policy(policy_dir, "allow")
    store = PolicyStore(policy_dir)
    engine = GovernanceEngine(store, EvidenceVerifier(), AuditLedger(root / "concurrent.jsonl", FIXTURE_KEY))
    known = {store.policy_set_hash: "allow"}
    responses = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        pending = [executor.submit(engine.evaluate, fixture_request()) for _ in range(requests)]
        for decision in ("review", "deny"):
            write_policy(policy_dir, decision)
            store.reload()
            known[store.policy_set_hash] = decision
            pending.extend(executor.submit(engine.evaluate, fixture_request()) for _ in range(requests))
        responses.extend(future.result() for future in pending)
    mismatches = sum(str(response.decision) != known[response.policy_set_hash] for response in responses)
    return {"requests": len(responses), "workers": 8, "bundle_decision_mismatches": mismatches,
            "audit": engine.audit_ledger.verify(), "passed": mismatches == 0
            and engine.audit_ledger.verify()["valid"]}


def scale_experiment(root: Path, samples: int = 100) -> list[dict[str, object]]:
    rows = []
    for rule_count in (100, 1000, 10000):
        policy_dir = root / f"scale-{rule_count}"
        write_policy(policy_dir, "allow", rule_count, required=True)
        store = PolicyStore(policy_dir)
        for evidence_count in (1, 10, 100):
            engine = GovernanceEngine(
                store, fixture_verifier(), AuditLedger(root / f"scale-{rule_count}-{evidence_count}.jsonl"),
            )
            request = fixture_request()
            request.evidence = [
                signed_fixture(request, evidence_id=f"change-{i}", now=datetime.now(UTC))
                for i in range(evidence_count)
            ]
            timings, failures = [], 0
            for _ in range(samples):
                started = time.perf_counter()
                response = engine.evaluate(request)
                timings.append((time.perf_counter() - started) * 1000)
                failures += response.decision != "allow"
            elapsed_ms = sum(timings)
            rows.append({
                "rules": rule_count, "evidence_items": evidence_count, "requests": samples,
                "failures": failures, "mean_ms": statistics.fmean(timings),
                "p95_ms": sorted(timings)[int(0.95 * (samples - 1))],
                "requests_per_second": samples * 1000 / elapsed_ms,
                "audit_valid": engine.audit_ledger.verify()["valid"],
            })
    return rows


def run(output: Path, *, scale_samples: int = 100, skip_scale: bool = False) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="veriweave-revision-") as temp:
        root = Path(temp)
        audit = audit_experiment(root)
        replay = replay_experiment(root)
        evidence = evidence_experiment()
        concurrent = concurrent_snapshot_experiment(root)
        scale = [] if skip_scale else scale_experiment(root, scale_samples)
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "unavailable"
    report = {
        "schema": "veriweave-reviewer-validation/v1",
        "created_at": datetime.now(UTC).isoformat(),
        "environment": {"python": platform.python_version(), "platform": platform.platform(),
                        "processor": platform.processor(), "base_commit": commit,
                        "working_tree": "revision sources; use accompanying source checksums"},
        "audit_faults": audit, "temporal_replay": replay, "evidence_admission": evidence,
        "concurrent_snapshot": concurrent, "scale": scale,
        "reported_human_bank_zero_event_bound": exact_binomial_interval(0, 70),
        "scope": (
            "Researcher-authored implementation fault tests, not independent human validation. "
            "Scale uses one process, sequential calls, in-process engine plus JSONL append, "
            "100-10000 rules and 1-100 evidence items. No HTTP, tool execution, distributed "
            "storage, legal correctness or enterprise deployment claim."
        ),
    }
    source_root = Path(__file__).resolve().parents[1]
    source_paths = sorted((source_root / "app").glob("*.py")) + [
        Path(__file__), source_root / "research" / "metrics.py",
    ]
    report["source_sha256"] = {
        str(path.relative_to(source_root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in source_paths
    }
    report["passed"] = (
        all(row["passed"] for row in audit + replay + evidence) and concurrent["passed"]
        and all(row["failures"] == 0 and row["audit_valid"] for row in scale)
    )
    output.mkdir(parents=True, exist_ok=True)
    (output / "validation.json").write_text(json.dumps(report, indent=2, sort_keys=True))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results/revision-2026-11"))
    parser.add_argument("--scale-samples", type=int, default=100)
    parser.add_argument("--skip-scale", action="store_true")
    args = parser.parse_args()
    if args.scale_samples < 1:
        parser.error("--scale-samples must be positive")
    report = run(args.output, scale_samples=args.scale_samples, skip_scale=args.skip_scale)
    print(json.dumps({"passed": report["passed"], "output": str(args.output)}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
