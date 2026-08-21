# ruff: noqa: I001
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib import error, request


DEFAULT_OLLAMA_MODEL = "gemma4:31b-cloud"


@dataclass
class StageResult:
    name: str
    status: str
    duration_seconds: float
    command: list[str]
    error: str | None = None


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _env_int(name: str, default: int, minimum: int = 1) -> int:
    value = int(os.getenv(name, str(default)))
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return value


def _wait_json(url: str, timeout_seconds: float = 60.0) -> object:
    deadline = time.monotonic() + timeout_seconds
    last_error = "endpoint unavailable"
    while time.monotonic() < deadline:
        try:
            with request.urlopen(url, timeout=5.0) as response:
                if 200 <= response.status < 300:
                    raw = response.read().decode("utf-8")
                    return json.loads(raw) if raw else {}
                last_error = f"HTTP {response.status}"
        except (error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            last_error = str(exc)
        time.sleep(1.0)
    raise RuntimeError(f"Timed out waiting for {url}: {last_error}")


def _post_json(
    url: str,
    payload: dict[str, object],
    timeout: float = 90.0,
) -> dict[str, object]:
    http_request = request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with request.urlopen(http_request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _ollama_model_names(payload: object) -> set[str]:
    if not isinstance(payload, dict):
        return set()
    models = payload.get("models", [])
    if not isinstance(models, list):
        return set()
    names: set[str] = set()
    for item in models:
        if not isinstance(item, dict):
            continue
        for field in ("name", "model"):
            value = item.get(field)
            if isinstance(value, str) and value:
                names.add(value)
    return names


def _probe_ollama(base_url: str, model: str) -> dict[str, object]:
    started = time.perf_counter()
    payload = _post_json(
        f"{base_url}/api/chat",
        {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "This is a publication-pipeline output-contract probe. "
                        "Return ONLY valid JSON with exactly two keys: decision and reason. "
                        "Set decision to review and reason to connectivity probe. "
                        "Do not use Markdown, code fences, or any text outside the JSON object."
                    ),
                }
            ],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0},
        },
        timeout=float(os.getenv("OLLAMA_PROBE_TIMEOUT", "120")),
    )
    message = payload.get("message", {})
    content = message.get("content", "") if isinstance(message, dict) else ""
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError(f"Ollama model {model!r} returned no message content during probe")
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Ollama model {model!r} did not honor JSON mode during probe: {content[:160]!r}"
        ) from exc
    decision = str(parsed.get("decision", "")).strip().lower()
    reason = str(parsed.get("reason", "")).strip()
    if decision not in {"allow", "review", "deny"} or not reason:
        raise RuntimeError(
            f"Ollama model {model!r} returned an invalid governance JSON contract: {parsed!r}"
        )
    return {
        "probe_passed": True,
        "probe_latency_ms": round((time.perf_counter() - started) * 1000, 3),
        "probe_decision": decision,
        "resolved_model": str(payload.get("model", model)),
    }


