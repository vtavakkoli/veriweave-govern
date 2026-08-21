from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from research.model import GovernCase

DECISIONS = {"allow", "review", "deny"}
DEFAULT_OLLAMA_MODEL = "gemma4:31b-cloud"


@dataclass(frozen=True)
class ExternalDecision:
    name: str
    decision: str
    available: bool
    latency_ms: float
    detail: str = ""


def _features(case: GovernCase) -> dict[str, object]:
    accepted_types = {
        item.evidence_type
        for item in case.evidence
        if item.label_valid and not item.contradiction
    }
    return {
        "case_id": case.case_id,
        "action": case.action,
        "impact": case.impact,
        "external": case.external,
        "data_classification": case.data_classification,
        "prohibited": bool(case.prohibition_reason),
        "high_impact": case.impact in {"high", "critical"},
        "unknown_action": case.action in {
            "invoke_unknown_tool",
            "delegate_unregistered",
            "opaque_side_effect",
        },
        "evidence_complete": all(
            required in accepted_types for required in case.required_evidence
        ),
    }


def _post_json(url: str, payload: dict[str, object], timeout: float) -> dict[str, Any]:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def opa_decision(case: GovernCase, *, timeout: float = 10.0) -> ExternalDecision:
    base_url = os.getenv("OPA_URL", "http://opa:8181").rstrip("/")
    started = time.perf_counter()
    last_error = "OPA did not become available"
    for attempt in range(10):
        try:
            payload = _post_json(
                f"{base_url}/v1/data/veriweave/decision",
                {"input": _features(case)},
                timeout,
            )
            decision = str(payload.get("result", "")).lower()
            if decision not in DECISIONS:
                raise ValueError(f"unexpected OPA result: {payload!r}")
            return ExternalDecision(
                "opa",
                decision,
                True,
                (time.perf_counter() - started) * 1000,
            )
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            last_error = str(exc)
            if attempt < 9:
                time.sleep(0.5)
        except (ValueError, json.JSONDecodeError) as exc:
            last_error = str(exc)
            break
    return ExternalDecision(
        "opa",
        "review",
        False,
        (time.perf_counter() - started) * 1000,
        last_error,
    )


def _run_cedar_policy(
    case: GovernCase,
    policy: Path,
    *,
    timeout: float,
) -> tuple[bool | None, str]:
    binary = os.getenv("CEDAR_BIN", "cedar")
    features = _features(case)
    request_payload = {
        "principal": 'BenchmarkPrincipal::"publication"',
        "action": 'Action::"evaluate"',
        "resource": f'Case::"{case.case_id}"',
        "context": {
            "prohibited": features["prohibited"],
            "external": features["external"],
            "protectedData": case.data_classification in {"secret", "restricted"},
            "highImpact": features["high_impact"],
            "unknownAction": features["unknown_action"],
            "evidenceComplete": features["evidence_complete"],
        },
    }
    try:
        with tempfile.TemporaryDirectory(prefix="veriweave-cedar-") as tmp:
            tmpdir = Path(tmp)
            request_file = tmpdir / "request.json"
            entities_file = tmpdir / "entities.json"
            request_file.write_text(json.dumps(request_payload), encoding="utf-8")
            entities_file.write_text("[]", encoding="utf-8")
            proc = subprocess.run(
                [
                    binary,
                    "authorize",
                    "--request-json",
                    str(request_file),
                    "--policies",
                    str(policy),
                    "--entities",
                    str(entities_file),
                ],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, str(exc)

    output = (proc.stdout + "\n" + proc.stderr).strip()
    if proc.returncode == 0 and "ALLOW" in proc.stdout:
        return True, output
    if proc.returncode == 2 and "DENY" in proc.stdout:
        return False, output
    return None, output or f"cedar exited {proc.returncode}"


def cedar_decision(case: GovernCase, *, timeout: float = 10.0) -> ExternalDecision:
    policy_dir = Path(
        os.getenv(
            "CEDAR_POLICY_DIR",
            "research/policy_baselines/cedar",
        )
    )
    started = time.perf_counter()
    deny, detail = _run_cedar_policy(case, policy_dir / "deny.cedar", timeout=timeout)
    if deny is None:
        return ExternalDecision(
            "cedar",
            "review",
            False,
            (time.perf_counter() - started) * 1000,
            detail,
        )
    if deny:
        return ExternalDecision(
            "cedar",
            "deny",
            True,
            (time.perf_counter() - started) * 1000,
        )

    allow, detail = _run_cedar_policy(case, policy_dir / "allow.cedar", timeout=timeout)
    if allow is None:
        return ExternalDecision(
            "cedar",
            "review",
            False,
            (time.perf_counter() - started) * 1000,
            detail,
        )
    return ExternalDecision(
        "cedar",
        "allow" if allow else "review",
        True,
        (time.perf_counter() - started) * 1000,
    )


def _legal_context(case: GovernCase, source_registry: dict[str, dict[str, object]]) -> str:
    lines = []
    for source_id in case.legal_basis:
        source = source_registry.get(source_id)
        if source:
            lines.append(
                f"- {source['instrument']} {source['provision']}: "
                f"{source['benchmark_summary']}"
            )
    return "\n".join(lines)


def ollama_decision(
    case: GovernCase,
    source_registry: dict[str, dict[str, object]],
    *,
    timeout: float = 120.0,
) -> ExternalDecision:
    base_url = os.getenv(
        "OLLAMA_BASE_URL",
        "http://host.docker.internal:11434",
    ).rstrip("/")
    model = os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
    facts = {
        "action": case.action,
        "resource": case.resource,
        "purpose": case.purpose,
        "impact": case.impact,
        "environment": case.environment,
        "data_classification": case.data_classification,
        "external": case.external,
        "required_evidence": list(case.required_evidence),
        "provided_evidence_types": [item.evidence_type for item in case.evidence],
        "evaluation_date": case.evaluation_date,
    }
    prompt = (
        "You are a conservative governance decision baseline. Decide only among "
        "allow, review, deny. Use only the supplied case facts and source summaries. "
        "Use deny only when the supplied facts clearly match a prohibition or an "
        "unacceptable disclosure. Use review when human/legal/privacy/security "
        "assessment or missing evidence is required. Do not invent exceptions or facts. "
        "Return ONLY valid JSON with exactly two keys: decision and reason. "
        "The decision value MUST be one of allow, review, deny. Do not use Markdown, "
        "code fences, headings, or text outside the JSON object.\n\n"
        f"CASE FACTS:\n{json.dumps(facts, indent=2, sort_keys=True)}\n\n"
        f"OFFICIAL-SOURCE SUMMARIES:\n{_legal_context(case, source_registry)}"
    )
    started = time.perf_counter()
    try:
        payload = _post_json(
            f"{base_url}/api/chat",
            {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "format": "json",
                "options": {"temperature": 0},
            },
            timeout,
        )
        content = payload.get("message", {}).get("content", "")
        parsed = json.loads(content)
        decision = str(parsed.get("decision", "")).strip().lower()
        if decision not in DECISIONS:
            raise ValueError(f"unexpected Ollama decision: {parsed!r}")
        reason = str(parsed.get("reason", "")).strip()
        resolved_model = str(payload.get("model", model))
        return ExternalDecision(
            "ollama",
            decision,
            True,
            (time.perf_counter() - started) * 1000,
            (
                f"requested_model={model}; resolved_model={resolved_model}; "
                f"reason={reason}"
            ),
        )
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
        return ExternalDecision(
            "ollama",
            "review",
            False,
            (time.perf_counter() - started) * 1000,
            f"model={model}; error={exc}",
        )
