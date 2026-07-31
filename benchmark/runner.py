from __future__ import annotations

import argparse
import html
import json
import os
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from statistics import fmean, median
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass
class HttpResult:
    status: int
    body: Any
    latency_ms: float
    error: str | None = None


@dataclass
class ScenarioResult:
    scenario_id: str
    name: str
    category: str
    description: str
    passed: bool
    expected_status: int
    actual_status: int
    expected_decision: str | None
    actual_decision: str | None
    review_queue: str | None
    matched_rules: list[str]
    evidence_scores: list[float]
    latency_ms: float
    errors: list[str]
    request: dict[str, Any]
    response: Any


def percentile(values: list[float], percentile_value: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * percentile_value
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def request_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    timeout: float = 10.0,
) -> HttpResult:
    encoded = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        url,
        data=encoded,
        method=method,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    started = time.perf_counter()
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            body = json.loads(raw) if raw else None
            return HttpResult(
                status=response.status,
                body=body,
                latency_ms=(time.perf_counter() - started) * 1000,
            )
    except HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            body = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            body = raw
        return HttpResult(
            status=exc.code,
            body=body,
            latency_ms=(time.perf_counter() - started) * 1000,
            error=str(exc),
        )
    except (URLError, TimeoutError, OSError) as exc:
        return HttpResult(
            status=0,
            body=None,
            latency_ms=(time.perf_counter() - started) * 1000,
            error=str(exc),
        )


def wait_for_service(base_url: str, timeout_seconds: float) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    last_error = "service did not respond"
    while time.monotonic() < deadline:
        result = request_json("GET", f"{base_url}/health", timeout=3.0)
        if result.status == 200 and isinstance(result.body, dict):
            return result.body
        last_error = result.error or f"HTTP {result.status}"
        time.sleep(1.0)
    raise RuntimeError(f"VeriWeave Govern did not become healthy: {last_error}")


def _flatten_missing_evidence(body: dict[str, Any]) -> list[str]:
    return [
        item
        for rule in body.get("matched_rules", [])
        for item in rule.get("missing_evidence", [])
    ]


def validate_response(
    scenario: dict[str, Any],
    http_result: HttpResult,
) -> tuple[list[str], dict[str, Any]]:
    expected = scenario["expect"]
    body = http_result.body if isinstance(http_result.body, dict) else {}
    errors: list[str] = []

    expected_status = int(expected.get("status", 200))
    if http_result.status != expected_status:
        errors.append(f"expected HTTP {expected_status}, received {http_result.status}")

    expected_decision = expected.get("decision")
    actual_decision = body.get("decision")
    if expected_decision is not None and actual_decision != expected_decision:
        errors.append(f"expected decision {expected_decision!r}, received {actual_decision!r}")

    if "review_queue" in expected and body.get("review_queue") != expected["review_queue"]:
        errors.append(
            f"expected review queue {expected['review_queue']!r}, "
            f"received {body.get('review_queue')!r}"
        )

    matched_rules = [rule.get("rule_id", "") for rule in body.get("matched_rules", [])]
    for rule_id in expected.get("matched_rules", []):
        if rule_id not in matched_rules:
            errors.append(f"expected matched rule {rule_id!r}")

    if expected.get("no_matched_rules") and matched_rules:
        errors.append(f"expected no matched rules, received {matched_rules}")

    missing_evidence = _flatten_missing_evidence(body)
    for evidence_type in expected.get("missing_evidence", []):
        if evidence_type not in missing_evidence:
            errors.append(f"expected missing evidence {evidence_type!r}")

    reasons = " ".join(str(item) for item in body.get("reasons", [])).lower()
    for fragment in expected.get("reason_contains", []):
        if fragment.lower() not in reasons:
            errors.append(f"expected reason containing {fragment!r}")

    assessments = body.get("evidence_assessments", [])
    accepted_count = sum(bool(item.get("accepted")) for item in assessments)
    if "min_accepted_evidence" in expected and accepted_count < expected["min_accepted_evidence"]:
        errors.append(
            f"expected at least {expected['min_accepted_evidence']} accepted evidence items, "
            f"received {accepted_count}"
        )
    if "max_accepted_evidence" in expected and accepted_count > expected["max_accepted_evidence"]:
        errors.append(
            f"expected at most {expected['max_accepted_evidence']} accepted evidence items, "
            f"received {accepted_count}"
        )

    scores = [float(item.get("score", 0.0)) for item in assessments]
    if "min_evidence_score" in expected and (
        not scores or max(scores) < float(expected["min_evidence_score"])
    ):
        errors.append(f"expected evidence score >= {expected['min_evidence_score']}")

    if expected.get("audit_signature") and not body.get("audit", {}).get("signature"):
        errors.append("expected a signed audit envelope")
    if expected.get("policy_set_hash") and not body.get("policy_set_hash"):
        errors.append("expected a policy-set hash")

    return errors, {
        "matched_rules": matched_rules,
        "evidence_scores": scores,
        "actual_decision": actual_decision,
        "review_queue": body.get("review_queue"),
    }


