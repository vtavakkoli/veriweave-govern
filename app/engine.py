from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from app.audit import AuditLedger
from app.evidence import EvidenceVerifier
from app.models import Decision, EvaluationRequest, EvaluationResponse, RuleResult
from app.policy import PolicyLoadError, PolicySnapshot, PolicyStore, rule_matches

_DECISION_PRIORITY = {Decision.ALLOW: 0, Decision.REVIEW: 1, Decision.DENY: 2}
EVALUATOR_VERSION = "veriweave-runtime/v2"


class ReplayError(ValueError):
    pass


class GovernanceEngine:
    def __init__(
        self,
        policy_store: PolicyStore,
        evidence_verifier: EvidenceVerifier,
        audit_ledger: AuditLedger,
    ) -> None:
        self.policy_store = policy_store
        self.evidence_verifier = evidence_verifier
        self.audit_ledger = audit_ledger

    def evaluate(self, request: EvaluationRequest) -> EvaluationResponse:
        # Freeze once: reload must not change the bundle between matching and hashing.
        snapshot = self.policy_store.capture()
        evaluated_at = datetime.now(UTC)
        payload = self._decision_payload(request, snapshot, evaluated_at)
        audit = self.audit_ledger.append(payload)
        return EvaluationResponse(
            request_id=request.request_id, audit=audit,
            **{key: value for key, value in payload.items() if key not in {"request", "evaluator_version"}},
        )

    def replay(
        self, record_id: str, expected_policy_set_hash: str | None = None,
    ) -> dict[str, Any]:
        """Replay historical inputs without executing tools or appending a new decision."""
        try:
            record = self.audit_ledger.checked_record(record_id)
            original = record["payload"]
            digest = original["policy_set_hash"]
            if expected_policy_set_hash is not None and digest != expected_policy_set_hash:
                raise ReplayError("incorrect historical policy version requested")
            if original["evaluator_version"] != EVALUATOR_VERSION:
                raise ReplayError("historical evaluator version unavailable")
            if original["evidence_verifier_id"] != self.evidence_verifier.verifier_id:
                raise ReplayError("historical evidence verifier/configuration unavailable")
            snapshot = self.policy_store.historical(digest)
            payload = self._decision_payload(
                EvaluationRequest.model_validate(original["request"]), snapshot,
                datetime.fromisoformat(original["evaluated_at"]),
            )
            if payload != original:
                raise ReplayError("historical decision does not reproduce")
            return {
                "record_id": record_id, "reproduced": True, "decision": payload["decision"],
                "policy_set_hash": digest, "evaluated_at": payload["evaluated_at"],
                "evidence_verifier_id": payload["evidence_verifier_id"],
            }
        except (ValueError, KeyError, TypeError, PolicyLoadError) as exc:
            raise ReplayError(str(exc)) from exc

    def _decision_payload(
        self, request: EvaluationRequest, snapshot: PolicySnapshot, evaluated_at: datetime,
    ) -> dict[str, Any]:
        assessments = self.evidence_verifier.assess(
            request.evidence, request=request, evaluated_at=evaluated_at,
        )
        assessment_by_id = {item.evidence_id: item for item in assessments}
        evidence_by_type: dict[str, list[str]] = defaultdict(list)
        for item in request.evidence:
            evidence_by_type[item.evidence_type].append(item.evidence_id)

        rule_results: list[RuleResult] = []
        for loaded in snapshot.policies:
            policy = loaded.document
            if policy.effective_from and evaluated_at.date() < policy.effective_from:
                continue
            for rule in policy.rules:
                if not rule_matches(request, rule):
                    continue

                missing: list[str] = []
                weak: list[str] = []
                for evidence_type in rule.required_evidence:
                    evidence_ids = evidence_by_type.get(evidence_type, [])
                    if not evidence_ids:
                        missing.append(evidence_type)
                        continue
                    if not any(
                        assessment_by_id[evidence_id].accepted
                        and assessment_by_id[evidence_id].score >= rule.min_evidence_score
                        for evidence_id in evidence_ids
                    ):
                        weak.append(evidence_type)

                decision = rule.decision
                reasons = [rule.reason]
                if missing or weak:
                    if decision == Decision.ALLOW:
                        decision = Decision.REVIEW
                    reasons.extend(
                        [
                            *(f"Missing required evidence: {item}" for item in missing),
                            *(f"Evidence below trust threshold: {item}" for item in weak),
                        ]
                    )

                rule_results.append(
                    RuleResult(
                        policy_id=policy.id,
                        policy_version=policy.version,
                        rule_id=rule.id,
                        matched=True,
                        decision=decision,
                        reasons=reasons,
                        missing_evidence=[*missing, *weak],
                        review_queue=rule.review_queue,
                    )
                )

        rule_results.sort(key=lambda item: (item.policy_id, item.policy_version, item.rule_id))
        if not rule_results:
            final_decision = Decision.REVIEW
            reasons = ["No active policy rule matched; fail-safe human review required"]
            review_queue = "governance-default"
        else:
            final_decision = max(
                (result.decision for result in rule_results), key=_DECISION_PRIORITY.__getitem__
            )
            conflict = any(item.metadata.get("contradiction") for item in request.evidence)
            if conflict and final_decision == Decision.ALLOW:
                final_decision = Decision.REVIEW
            reasons = _unique(reason for result in rule_results for reason in result.reasons)
            if conflict:
                reasons.append("Conflicting evidence requires accountable review")
            review_queue = next(
                (
                    result.review_queue
                    for result in rule_results
                    if result.decision == final_decision and result.review_queue
                ),
                None,
            )
            if final_decision == Decision.REVIEW and review_queue is None:
                review_queue = "governance-default"

        return {
            "request": request.model_dump(mode="json"),
            "decision": str(final_decision),
            "reasons": reasons,
            "matched_rules": [item.model_dump(mode="json") for item in rule_results],
            "evidence_assessments": [item.model_dump(mode="json") for item in assessments],
            "policy_set_hash": snapshot.policy_set_hash,
            "evaluated_at": evaluated_at.isoformat(),
            "evidence_verifier_id": self.evidence_verifier.verifier_id,
            "evaluator_version": EVALUATOR_VERSION,
            "review_queue": review_queue,
        }


def _unique(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(values))
