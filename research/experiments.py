from __future__ import annotations

import argparse
import csv
import html
import json
import os
import time
from pathlib import Path
from statistics import fmean

from research.baselines import abac, llm_proxy, rbac, veriweave
from research.calibration import evidence_rows, train_calibrator
from research.dataset import generate_governbench, write_jsonl
from research.governor import decide, governance_certificate
from research.metrics import (
    attack_success_rate,
    brier_score,
    classification_metrics,
    expected_calibration_error,
    pr_auc,
    roc_auc,
    summarize_runs,
)

BASELINES = ("rbac", "abac", "llm-proxy", "veriweave")
ABLATIONS = (
    "evidence-gate",
    "contradiction-check",
    "human-review",
    "fail-safe-ood",
    "deny-precedence",
    "temporal-replay",
)
METRICS = (
    "accuracy",
    "macro_f1",
    "false_allow_rate",
    "false_deny_rate",
    "false_review_rate",
    "gasr",
)


def split_cases(cases):
    train = [case for index, case in enumerate(cases) if index % 5 not in {0, 1}]
    test = [case for index, case in enumerate(cases) if index % 5 in {0, 1}]
    return train, test


def evaluate_seed(seed: int, case_count: int) -> dict[str, object]:
    cases = generate_governbench(seed, case_count)
    train, test = split_cases(cases)
    model = train_calibrator(train)
    truth = [case.ground_truth for case in test]
    attacks = [bool(case.attack_type) for case in test]
    predictions = {
        "rbac": [rbac(case) for case in test],
        "abac": [abac(case) for case in test],
        "llm-proxy": [llm_proxy(case) for case in test],
        "veriweave": [veriweave(case, model) for case in test],
    }
    baseline_metrics = {}
    for name, predicted in predictions.items():
        values = classification_metrics(truth, predicted)
        values["gasr"] = attack_success_rate(truth, predicted, attacks)
        baseline_metrics[name] = values

    ablations = {}
    for name in ABLATIONS:
        predicted = [
            decide(case, model, ablations=frozenset({name})).decision for case in test
        ]
        values = classification_metrics(truth, predicted)
        values["gasr"] = attack_success_rate(truth, predicted, attacks)
        ablations[name] = values

    rows = evidence_rows(test)
    labels = [int(evidence.label_valid) for evidence in rows]
    probabilities = [model.predict_proba(evidence) for evidence in rows]
    calibration = {
        "brier": brier_score(labels, probabilities),
        "ece": expected_calibration_error(labels, probabilities),
        "auroc": roc_auc(labels, probabilities),
        "auprc": pr_auc(labels, probabilities),
        "threshold": model.threshold,
    }
    temporal = [case for case in test if case.category == "temporal"]
    return {
        "seed": seed,
        "baselines": baseline_metrics,
        "ablations": ablations,
        "calibration": calibration,
        "temporal_accuracy": sum(
            decide(case, model).decision == case.ground_truth for case in temporal
        )
        / max(len(temporal), 1),
        "calibration_model": model.to_dict(),
        "certificate_example": governance_certificate(test[0], model),
    }


def aggregate(runs: list[dict[str, object]]) -> dict[str, object]:
    return {
        "baselines": {
            name: summarize_runs([run["baselines"][name] for run in runs], METRICS)
            for name in BASELINES
        },
        "ablations": {
            name: summarize_runs([run["ablations"][name] for run in runs], METRICS)
            for name in ABLATIONS
        },
        "calibration": {
            metric: summarize_runs(
                [{metric: float(run["calibration"][metric])} for run in runs],
                (metric,),
            )[metric]
            for metric in ("brier", "ece", "auroc", "auprc", "threshold")
        },
        "temporal_accuracy": summarize_runs(
            [{"accuracy": float(run["temporal_accuracy"])} for run in runs],
            ("accuracy",),
        )["accuracy"],
    }