def preflight() -> dict[str, object]:
    opa_url = os.getenv("OPA_URL", "http://opa:8181").rstrip("/")
    ollama_url = os.getenv(
        "OLLAMA_BASE_URL", "http://host.docker.internal:11434"
    ).rstrip("/")
    ollama_model = os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)

    print(f"[preflight] waiting for OPA at {opa_url}", flush=True)
    _wait_json(f"{opa_url}/health?plugins", timeout_seconds=60.0)

    print(f"[preflight] checking host Ollama at {ollama_url}", flush=True)
    tags = _wait_json(f"{ollama_url}/api/tags", timeout_seconds=30.0)
    available = _ollama_model_names(tags)
    if available and ollama_model not in available:
        rendered = ", ".join(sorted(available))
        print(
            f"[preflight] model {ollama_model!r} is not listed by /api/tags; "
            f"visible models: {rendered}. Trying a real /api/chat invocation anyway.",
            flush=True,
        )

    print(f"[preflight] invoking real Ollama model: {ollama_model}", flush=True)
    try:
        probe = _probe_ollama(ollama_url, ollama_model)
    except (error.URLError, TimeoutError, OSError, RuntimeError, json.JSONDecodeError) as exc:
        rendered = ", ".join(sorted(available)) or "<none>"
        raise RuntimeError(
            f"Real Ollama invocation failed for {ollama_model!r} at {ollama_url}: {exc}. "
            f"Models visible to /api/tags: {rendered}. The pipeline never pulls models automatically."
        ) from exc

    print(
        f"[preflight] real Ollama JSON invocation succeeded: {ollama_model} "
        f"-> {probe['resolved_model']} ({probe['probe_latency_ms']} ms)",
        flush=True,
    )
    return {
        "opa_url": opa_url,
        "ollama_base_url": ollama_url,
        "ollama_model": ollama_model,
        "ollama_resolved_model": probe["resolved_model"],
        "ollama_probe_passed": probe["probe_passed"],
        "ollama_probe_latency_ms": probe["probe_latency_ms"],
        "ollama_probe_decision": probe["probe_decision"],
        "model_pull_performed": False,
    }


def build_stages(results_root: Path) -> list[tuple[str, list[str]]]:
    publication_dir = results_root / "publication"
    research_dir = results_root / "research-v1"
    benchmark_scenarios = Path(
        os.getenv("BENCHMARK_SCENARIOS", "/app/benchmark/scenarios.json")
    )

    seeds = _env_int("GOVERNBENCH_SEEDS", 30)
    cases = _env_int("GOVERNBENCH_CASES", 2000)
    bootstrap_samples = _env_int("PUBLICATION_BOOTSTRAP_SAMPLES", 10000, 1000)
    bootstrap_seed = _env_int("PUBLICATION_BOOTSTRAP_SEED", 20260817, 0)

    return [
        (
            "governbench",
            [
                sys.executable,
                "-m",
                "research.experiments",
                "--seeds",
                str(seeds),
                "--cases",
                str(cases),
                "--output",
                str(research_dir),
            ],
        ),
        (
            "service-benchmark",
            [
                sys.executable,
                "-m",
                "benchmark.runner",
                "--base-url",
                os.getenv("BENCHMARK_BASE_URL", "http://govern:8080"),
                "--scenarios",
                str(benchmark_scenarios),
                "--results-dir",
                str(results_root),
                "--iterations",
                str(_env_int("BENCHMARK_ITERATIONS", 10)),
                "--concurrency",
                str(_env_int("BENCHMARK_CONCURRENCY", 4)),
            ],
        ),
        (
            "legal-audit",
            [
                sys.executable,
                "-m",
                "research.legal_audit",
                "--validation-dir",
                "research/validation",
                "--output",
                str(publication_dir / "legal-audit.json"),
            ],
        ),
        (
            "publication-validation",
            [
                sys.executable,
                "-m",
                "research.regulatory_validation",
                "--opa",
                "--cedar",
                "--ollama",
                "--require-external",
                "--output",
                str(publication_dir),
            ],
        ),
        (
            "publication-statistics",
            [
                sys.executable,
                "-m",
                "research.publication_statistics",
                "--predictions",
                str(publication_dir / "predictions.csv"),
                "--output",
                str(publication_dir / "statistics.json"),
                "--samples",
                str(bootstrap_samples),
                "--seed",
                str(bootstrap_seed),
            ],
        ),
        (
            "calibration-reliability",
            [
                sys.executable,
                "-m",
                "research.reliability_report",
                "--report",
                str(publication_dir / "report.json"),
                "--output",
                str(publication_dir / "calibration-reliability.svg"),
            ],
        ),
        (
            "load-matrix",
            [
                sys.executable,
                "-m",
                "benchmark.load_matrix",
                "--base-url",
                os.getenv("BENCHMARK_BASE_URL", "http://govern:8080"),
                "--scenarios",
                str(benchmark_scenarios),
                "--results-dir",
                str(results_root),
                "--requests-per-level",
                str(_env_int("LOAD_MATRIX_REQUESTS_PER_LEVEL", 10000)),
                "--concurrencies",
                os.getenv("LOAD_MATRIX_CONCURRENCIES", "1,4,16,32"),
            ],
        ),
    ]


