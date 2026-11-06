from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


class Decision(StrEnum):
    ALLOW = "allow"
    REVIEW = "review"
    DENY = "deny"


class EvidenceAttestation(BaseModel):
    key_id: str = Field(min_length=1, max_length=100)
    issued_at: datetime
    expires_at: datetime
    tenant_id: str
    agent_id: str
    action: str
    resource: str
    request_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    signature: str = Field(max_length=128)

    @model_validator(mode="after")
    def validate_time_window(self) -> EvidenceAttestation:
        if self.issued_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("attestation timestamps must include a timezone")
        if self.expires_at <= self.issued_at:
            raise ValueError("attestation expiry must follow issuance")
        return self


class EvidenceItem(BaseModel):
    evidence_id: str = Field(min_length=1, max_length=200)
    source_id: str = Field(min_length=1, max_length=200)
    source_version: str = Field(min_length=1, max_length=100)
    evidence_type: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1, max_length=20_000)
    authority: int = Field(default=50, ge=0, le=100)
    current: bool = True
    signed: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    attestation: EvidenceAttestation | None = None


class EvaluationRequest(BaseModel):
    tenant_id: str = Field(default="default", min_length=1, max_length=100)
    agent_id: str = Field(min_length=1, max_length=200)
    action: str = Field(min_length=1, max_length=200)
    resource: str = Field(default="", max_length=500)
    purpose: str = Field(default="", max_length=1_000)
    context: dict[str, Any] = Field(default_factory=dict)
    evidence: list[EvidenceItem] = Field(default_factory=list, max_length=100)
    request_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=200)

    @field_validator("action", "resource", "purpose")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def validate_identifiers(self) -> EvaluationRequest:
        ids = [item.evidence_id for item in self.evidence]
        if len(ids) != len(set(ids)):
            raise ValueError("evidence_id values must be unique within a request")
        if not self.action:
            raise ValueError("action must not be whitespace")
        return self


class EvidenceAssessment(BaseModel):
    evidence_id: str
    accepted: bool
    score: float = Field(ge=0.0, le=1.0)
    reasons: list[str] = Field(default_factory=list)


class RuleResult(BaseModel):
    policy_id: str
    policy_version: str
    rule_id: str
    matched: bool
    decision: Decision
    reasons: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    review_queue: str | None = None


class AuditEnvelope(BaseModel):
    record_id: str
    created_at: datetime
    record_hash: str
    previous_hash: str
    signature: str | None = None


class EvaluationResponse(BaseModel):
    request_id: str
    decision: Decision
    reasons: list[str]
    matched_rules: list[RuleResult]
    evidence_assessments: list[EvidenceAssessment]
    policy_set_hash: str
    evaluated_at: datetime
    evidence_verifier_id: str
    audit: AuditEnvelope
    review_queue: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ReplayRequest(BaseModel):
    record_id: str = Field(min_length=1, max_length=200)
    expected_policy_set_hash: str | None = None