def latency_profile(seed: int = 997) -> dict[str, object]:
    train, test = split_cases(generate_governbench(seed, 400))
    model = train_calibrator(train, epochs=80)
    rows = []
    for multiplier in (1, 5, 20):
        expanded = [
            type(case)(**{**case.__dict__, "evidence": case.evidence * multiplier})
            for case in test[:100]
        ]
        timings = []
        started = time.perf_counter()
        for _ in range(5):
            for case in expanded:
                one = time.perf_counter()
                decide(case, model)
                timings.append((time.perf_counter() - one) * 1000)
        elapsed = max(time.perf_counter() - started, 1e-9)
        timings.sort()
        rows.append(
            {
                "evidence_multiplier": multiplier,
                "requests": len(timings),
                "mean_ms": fmean(timings),
                "p95_ms": timings[int(0.95 * (len(timings) - 1))],
                "throughput_rps": len(timings) / elapsed,
            }
        )
    return {
        "note": "In-process synthetic profile; use Docker benchmark for service latency.",
        "rows": rows,
    }


def render_html(report: dict[str, object]) -> str:
    rows = []
    for name, values in report["aggregate"]["baselines"].items():
        acc, f1, far, gasr = (
            values[key] for key in ("accuracy", "macro_f1", "false_allow_rate", "gasr")
        )
        rows.append(
            "<tr>"
            f"<td><b>{html.escape(name)}</b></td>"
            f"<td>{acc['mean']:.4f} [{acc['ci95_low']:.4f}, {acc['ci95_high']:.4f}]</td>"
            f"<td>{f1['mean']:.4f}</td>"
            f"<td>{far['mean']:.4f}</td>"
            f"<td>{gasr['mean']:.4f}</td>"
            "</tr>"
        )
    return (
        "<!doctype html><meta charset='utf-8'><title>GovernBench</title>"
        "<style>body{font:15px system-ui;max-width:1100px;margin:40px auto;padding:0 20px}"
        "table{width:100%;border-collapse:collapse}td,th{padding:10px;border-bottom:1px solid #ddd}"
        ".note{padding:14px;background:#fff8e1}</style>"
        "<h1>GovernBench Scientific Report</h1>"
        "<p class='note'><b>Scientific boundary:</b> synthetic, oracle-labelled reference "
        "benchmark; not human-validated real-world effectiveness or legal certification.</p>"
        "<table><tr><th>Method</th><th>Accuracy mean [95% CI]</th><th>Macro F1</th>"
        "<th>False-Allow</th><th>GASR</th></tr>"
        + "".join(rows)
        + "</table><p>Reproduce: <code>python -m research.experiments --seeds 30 "
        "--cases 2000 --output results/research-v1</code></p>"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run GovernBench scientific evaluation")
    parser.add_argument(
        "--seeds", type=int, default=int(os.getenv("GOVERNBENCH_SEEDS", "30"))
    )
    parser.add_argument(
        "--cases", type=int, default=int(os.getenv("GOVERNBENCH_CASES", "2000"))
    )
    parser.add_argument("--output", type=Path, default=Path("results/research-v1"))
    parser.add_argument("--write-dataset", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    runs = [evaluate_seed(seed, args.cases) for seed in range(args.seeds)]
    report = {
        "schema": "governbench-report/v1",
        "configuration": {
            "seeds": args.seeds,
            "cases_per_seed": args.cases,
            "synthetic": True,
        },
        "aggregate": aggregate(runs),
        "scalability": latency_profile(),
        "runs": runs,
    }
    (args.output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    (args.output / "report.html").write_text(render_html(report), encoding="utf-8")
    with (args.output / "baseline-runs.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=("seed", "baseline", *METRICS))
        writer.writeheader()
        for run in runs:
            for name, values in run["baselines"].items():
                writer.writerow({"seed": run["seed"], "baseline": name, **values})

    (args.output / "calibration-model.json").write_text(
        json.dumps(runs[0]["calibration_model"], indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (args.output / "certificate-example.json").write_text(
        json.dumps(runs[0]["certificate_example"], indent=2, sort_keys=True),
        encoding="utf-8",
    )
    if args.write_dataset:
        write_jsonl(
            args.output / "governbench-seed0.jsonl",
            generate_governbench(0, args.cases),
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
