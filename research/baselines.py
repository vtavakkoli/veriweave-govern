from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass

from research.calibration import EvidenceCalibrationModel
from research.governor import decide
from research.model import GovernCase


@dataclass(frozen=True)
class BaselineResult:
    name: str
    decision: str
    available: bool = True
    note: str = ""


def rbac(case: GovernCase) -> str:
    if case.action in {"read", "search", "summarize", "classify", "draft"}:
        return "allow"
    if case.action in {"send_external", "delete_production", "wire_transfer"}:
        return "deny"
    return "review"


def abac(case: GovernCase) -> str:
    if case.external and case.data_classification in {"secret", "restricted"}:
        return "deny"
    if case.impact in {"high", "critical"}:
        return "review"
    return "allow"


def llm_proxy(case: GovernCase) -> str:
    """Deterministic language-style proxy baseline; not an actual LLM result."""
    text = " ".join([case.action, case.resource, case.purpose, *[item.content for item in case.evidence]]).lower()
    if any(term in text for term in ("secret", "delete_production", "wire_transfer")):
        return "deny"
    if any(term in text for term in ("approve", "deploy", "unknown", "unregistered")):
        return "review"
    return "allow"


def veriweave(case: GovernCase, calibration: EvidenceCalibrationModel) -> str:
    return decide(case, calibration).decision


def external_json_baseline(name: str, executable: str, case: GovernCase) -> BaselineResult:
    """Run an optional OPA/Cedar adapter executable using JSON stdin/stdout."""
    path = shutil.which(executable)
    if not path:
        return BaselineResult(name=name, decision="review", available=False, note=f"{executable} not installed")
    proc = subprocess.run([path], input=json.dumps(case.to_dict()), text=True, capture_output=True, check=False, timeout=10)
    if proc.returncode != 0:
        return BaselineResult(name=name, decision="review", available=False, note=proc.stderr.strip())
    payload = json.loads(proc.stdout)
    return BaselineResult(name=name, decision=str(payload["decision"]))