def run_correctness_scenario(
    base_url: str,
    scenario: dict[str, Any],
    timeout: float,
) -> ScenarioResult:
    result = request_json("POST", f"{base_url}/v1/evaluate", scenario["request"], timeout)
    errors, extracted = validate_response(scenario, result)
    return ScenarioResult(
        scenario_id=scenario["id"],
        name=scenario["name"],
        category=scenario["category"],
        description=scenario.get("description", ""),
        passed=not errors,
        expected_status=int(scenario["expect"].get("status", 200)),
        actual_status=result.status,
        expected_decision=scenario["expect"].get("decision"),
        actual_decision=extracted["actual_decision"],
        review_queue=extracted["review_queue"],
        matched_rules=extracted["matched_rules"],
        evidence_scores=extracted["evidence_scores"],
        latency_ms=result.latency_ms,
        errors=errors,
        request=scenario["request"],
        response=result.body,
    )


def run_performance_profile(
    base_url: str,
    scenarios: list[dict[str, Any]],
    iterations: int,
    concurrency: int,
    timeout: float,
) -> dict[str, Any]:
    benchmark_scenarios = [
        scenario
        for scenario in scenarios
        if scenario.get("benchmark", True) and int(scenario["expect"].get("status", 200)) == 200
    ]
    tasks = [scenario for scenario in benchmark_scenarios for _ in range(iterations)]
    scenario_latencies: dict[str, list[float]] = {
        scenario["id"]: [] for scenario in benchmark_scenarios
    }
    failures: list[str] = []
    decision_distribution: Counter[str] = Counter()
    started = time.perf_counter()

    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as executor:
        future_map = {
            executor.submit(
                request_json,
                "POST",
                f"{base_url}/v1/evaluate",
                scenario["request"],
                timeout,
            ): scenario
            for scenario in tasks
        }
        for future in as_completed(future_map):
            scenario = future_map[future]
            result = future.result()
            errors, extracted = validate_response(scenario, result)
            scenario_latencies[scenario["id"]].append(result.latency_ms)
            decision_distribution[str(extracted["actual_decision"] or "none")] += 1
            if errors:
                failures.append(f"{scenario['id']}: {'; '.join(errors)}")

    duration_seconds = max(time.perf_counter() - started, 0.000001)
    all_latencies = [value for values in scenario_latencies.values() for value in values]
    per_scenario = []
    for scenario in benchmark_scenarios:
        values = scenario_latencies[scenario["id"]]
        per_scenario.append(
            {
                "scenario_id": scenario["id"],
                "name": scenario["name"],
                "requests": len(values),
                "mean_ms": round(fmean(values), 3) if values else 0.0,
                "median_ms": round(median(values), 3) if values else 0.0,
                "p95_ms": round(percentile(values, 0.95), 3),
                "max_ms": round(max(values), 3) if values else 0.0,
            }
        )

    return {
        "requests": len(tasks),
        "concurrency": concurrency,
        "iterations_per_scenario": iterations,
        "duration_seconds": round(duration_seconds, 3),
        "requests_per_second": round(len(tasks) / duration_seconds, 3),
        "mean_ms": round(fmean(all_latencies), 3) if all_latencies else 0.0,
        "median_ms": round(median(all_latencies), 3) if all_latencies else 0.0,
        "p95_ms": round(percentile(all_latencies, 0.95), 3),
        "p99_ms": round(percentile(all_latencies, 0.99), 3),
        "max_ms": round(max(all_latencies), 3) if all_latencies else 0.0,
        "decision_distribution": dict(sorted(decision_distribution.items())),
        "failures": failures,
        "scenarios": per_scenario,
    }


def _format_json(value: Any) -> str:
    return html.escape(json.dumps(value, indent=2, sort_keys=True, default=str))


