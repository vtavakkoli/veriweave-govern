from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.audit import AuditLedger
from app.engine import GovernanceEngine
from app.evidence import EvidenceVerifier
from app.models import EvaluationRequest
from app.policy import PolicyLoadError, PolicyStore
from research.revision_validation import (
    audit_experiment,
    concurrent_snapshot_experiment,
    evidence_experiment,
    fixture_request,
    fixture_verifier,
    replay_experiment,
    signed_fixture,
    write_policy,
)


def test_direct_tamper_faults_and_protected_checkpoint(tmp_path: Path):
    rows = audit_experiment(tmp_path)
    assert len(rows) == 11 and all(row["passed"] for row in rows)
    assert rows[-1]["unanchored_prefix_valid"] is True


def test_actual_temporal_replay_including_missing_and_corrupt_state(tmp_path: Path):
    rows = replay_experiment(tmp_path)
    assert len(rows) == 7 and all(row["passed"] for row in rows)


def test_authenticated_artifact_admission_faults():
    rows = evidence_experiment()
    assert len(rows) == 17 and all(row["passed"] for row in rows)


def test_concurrent_reload_never_mislabels_policy_hash(tmp_path: Path):
    report = concurrent_snapshot_experiment(tmp_path, requests=30)
    assert report["requests"] == 90 and report["passed"]


def test_duplicate_ids_cannot_launder_rejected_evidence():
    request = fixture_request()
    good = signed_fixture(request)
    weak = good.model_copy(update={"content": "forged"})
    with pytest.raises(ValidationError, match="unique"):
        EvaluationRequest.model_validate({**request.model_dump(), "evidence": [weak, good]})


def test_failed_reload_retains_previous_snapshot(tmp_path: Path):
    write_policy(tmp_path, "deny")
    store = PolicyStore(tmp_path)
    digest = store.policy_set_hash
    (tmp_path / "policy.yaml").write_text("rules: [malformed]")
    with pytest.raises(PolicyLoadError):
        store.reload()
    assert store.policy_set_hash == digest


def test_replay_uses_historical_time_after_evidence_expires(tmp_path: Path):
    policy_dir = tmp_path / "policies"
    write_policy(policy_dir, "allow", required=True)
    store = PolicyStore(policy_dir, tmp_path / "snapshots")
    engine = GovernanceEngine(store, fixture_verifier(), AuditLedger(tmp_path / "audit.jsonl"))
    request = fixture_request()
    now = datetime.now(UTC)
    request.evidence = [signed_fixture(request, now=now)]
    response = engine.evaluate(request)
    assert response.decision == "allow"
    # Later admission must fail while replay still uses the original recorded time.
    later = engine.evidence_verifier.assess(
        request.evidence, request=request, evaluated_at=now + timedelta(days=1),
    )
    assert not later[0].accepted
    assert engine.replay(response.audit.record_id)["decision"] == "allow"


def test_review_is_routed_and_deny_queue_has_precedence(tmp_path: Path):
    policy = tmp_path / "policy.yaml"
    policy.write_text("""id: conflict
name: Conflict test
version: '1'
rules:
  - id: a-review
    decision: review
    review_queue: general-review
  - id: z-deny
    decision: deny
    review_queue: security
""")
    engine = GovernanceEngine(
        PolicyStore(tmp_path), EvidenceVerifier(), AuditLedger(tmp_path / "audit.jsonl"),
    )
    response = engine.evaluate(fixture_request())
    assert response.decision == "deny" and response.review_queue == "security"


def test_http_replay_contract_and_schema_rejection(tmp_path: Path, monkeypatch):
    from fastapi.testclient import TestClient

    import app.main as service

    write_policy(tmp_path / "policies", "allow")
    store = PolicyStore(tmp_path / "policies", tmp_path / "snapshots")
    engine = GovernanceEngine(store, EvidenceVerifier(), AuditLedger(tmp_path / "api.jsonl"))
    monkeypatch.setattr(service, "engine", engine)
    client = TestClient(service.app)
    response = client.post("/v1/evaluate", json=fixture_request().model_dump(mode="json"))
    assert response.status_code == 200
    record_id = response.json()["audit"]["record_id"]
    assert client.post("/v1/replay", json={"record_id": record_id}).json()["reproduced"]
    assert client.post("/v1/replay", json={
        "record_id": record_id, "expected_policy_set_hash": "0" * 64,
    }).status_code == 409
    assert client.post("/v1/evaluate", json={"agent_id": "a", "action": "   "}).status_code == 422