def _expected_artifacts(results_root: Path) -> list[Path]:
    publication = results_root / "publication"
    research = results_root / "research-v1"
    return [
        research / "report.json",
        research / "report.html",
        research / "baseline-runs.csv",
        results_root / "benchmark-results.json",
        results_root / "benchmark-report.html",
        publication / "legal-audit.json",
        publication / "report.json",
        publication / "report.html",
        publication / "statistics.json",
        publication / "statistics.html",
        publication / "predictions.csv",
        publication / "external-details.jsonl",
        publication / "calibration-reliability.svg",
        publication / "annotator-a.csv",
        publication / "annotator-b.csv",
        publication / "adjudication.csv",
        results_root / "load-matrix.json",
        results_root / "load-matrix.html",
    ]


def _write_summary(
    path: Path,
    *,
    started_at: str,
    finished_at: str,
    status: str,
    preflight_info: dict[str, object],
    stages: list[StageResult],
    artifacts: list[Path],
) -> None:
    payload = {
        "schema": "veriweave-full-publication-pipeline/v1",
        "status": status,
        "started_at": started_at,
        "finished_at": finished_at,
        "preflight": preflight_info,
        "stages": [asdict(stage) for stage in stages],
        "artifacts": [
            {
                "path": str(item),
                "exists": item.is_file(),
                "size": item.stat().st_size if item.is_file() else 0,
            }
            for item in artifacts
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def main() -> int:
    results_root = Path(os.getenv("PIPELINE_RESULTS_DIR", "/app/results"))
    results_root.mkdir(parents=True, exist_ok=True)
    summary_path = results_root / "pipeline-summary.json"
    started_at = _utc_now()
    stage_results: list[StageResult] = []
    preflight_info: dict[str, object] = {}

    try:
        preflight_info = preflight()
        for name, command in build_stages(results_root):
            print(f"\n=== {name} ===", flush=True)
            print(" ".join(command), flush=True)
            started = time.perf_counter()
            try:
                subprocess.run(command, check=True)
            except subprocess.CalledProcessError as exc:
                duration = time.perf_counter() - started
                stage_results.append(
                    StageResult(
                        name,
                        "failed",
                        duration,
                        command,
                        f"exit code {exc.returncode}",
                    )
                )
                raise
            duration = time.perf_counter() - started
            stage_results.append(StageResult(name, "success", duration, command))

        artifacts = _expected_artifacts(results_root)
        missing = [item for item in artifacts if not item.is_file() or item.stat().st_size == 0]
        if missing:
            raise RuntimeError(
                "Pipeline completed but required artifacts are missing/empty: "
                + ", ".join(str(item) for item in missing)
            )

        _write_summary(
            summary_path,
            started_at=started_at,
            finished_at=_utc_now(),
            status="success",
            preflight_info=preflight_info,
            stages=stage_results,
            artifacts=artifacts,
        )
        print(f"\nFULL PUBLICATION PIPELINE PASSED: {summary_path}", flush=True)
        return 0
    except (
        subprocess.CalledProcessError,
        RuntimeError,
        ValueError,
        error.URLError,
        TimeoutError,
        OSError,
        json.JSONDecodeError,
    ) as exc:
        artifacts = _expected_artifacts(results_root)
        _write_summary(
            summary_path,
            started_at=started_at,
            finished_at=_utc_now(),
            status="failed",
            preflight_info=preflight_info,
            stages=stage_results,
            artifacts=artifacts,
        )
        print(f"\nFULL PUBLICATION PIPELINE FAILED: {exc}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