def render_html_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    performance = report["performance"]
    passed = summary["overall_passed"]
    status_class = "pass" if passed else "fail"
    status_label = "PASSED" if passed else "FAILED"

    scenario_rows = []
    scenario_details = []
    for scenario in report["scenarios"]:
        row_class = "pass" if scenario["passed"] else "fail"
        error_text = "<br>".join(html.escape(item) for item in scenario["errors"]) or "—"
        rules = ", ".join(scenario["matched_rules"]) or "—"
        scenario_rows.append(
            "<tr>"
            f"<td><span class='status {row_class}'>{'PASS' if scenario['passed'] else 'FAIL'}</span></td>"
            f"<td><strong>{html.escape(scenario['name'])}</strong><small>{html.escape(scenario['scenario_id'])}</small></td>"
            f"<td>{html.escape(scenario['category'])}</td>"
            f"<td>{html.escape(str(scenario['expected_decision'] or scenario['expected_status']))}</td>"
            f"<td>{html.escape(str(scenario['actual_decision'] or scenario['actual_status']))}</td>"
            f"<td>{html.escape(rules)}</td>"
            f"<td>{scenario['latency_ms']:.2f} ms</td>"
            f"<td>{error_text}</td>"
            "</tr>"
        )
        scenario_details.append(
            "<details>"
            f"<summary>{html.escape(scenario['name'])}</summary>"
            f"<p>{html.escape(scenario['description'])}</p>"
            "<div class='code-grid'>"
            f"<div><h4>Request</h4><pre>{_format_json(scenario['request'])}</pre></div>"
            f"<div><h4>Response</h4><pre>{_format_json(scenario['response'])}</pre></div>"
            "</div></details>"
        )

    performance_rows = "".join(
        "<tr>"
        f"<td>{html.escape(item['name'])}</td>"
        f"<td>{item['requests']}</td>"
        f"<td>{item['mean_ms']:.3f}</td>"
        f"<td>{item['median_ms']:.3f}</td>"
        f"<td>{item['p95_ms']:.3f}</td>"
        f"<td>{item['max_ms']:.3f}</td>"
        "</tr>"
        for item in performance["scenarios"]
    )

    decision_total = max(sum(performance["decision_distribution"].values()), 1)
    decision_bars = "".join(
        "<div class='bar-row'>"
        f"<span>{html.escape(decision)}</span>"
        f"<div class='bar'><i style='width:{count / decision_total * 100:.1f}%'></i></div>"
        f"<strong>{count}</strong>"
        "</div>"
        for decision, count in performance["decision_distribution"].items()
    )

    categories = "".join(
        f"<span class='chip'>{html.escape(category)}</span>"
        for category in summary["categories"]
    )
    audit = report["audit_integrity"]
    policy_hash = str(report.get("policies", {}).get("policy_set_hash", "unknown"))

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VeriWeave Govern Benchmark Report</title>
<style>
:root{{--bg:#07111f;--panel:#101c2d;--panel2:#0c1726;--line:#263750;--text:#eef6ff;--muted:#91a4bd;--green:#62e6b8;--red:#ff7d8d;--amber:#ffd166;--blue:#78a9ff}}
*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at 85% 0,#18375c 0,#07111f 42%);color:var(--text);font:15px/1.55 Inter,ui-sans-serif,system-ui,sans-serif}}
main{{width:min(1280px,94vw);margin:auto;padding:42px 0 64px}}header{{display:flex;justify-content:space-between;gap:24px;align-items:end;margin-bottom:26px}}h1{{font-size:clamp(2.3rem,6vw,5rem);letter-spacing:-.06em;line-height:.92;margin:0}}h1 span{{color:var(--green)}}p{{color:var(--muted)}}.hero-status{{padding:11px 18px;border-radius:999px;font-weight:900;border:1px solid var(--line)}}.hero-status.pass{{color:var(--green);background:#0d2b25}}.hero-status.fail{{color:var(--red);background:#351823}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:18px 0}}.card,.panel{{background:linear-gradient(180deg,#112039ee,#0c1728ee);border:1px solid var(--line);border-radius:18px;box-shadow:0 18px 55px #0005}}.card{{padding:18px}}.card small{{display:block;color:var(--muted);text-transform:uppercase;letter-spacing:.1em}}.card strong{{font-size:1.7rem;display:block;margin-top:4px}}.panel{{padding:22px;margin-top:18px;overflow:auto}}h2{{margin:0 0 14px;font-size:1.2rem}}h4{{margin:0 0 8px}}.chips{{display:flex;flex-wrap:wrap;gap:8px}}.chip{{border:1px solid var(--line);border-radius:999px;padding:5px 10px;color:#c9d8ea;background:#0a1524}}
table{{width:100%;border-collapse:collapse;min-width:900px}}th,td{{text-align:left;padding:12px;border-bottom:1px solid var(--line);vertical-align:top}}th{{color:var(--muted);font-size:.76rem;text-transform:uppercase;letter-spacing:.08em}}td small{{display:block;color:var(--muted)}}.status{{font-size:.72rem;font-weight:900;padding:4px 8px;border-radius:999px}}.status.pass{{color:#05251b;background:var(--green)}}.status.fail{{color:#2b0710;background:var(--red)}}
.split{{display:grid;grid-template-columns:1.2fr .8fr;gap:18px}}.bar-row{{display:grid;grid-template-columns:70px 1fr 42px;gap:10px;align-items:center;margin:11px 0}}.bar{{height:10px;background:#07101d;border-radius:999px;overflow:hidden}}.bar i{{display:block;height:100%;background:linear-gradient(90deg,var(--blue),var(--green));border-radius:inherit}}details{{border-top:1px solid var(--line);padding:13px 0}}summary{{cursor:pointer;font-weight:750}}.code-grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}pre{{background:#06101d;border:1px solid var(--line);border-radius:12px;padding:14px;overflow:auto;color:#c9d8ea;font-size:.78rem;max-height:430px}}code{{color:#bdd2ec;word-break:break-all}}.good{{color:var(--green)}}.bad{{color:var(--red)}}footer{{color:var(--muted);margin-top:22px;font-size:.82rem}}@media(max-width:900px){{header{{align-items:start;flex-direction:column}}.grid{{grid-template-columns:1fr 1fr}}.split,.code-grid{{grid-template-columns:1fr}}}}@media(max-width:540px){{.grid{{grid-template-columns:1fr}}}}
</style>
</head>
<body><main>
<header><div><h1>VeriWeave <span>Govern</span></h1><p>End-to-end governance correctness, evidence, audit-integrity, and performance benchmark.</p></div><div class="hero-status {status_class}">{status_label}</div></header>
<div class="chips">{categories}</div>
<section class="grid">
<div class="card"><small>Scenario accuracy</small><strong>{summary['passed_scenarios']}/{summary['scenario_count']}</strong></div>
<div class="card"><small>Benchmark requests</small><strong>{performance['requests']}</strong></div>
<div class="card"><small>P95 latency</small><strong>{performance['p95_ms']:.2f} ms</strong></div>
<div class="card"><small>Throughput</small><strong>{performance['requests_per_second']:.1f} req/s</strong></div>
</section>
<section class="split">
<div class="panel"><h2>Run configuration</h2><p>Generated <strong>{html.escape(report['generated_at'])}</strong></p><p>Target <code>{html.escape(report['base_url'])}</code></p><p>Policy set <code>{html.escape(policy_hash)}</code></p><p>Iterations per scenario: <strong>{performance['iterations_per_scenario']}</strong> · concurrency: <strong>{performance['concurrency']}</strong></p></div>
<div class="panel"><h2>Decision distribution</h2>{decision_bars or '<p>No performance requests.</p>'}</div>
</section>
<section class="panel"><h2>Correctness scenarios</h2><table><thead><tr><th>Status</th><th>Scenario</th><th>Category</th><th>Expected</th><th>Actual</th><th>Matched rules</th><th>Latency</th><th>Errors</th></tr></thead><tbody>{''.join(scenario_rows)}</tbody></table></section>
<section class="panel"><h2>Performance by scenario</h2><table><thead><tr><th>Scenario</th><th>Requests</th><th>Mean ms</th><th>Median ms</th><th>P95 ms</th><th>Max ms</th></tr></thead><tbody>{performance_rows}</tbody></table></section>
<section class="panel"><h2>Audit integrity</h2><p class="{'good' if audit.get('valid') else 'bad'}"><strong>{'Valid' if audit.get('valid') else 'Invalid'}</strong> · records: {audit.get('records', 0)} · head hash: <code>{html.escape(str(audit.get('head_hash', 'n/a')))}</code></p></section>
<section class="panel"><h2>Scenario evidence</h2>{''.join(scenario_details)}</section>
<footer>Generated by <code>python -m benchmark.runner</code>. Machine-readable results are available beside this report in <code>benchmark-results.json</code>.</footer>
</main></body></html>"""


def build_report(
    base_url: str,
    health: dict[str, Any],
    policies: dict[str, Any],
    scenarios: list[ScenarioResult],
    performance: dict[str, Any],
    audit_integrity: dict[str, Any],
) -> dict[str, Any]:
    passed_scenarios = sum(item.passed for item in scenarios)
    categories = sorted({item.category for item in scenarios})
    overall_passed = (
        passed_scenarios == len(scenarios)
        and not performance["failures"]
        and bool(audit_integrity.get("valid"))
    )
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "base_url": base_url,
        "health": health,
        "policies": policies,
        "summary": {
            "overall_passed": overall_passed,
            "scenario_count": len(scenarios),
            "passed_scenarios": passed_scenarios,
            "failed_scenarios": len(scenarios) - passed_scenarios,
            "categories": categories,
        },
        "scenarios": [asdict(item) for item in scenarios],
        "performance": performance,
        "audit_integrity": audit_integrity,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark a running VeriWeave Govern service")
    parser.add_argument(
        "--base-url",
        default=os.getenv("BENCHMARK_BASE_URL", "http://localhost:8080"),
    )
    parser.add_argument(
        "--scenarios",
        type=Path,
        default=Path(os.getenv("BENCHMARK_SCENARIOS", "benchmark/scenarios.json")),
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path(os.getenv("BENCHMARK_RESULTS_DIR", "results")),
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=int(os.getenv("BENCHMARK_ITERATIONS", "10")),
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=int(os.getenv("BENCHMARK_CONCURRENCY", "4")),
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.getenv("BENCHMARK_REQUEST_TIMEOUT", "10")),
    )
    parser.add_argument(
        "--startup-timeout",
        type=float,
        default=float(os.getenv("BENCHMARK_STARTUP_TIMEOUT", "60")),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.results_dir.mkdir(parents=True, exist_ok=True)
    scenarios = json.loads(args.scenarios.read_text(encoding="utf-8"))["scenarios"]

    print(f"Waiting for VeriWeave Govern at {args.base_url} ...", flush=True)
    try:
        health = wait_for_service(args.base_url, args.startup_timeout)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    policies_result = request_json("GET", f"{args.base_url}/v1/policies", timeout=args.timeout)
    policies = policies_result.body if isinstance(policies_result.body, dict) else {}

    print(f"Running {len(scenarios)} correctness scenarios ...", flush=True)
    correctness = [
        run_correctness_scenario(args.base_url, scenario, args.timeout) for scenario in scenarios
    ]
    for result in correctness:
        marker = "PASS" if result.passed else "FAIL"
        print(
            f"[{marker}] {result.scenario_id}: expected={result.expected_decision or result.expected_status} "
            f"actual={result.actual_decision or result.actual_status} ({result.latency_ms:.2f} ms)",
            flush=True,
        )
        for error in result.errors:
            print(f"       - {error}", flush=True)

    print(
        f"Running performance profile: {args.iterations} iterations/scenario, "
        f"concurrency={args.concurrency} ...",
        flush=True,
    )
    performance = run_performance_profile(
        args.base_url,
        scenarios,
        max(1, args.iterations),
        max(1, args.concurrency),
        args.timeout,
    )
    audit_result = request_json("GET", f"{args.base_url}/v1/audit/verify", timeout=args.timeout)
    audit_integrity = audit_result.body if isinstance(audit_result.body, dict) else {"valid": False}

    report = build_report(
        args.base_url,
        health,
        policies,
        correctness,
        performance,
        audit_integrity,
    )
    json_path = args.results_dir / "benchmark-results.json"
    html_path = args.results_dir / "benchmark-report.html"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    html_path.write_text(render_html_report(report), encoding="utf-8")

    summary = report["summary"]
    print("", flush=True)
    print("VeriWeave Govern benchmark complete", flush=True)
    print(
        f"Scenarios: {summary['passed_scenarios']}/{summary['scenario_count']} passed | "
        f"P95: {performance['p95_ms']:.2f} ms | "
        f"Throughput: {performance['requests_per_second']:.2f} req/s | "
        f"Audit: {'valid' if audit_integrity.get('valid') else 'invalid'}",
        flush=True,
    )
    print(f"HTML report: {html_path}", flush=True)
    print(f"JSON report: {json_path}", flush=True)
    return 0 if summary["overall_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
