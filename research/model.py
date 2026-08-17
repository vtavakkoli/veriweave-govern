from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Decision = Literal["allow", "review", "deny"]


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    evidence_type: str
    source_id: str
    authority: int
    current: bool
    signed: bool
    content: str
    label_valid: bool
    contradiction: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GovernCase:
    case_id: str
    seed: int
    domain: str
    category: str
    action: str
    resource: str
    purpose: str
    impact: str
    environment: str
    data_classification: str
    external: bool
    required_evidence: tuple[str, ...]
    evidence: tuple[Evidence, ...]
    ground_truth: Decision
    attack_type: str | None = None
    temporal_policy_version: int = 1
    notes: str = ""
    prohibition_reason: str | None = None
    legal_basis: tuple[str, ...] = ()
    evaluation_date: str | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["required_evidence"] = list(self.required_evidence)
        value["evidence"] = [item.to_dict() for item in self.evidence]
        value["legal_basis"] = list(self.legal_basis)
        return value
