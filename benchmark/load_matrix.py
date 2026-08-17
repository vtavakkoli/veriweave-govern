from __future__ import annotations

import argparse
import html
import json
import math
import os
from pathlib import Path

from benchmark.runner import run_performance_profile, wait_for_service


def _concurrencies(raw: str) -> list[int]:
    values = [int(item.strip()) for item in raw.split(",") if item.strip()]
    if not values or any(value < 1 for value in values):
        raise ValueError("concurrency levels must be positive integers")
    return values


def _render_html(report: dict[str, object]) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{row['concurrency']}</td>"
        f"<td>{row['requests']}</td>"
        f"<td>{row['requests_per_second']:.2f}</td>"
        f"<td>{row['mean_ms']:.2f}</td>"
        f"<td>{row['p95_ms']:.2f}</td>"
        f"<td>{row['p99_ms']:.2f}</td>"
        f"<td>{row['max_ms']:.2f}</td>"
        f"<td>{len(row['failures'])}</td>"
        "</tr>"
        for row in report["rows"]
    )
    base_url = html.escape(str(report["base_url"]))
    return f"""<!doctype html><meta charset="utf-8">
<title>VeriWeave Load Matrix</title>
<style>
body{{font:15px system-ui;max-width:1100px;margin:40px auto;padding:0 20px;color:#172033}}
table{{width:100%;border-collapse:collapse}}td,th{{padding:10px;border-bottom:1px solid #ddd}}
.note{{padding:14px;background:#eef5ff;border-left:5px solid #3267d6}}
</style><h1>VeriWeave service load matrix</h1>
<p class="note">Service-level Docker benchmark against <code>{base_url}</code>. This is
separate from the in-process GovernBench scalability profile.</p>
<table><tr><th>Concurrency</th><th>Requests</th><th>Req/s</th><th>Mean ms</th>
<th>P95 ms</th><th>P99 ms</th><th>Max ms</th><th>Failures</th></tr>{rows}</table>
<p>Total requests: <b>{report['total_requests']}</b></p>"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a multi-concurrency service load matrix")
    parser.add_argument(
        "--base-url",
        default=os.getenv("BENCHMARK_BASE_URL", "http://govern:8080"),
    )
    parser.add_argument(
        "--scenarios",
        type=Path,
        default=Path(os.getenv("BENCHMARK_SCENARIOS", "/workspace/benchmark/scenarios.json")),
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path(os.getenv("BENCHMARK_RESULTS_DIR", "/results")),
    )
    parser.add_argument(
        "--requests-per-level",
        type=int,
        default=int(os.getenv("LOAD_MATRIX_REQUESTS_PER_LEVEL", "10000")),
    )
    parser.add_argument(
        "--concurrencies",
        default=os.getenv("LOAD_MATRIX_CONCURRENCIES", "1,4,16,32"),
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
    args = parser.parse_args()

    if args.requests_per_level < 1:
        raise SystemExit("requests-per-level must be positive")
    concurrencies = _concurrencies(args.concurrencies)
    scenarios = json.loads(args.scenarios.read_text(encoding="utf-8"))["scenarios"]
    benchmark_scenarios = [
        scenario
        for scenario in scenarios
        if scenario.get("benchmark", True)
        and int(scenario["expect"].get("status", 200)) == 200
    ]
    if not benchmark_scenarios:
        raise SystemExit("no benchmark scenarios available")

    wait_for_service(args.base_url, args.startup_timeout)
    iterations = max(1, math.ceil(args.requests_per_level / len(benchmark_scenarios)))
    rows = []
    for concurrency in concurrencies:
        print(
            f"Load level concurrency={concurrency}, "
            f"target_requests>={args.requests_per_level}",
            flush=True,
        )
        profile = run_performance_profile(
            args.base_url,
            scenarios,
            iterations,
            concurrency,
            args.timeout,
        )
        rows.append(profile)

    report = {
        "schema": "veriweave-load-matrix/v1",
        "base_url": args.base_url,
        "requested_per_level": args.requests_per_level,
        "concurrencies": concurrencies,
        "scenario_count": len(benchmark_scenarios),
        "iterations_per_scenario": iterations,
        "total_requests": sum(int(row["requests"]) for row in rows),
        "rows": rows,
    }
    args.results_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.results_dir / "load-matrix.json"
    html_path = args.results_dir / "load-matrix.html"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    html_path.write_text(_render_html(report), encoding="utf-8")

    failures = sum(len(row["failures"]) for row in rows)
    print(f"Load matrix complete: {report['total_requests']} requests, failures={failures}")
    print(f"HTML report: {html_path}")
    print(f"JSON report: {json_path}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
