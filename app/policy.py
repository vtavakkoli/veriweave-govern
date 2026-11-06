from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from app.models import Decision, EvaluationRequest


class Predicate(BaseModel):
    model_config = ConfigDict(frozen=True)
    field: str = Field(min_length=1)
    operator: str = Field(default="eq")
    value: Any = None

    @field_validator("operator")
    @classmethod
    def supported_operator(cls, value: str) -> str:
        value = value.lower()
        if value not in {
            "exists", "eq", "neq", "in", "not_in", "contains", "starts_with", "gte",
            "lte", "truthy",
        }:
            raise ValueError(f"unsupported predicate operator: {value}")
        return value


class PolicyRule(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str = Field(min_length=1)
    description: str = ""
    when: tuple[Predicate, ...] = ()
    decision: Decision = Decision.REVIEW
    required_evidence: tuple[str, ...] = ()
    min_evidence_score: float = Field(default=0.55, ge=0.0, le=1.0)
    review_queue: str | None = None
    reason: str = "Policy rule matched"


class PolicyDocument(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    status: str = "active"
    owner: str = "governance"
    effective_from: date | None = None
    tags: tuple[str, ...] = ()
    rules: tuple[PolicyRule, ...] = Field(min_length=1)


@dataclass(frozen=True)
class LoadedPolicy:
    document: PolicyDocument
    content_hash: str
    path: Path
    raw_text: str


@dataclass(frozen=True)
class PolicySnapshot:
    policies: tuple[LoadedPolicy, ...]
    policy_set_hash: str


def _snapshot(policies: list[LoadedPolicy]) -> PolicySnapshot:
    payload = "|".join(sorted(policy.content_hash for policy in policies))
    return PolicySnapshot(tuple(policies), hashlib.sha256(payload.encode("utf-8")).hexdigest())


class PolicyLoadError(RuntimeError):
    pass


class PolicyStore:
    def __init__(self, policy_dir: Path, snapshot_dir: Path | None = None) -> None:
        self.policy_dir = policy_dir
        self.snapshot_dir = snapshot_dir
        self._lock = threading.RLock()
        self._history: dict[str, PolicySnapshot] = {}
        self._active = _snapshot([])
        self.reload()

    @property
    def policies(self) -> list[LoadedPolicy]:
        return list(self.capture().policies)

    @property
    def policy_set_hash(self) -> str:
        return self.capture().policy_set_hash

    def capture(self) -> PolicySnapshot:
        # One reference swap binds matching and the reported hash to the same bundle.
        with self._lock:
            return self._active

    def historical(self, policy_set_hash: str) -> PolicySnapshot:
        if len(policy_set_hash) != 64 or any(c not in "0123456789abcdef" for c in policy_set_hash):
            raise PolicyLoadError("invalid policy hash")
        with self._lock:
            if self.snapshot_dir is None:
                try:
                    return self._history[policy_set_hash]
                except KeyError as exc:
                    raise PolicyLoadError("historical policy unavailable") from exc
            path = self.snapshot_dir / f"{policy_set_hash}.json"
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                if payload["schema"] != "veriweave-policy-snapshot/v1":
                    raise ValueError("unsupported snapshot schema")
                loaded = []
                for row in payload["policies"]:
                    text = row["raw_text"]
                    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
                    if digest != row["content_hash"]:
                        raise ValueError("policy content hash mismatch")
                    document = PolicyDocument.model_validate(yaml.safe_load(text))
                    loaded.append(LoadedPolicy(document, digest, Path(row["name"]), text))
                snapshot = _snapshot(loaded)
                if snapshot.policy_set_hash != policy_set_hash:
                    raise ValueError("policy set hash mismatch")
                return snapshot
            except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as exc:
                raise PolicyLoadError(f"historical policy unavailable or corrupt: {exc}") from exc

    def reload(self) -> None:
        loaded: list[LoadedPolicy] = []
        if not self.policy_dir.exists():
            raise PolicyLoadError(f"Policy directory does not exist: {self.policy_dir}")

        for path in sorted(self.policy_dir.glob("*.y*ml")):
            raw_text = path.read_text(encoding="utf-8")
            try:
                raw = yaml.safe_load(raw_text)
                document = PolicyDocument.model_validate(raw)
            except (yaml.YAMLError, ValidationError) as exc:
                raise PolicyLoadError(f"Invalid policy {path}: {exc}") from exc

            if document.status.lower() != "active":
                continue
            loaded.append(
                LoadedPolicy(
                    document=document,
                    content_hash=hashlib.sha256(raw_text.encode("utf-8")).hexdigest(),
                    path=path,
                    raw_text=raw_text,
                )
            )

        if not loaded:
            raise PolicyLoadError(f"No active YAML policies found in {self.policy_dir}")
        identities = [(item.document.id, item.document.version) for item in loaded]
        if len(identities) != len(set(identities)):
            raise PolicyLoadError("duplicate policy identity/version")
        for item in loaded:
            ids = [rule.id for rule in item.document.rules]
            if len(ids) != len(set(ids)):
                raise PolicyLoadError("duplicate rule identifier")
        snapshot = _snapshot(loaded)
        with self._lock:
            if self.snapshot_dir is not None:
                self.snapshot_dir.mkdir(parents=True, exist_ok=True)
                path = self.snapshot_dir / f"{snapshot.policy_set_hash}.json"
                if path.exists():
                    self.historical(snapshot.policy_set_hash)  # fail on corrupt existing archives
                else:
                    payload = {
                        "schema": "veriweave-policy-snapshot/v1",
                        "policies": [
                            {"name": p.path.name, "raw_text": p.raw_text,
                             "content_hash": p.content_hash} for p in snapshot.policies
                        ],
                    }
                    # Exclusive creation never overwrites a historical snapshot.
                    with path.open("x", encoding="utf-8") as handle:
                        json.dump(payload, handle, sort_keys=True)
            self._history[snapshot.policy_set_hash] = snapshot
            self._active = snapshot

    def describe(self) -> list[dict[str, Any]]:
        return [
            {
                "id": item.document.id,
                "name": item.document.name,
                "version": item.document.version,
                "owner": item.document.owner,
                "tags": list(item.document.tags),
                "rules": len(item.document.rules),
                "content_hash": item.content_hash,
            }
            for item in self.capture().policies
        ]


def request_field(request: EvaluationRequest, dotted_field: str) -> Any:
    roots: dict[str, Any] = {
        "tenant_id": request.tenant_id,
        "agent_id": request.agent_id,
        "action": request.action,
        "resource": request.resource,
        "purpose": request.purpose,
        "context": request.context,
    }
    parts = dotted_field.split(".")
    current: Any = roots.get(parts[0])
    for part in parts[1:]:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def predicate_matches(request: EvaluationRequest, predicate: Predicate) -> bool:
    actual = request_field(request, predicate.field)
    expected = predicate.value
    operator = predicate.operator.lower()

    if operator == "exists":
        return actual is not None
    if operator == "eq":
        return actual == expected
    if operator == "neq":
        return actual != expected
    if operator == "in":
        return actual in expected if isinstance(expected, (list, tuple, set)) else False
    if operator == "not_in":
        return actual not in expected if isinstance(expected, (list, tuple, set)) else False
    if operator == "contains":
        return expected in actual if isinstance(actual, (str, list, tuple, set, dict)) else False
    if operator == "starts_with":
        return isinstance(actual, str) and isinstance(expected, str) and actual.startswith(expected)
    if operator == "gte":
        try:
            return actual is not None and actual >= expected
        except TypeError:
            return False
    if operator == "lte":
        try:
            return actual is not None and actual <= expected
        except TypeError:
            return False
    if operator == "truthy":
        return bool(actual) is bool(expected)
    raise PolicyLoadError(f"Unsupported predicate operator: {predicate.operator}")


def rule_matches(request: EvaluationRequest, rule: PolicyRule) -> bool:
    return all(predicate_matches(request, predicate) for predicate in rule.when)


def canonical_policy_json(policy: PolicyDocument) -> str:
    return json.dumps(policy.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
