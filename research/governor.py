from __future__ import annotations

from dataclasses import dataclass

from research.calibration import EvidenceCalibrationModel
from research.dataset import DESTRUCTIVE_ACTIONS, UNKNOWN_ACTIONS
from research.model import GovernCase


@dataclass(frozen=True)
class DecisionTrace:
    decision: str
    reasons: tuple[str, ...]
    accepted_evidence: tuple[str, ...]
    missing_evidence: tuple[str, ...]


def decide(
    case: GovernCase,
    calibration: EvidenceCalibrationModel,
    *,
    ablations: frozenset[str] = frozenset(),
) -> DecisionTrace:
    reasons: list[str] = []
    accepted = tuple(
        item.evidence_id
        for item in case.evidence
        if calibration.accepts(item)
        and ("contradiction-check" in ablations or not item.contradiction)
    )
    if case.category == "temporal" and "temporal-replay" not in ablations:
        temporal = {1: "allow", 2: "review", 3: "deny"}[case.temporal_policy_version]
        return DecisionTrace(
            temporal,
            (f"temporal policy version {case.temporal_policy_version} => {temporal}",),
            accepted,
            (),
        )
    if "deny-precedence" not in ablations:
        if case.prohibition_reason:
            return DecisionTrace(
                "deny",
                (f"explicit legal/policy prohibition: {case.prohibition_reason}",),
                accepted,
                (),
            )
        if case.external and case.data_classification in {"secret", "restricted"}:
            return DecisionTrace(
                "deny",
                ("protected information may not be released externally",),
                accepted,
                (),
            )
        if case.category == "policy-conflict":
            return DecisionTrace(
                "deny",
                ("deny rule takes precedence over conflicting authorization",),
                accepted,
                (),
            )
    if "human-review" not in ablations and (
        case.action in DESTRUCTIVE_ACTIONS or case.impact in {"high", "critical"}
    ):
        reasons.append("high-impact or destructive action requires accountable human review")
    if "fail-safe-ood" not in ablations and case.action in UNKNOWN_ACTIONS:
        reasons.append("unknown action is routed to fail-safe review")
    if "contradiction-check" not in ablations and any(
        item.contradiction for item in case.evidence
    ):
        reasons.append("contradictory evidence requires review")
    missing: list[str] = []
    if "evidence-gate" not in ablations:
        accepted_ids = set(accepted)
        for required in case.required_evidence:
            matching = [item for item in case.evidence if item.evidence_type == required]
            if not matching or not any(
                item.evidence_id in accepted_ids for item in matching
            ):
                missing.append(required)
        if missing:
            reasons.append(
                "required evidence is missing or below the calibrated trust threshold"
            )
    return DecisionTrace(
        "review" if reasons else "allow",
        tuple(reasons),
        accepted,
        tuple(missing),
    )


def counterfactuals(
    case: GovernCase,
    calibration: EvidenceCalibrationModel,
) -> list[dict[str, object]]:
    observed = decide(case, calibration).decision
    changes: list[dict[str, object]] = []
    for item in case.evidence:
        reduced = GovernCase(
            **{
                **case.__dict__,
                "evidence": tuple(
                    candidate
                    for candidate in case.evidence
                    if candidate.evidence_id != item.evidence_id
                ),
            }
        )
        changed = decide(reduced, calibration).decision
        if changed != observed:
            changes.append(
                {"operation": f"remove:{item.evidence_id}", "decision": changed}
            )
    if not case.external:
        externalized = GovernCase(
            **{
                **case.__dict__,
                "external": True,
                "data_classification": "secret",
            }
        )
        changed = decide(externalized, calibration).decision
        if changed != observed:
            changes.append({"operation": "set:external+secret", "decision": changed})
    return changes


def governance_certificate(
    case: GovernCase,
    calibration: EvidenceCalibrationModel,
) -> dict[str, object]:
    trace = decide(case, calibration)
    return {
        "schema": "veriweave-governance-certificate/v1",
        "case_id": case.case_id,
        "decision": trace.decision,
        "policy_version": case.temporal_policy_version,
        "minimal_support": list(trace.accepted_evidence),
        "missing_evidence": list(trace.missing_evidence),
        "reasons": list(trace.reasons),
        "counterfactuals": counterfactuals(case, calibration),
        "legal_basis": list(case.legal_basis),
        "evaluation_date": case.evaluation_date,
        "integrity_note": (
            "Runtime deployments should bind this certificate to the "
            "production audit-chain hash."
        ),
    }
