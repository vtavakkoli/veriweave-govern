from __future__ import annotations

import hashlib
import hmac
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.models import EvaluationRequest, EvidenceAssessment, EvidenceItem


@dataclass(frozen=True)
class TrustedEvidenceSource:
    authority: int
    versions: tuple[str, ...]
    evidence_types: tuple[str, ...]
    key_ids: tuple[str, ...]


def attestation_payload(item: EvidenceItem) -> bytes:
    """Bind the complete evidence and request scope, excluding only the MAC itself."""
    payload = item.model_dump(mode="json")
    if payload["attestation"] is None:
        raise ValueError("attestation required")
    payload["attestation"].pop("signature")
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def request_scope_hash(request: EvaluationRequest) -> str:
    scope = request.model_dump(mode="json", exclude={"request_id", "evidence"})
    canonical = json.dumps(scope, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class EvidenceVerifier:
    """Deterministic, explainable evidence-quality gate.

    VeriWeave research methods can later replace or augment this adapter while
    preserving the governance API and decision contract.
    """

    def __init__(
        self, trusted_sources: dict[str, TrustedEvidenceSource] | None = None,
        keys: dict[str, str] | None = None,
    ) -> None:
        # No configuration retains the explicitly labelled demonstration adapter.
        self.trusted_sources = dict(trusted_sources) if trusted_sources is not None else None
        self._keys = dict(keys or {})

    @classmethod
    def from_config(cls, path: Path) -> EvidenceVerifier:
        config = json.loads(path.read_text(encoding="utf-8"))
        sources = {
            source_id: TrustedEvidenceSource(
                authority=row["authority"], versions=tuple(row["versions"]),
                evidence_types=tuple(row["evidence_types"]), key_ids=tuple(row["key_ids"]),
            ) for source_id, row in config["sources"].items()
        }
        for source in sources.values():
            if not 0 <= source.authority <= 100 or not source.key_ids:
                raise ValueError("source requires authority in [0,100] and trusted key IDs")
            if any(key_id not in config["keys"] for key_id in source.key_ids):
                raise ValueError("trusted source refers to an unavailable signing key")
        return cls(sources, config["keys"])

    @property
    def verifier_id(self) -> str:
        payload = {
            "algorithm": "evidence-verifier/v2",
            "mode": "attested" if self.trusted_sources is not None else "demo-metadata",
            "sources": {name: source.__dict__ for name, source in (self.trusted_sources or {}).items()},
            "key_fingerprints": {
                name: hashlib.sha256(key.encode("utf-8")).hexdigest()
                for name, key in self._keys.items()
            },
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

    def _admission_errors(
        self, item: EvidenceItem, request: EvaluationRequest | None, evaluated_at: datetime,
    ) -> list[str]:
        source = (self.trusted_sources or {}).get(item.source_id)
        attestation = item.attestation
        errors = []
        if source is None:
            return ["untrusted evidence source"]
        if item.source_version not in source.versions:
            errors.append("unapproved source version")
        if item.evidence_type not in source.evidence_types:
            errors.append("source not authorized for evidence type")
        if attestation is None:
            return [*errors, "missing connector attestation (signed flag is insufficient)"]
        key = self._keys.get(attestation.key_id)
        if key is None or attestation.key_id not in source.key_ids:
            errors.append("untrusted attestation key")
        else:
            expected = hmac.new(key.encode("utf-8"), attestation_payload(item), hashlib.sha256)
            if not hmac.compare_digest(expected.hexdigest().encode(), attestation.signature.encode()):
                errors.append("invalid evidence HMAC")
        if not attestation.issued_at <= evaluated_at < attestation.expires_at:
            errors.append("attestation outside validity window")
        scope = ("tenant_id", "agent_id", "action", "resource")
        if request is None or any(
            getattr(attestation, field) != getattr(request, field) for field in scope
        ) or attestation.request_hash != request_scope_hash(request):
            errors.append("attestation request scope mismatch")
        return errors

    def assess(
        self, evidence: list[EvidenceItem], *, request: EvaluationRequest | None = None,
        evaluated_at: datetime | None = None,
    ) -> list[EvidenceAssessment]:
        evaluated_at = evaluated_at or datetime.now(UTC)
        duplicate_counts: dict[tuple[str, str], int] = defaultdict(int)
        for item in evidence:
            duplicate_counts[(item.source_id, item.content.strip().lower())] += 1

        results: list[EvidenceAssessment] = []
        for item in evidence:
            score = 0.0
            reasons: list[str] = []

            source = (self.trusted_sources or {}).get(item.source_id)
            authority = source.authority if source else item.authority
            score += authority / 100.0 * 0.35
            reasons.append(f"authority={authority}/100")

            if item.current:
                score += 0.20
                reasons.append("current source version")
            else:
                reasons.append("source marked non-current")

            if item.signed:
                score += 0.15
                reasons.append("signed evidence")
            else:
                reasons.append("unsigned evidence")

            if len(item.content.split()) >= 8:
                score += 0.15
                reasons.append("substantive content")
            else:
                reasons.append("content too short")

            if re.search(
                r"\b(section|article|control|policy|requirement|clause)\b",
                item.content,
                re.IGNORECASE,
            ):
                score += 0.10
                reasons.append("contains policy reference language")

            if duplicate_counts[(item.source_id, item.content.strip().lower())] == 1:
                score += 0.05
            else:
                reasons.append("duplicate evidence")

            score = min(round(score, 4), 1.0)
            errors = (
                self._admission_errors(item, request, evaluated_at)
                if self.trusted_sources is not None else []
            )
            if item.metadata.get("contradiction"):
                errors.append("conflicting evidence requires review")
            reasons.extend(errors)
            if self.trusted_sources is None:
                reasons.append("demo metadata adapter; authenticity not established")
            results.append(
                EvidenceAssessment(
                    evidence_id=item.evidence_id,
                    accepted=score >= 0.55 and item.current and not errors,
                    score=score,
                    reasons=reasons,
                )
            )
        return results
