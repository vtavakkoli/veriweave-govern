import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.audit import AuditLedger
from app.engine import GovernanceEngine
from app.evidence import EvidenceVerifier
from app.models import Decision, EvaluationRequest, EvidenceItem
from app.policy import PolicyStore

POLICY_DIR = Path(__file__).resolve().parents[1] / "config" / "policies"


def build_engine(tmp_path: Path) -> GovernanceEngine:
    return GovernanceEngine(
        PolicyStore(POLICY_DIR),
        EvidenceVerifier(),
        AuditLedger(tmp_path / "audit.jsonl", "test-key"),
    )


def strong_evidence(evidence_id: str, evidence_type: str) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id,
        source_id="policy-library",
        source_version="2026.1",
        evidence_type=evidence_type,
        content="Policy section 4 requires documented approval and accountable human oversight.",
        authority=90,
        current=True,
        signed=True,
    )


def test_low_risk_read_is_allowed_with_policy_evidence(tmp_path: Path) -> None:
    response = build_engine(tmp_path).evaluate(
        EvaluationRequest(
            agent_id="knowledge-assistant",
            action="summarize",
            context={"impact": "low", "environment": "test"},
            evidence=[strong_evidence("e1", "policy_reference")],
        )
    )
    assert response.decision == Decision.ALLOW
    assert response.audit.signature


def test_missing_evidence_escalates_allow_to_review(tmp_path: Path) -> None:
    response = build_engine(tmp_path).evaluate(
        EvaluationRequest(
            agent_id="knowledge-assistant",
            action="summarize",
            context={"impact": "low"},
        )
    )
    assert response.decision == Decision.REVIEW
    assert "policy_reference" in response.matched_rules[0].missing_evidence


def test_high_impact_action_routes_to_human_review(tmp_path: Path) -> None:
    response = build_engine(tmp_path).evaluate(
        EvaluationRequest(
            agent_id="decision-agent",
            action="approve",
            context={"impact": "high", "environment": "test"},
            evidence=[
                strong_evidence("business", "business_justification"),
                strong_evidence("risk", "risk_assessment"),
            ],
        )
    )
    assert response.decision == Decision.REVIEW
    assert response.review_queue == "ai-governance-board"
    assert response.matched_rules[0].missing_evidence == []


def test_protected_data_transfer_is_denied(tmp_path: Path) -> None:
    response = build_engine(tmp_path).evaluate(
        EvaluationRequest(
            agent_id="export-agent",
            action="send_external",
            resource="customer-records",
            context={"data_classification": "secret", "impact": "critical"},
        )
    )
    assert response.decision == Decision.DENY
    assert response.review_queue == "security-incident"


def test_deny_takes_precedence_over_review(tmp_path: Path) -> None:
    response = build_engine(tmp_path).evaluate(
        EvaluationRequest(
            agent_id="export-agent",
            action="upload_external",
            context={"data_classification": "restricted", "impact": "high"},
            evidence=[
                strong_evidence("business", "business_justification"),
                strong_evidence("risk", "risk_assessment"),
            ],
        )
    )
    assert response.decision == Decision.DENY
    assert {rule.rule_id for rule in response.matched_rules} == {
        "prohibit-secret-exfiltration",
        "high-impact-human-review",
    }


def test_unknown_action_uses_fail_safe_review(tmp_path: Path) -> None:
    response = build_engine(tmp_path).evaluate(
        EvaluationRequest(
            agent_id="experimental-agent",
            action="translate",
            context={"impact": "medium", "environment": "test"},
        )
    )
    assert response.decision == Decision.REVIEW
    assert response.review_queue == "governance-default"
    assert response.matched_rules == []


def test_audit_chain_is_valid_for_untampered_records(tmp_path: Path) -> None:
    engine = build_engine(tmp_path)
    request = EvaluationRequest(agent_id="agent", action="unknown", context={})
    engine.evaluate(request)
    engine.evaluate(request)
    verification = engine.audit_ledger.verify()
    assert verification["valid"] is True
    assert verification["records"] == 2


def test_audit_chain_continues_across_process_restart(tmp_path: Path) -> None:
    path = tmp_path / "audit.jsonl"
    first_ledger = AuditLedger(path, "test-key")
    first = first_ledger.append({"sequence": 1})

    restarted_ledger = AuditLedger(path, "test-key")
    second = restarted_ledger.append({"sequence": 2})

    assert second.previous_hash == first.record_hash
    assert restarted_ledger.verify()["valid"] is True
    assert restarted_ledger.verify()["records"] == 2


def test_audit_append_uses_cached_head_instead_of_rescanning(tmp_path: Path) -> None:
    ledger = AuditLedger(tmp_path / "audit.jsonl", "test-key")
    ledger.append({"sequence": 1})

    def unexpected_rescan() -> str:
        raise AssertionError("append must not rescan the complete audit ledger")

    ledger._read_head_hash = unexpected_rescan  # type: ignore[method-assign]
    ledger.append({"sequence": 2})

    verification = ledger.verify()
    assert verification["valid"] is True
    assert verification["records"] == 2


def test_audit_chain_remains_valid_under_concurrent_appends(tmp_path: Path) -> None:
    ledger = AuditLedger(tmp_path / "audit.jsonl", "test-key")

    with ThreadPoolExecutor(max_workers=16) as executor:
        list(executor.map(lambda sequence: ledger.append({"sequence": sequence}), range(250)))

    verification = ledger.verify()
    assert verification["valid"] is True
    assert verification["records"] == 250


def test_audit_chain_detects_tampered_signature(tmp_path: Path) -> None:
    engine = build_engine(tmp_path)
    engine.evaluate(EvaluationRequest(agent_id="agent", action="unknown", context={}))

    records = [
        json.loads(line)
        for line in engine.audit_ledger.path.read_text(encoding="utf-8").splitlines()
        if line
    ]
    records[0]["signature"] = "tampered"
    engine.audit_ledger.path.write_text(
        "\n".join(json.dumps(record) for record in records) + "\n",
        encoding="utf-8",
    )

    verification = engine.audit_ledger.verify()
    assert verification["valid"] is False
    assert verification["reason"] == "invalid signature"
