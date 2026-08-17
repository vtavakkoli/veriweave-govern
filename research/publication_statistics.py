from __future__ import annotations

import argparse
import csv
import html
import json
import math
import random
from pathlib import Path
from statistics import fmean

from research.metrics import classification_metrics

DECISIONS = {"allow", "review", "deny"}
METADATA_FIELDS = {
    "case_id",
    "domain",
    "family",
    "provisional_label",
    "annotator_a",
    "annotator_b",
    "adjudicated_label",
}
CI_METRICS = ("accuracy", "macro_f1", "false_allow_rate")


def load_predictions(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    methods = [field for field in fields if field not in METADATA_FIELDS]
    if not rows:
        raise ValueError("predictions.csv is empty")
    if not methods:
        raise ValueError("predictions.csv contains no method columns")
    return rows, methods


def _truth(rows: list[dict[str, str]]) -> tuple[list[str], str]:
    adjudicated = [row.get("adjudicated_label", "").strip().lower() for row in rows]
    if adjudicated and all(label in DECISIONS for label in adjudicated):
        return adjudicated, "human-adjudicated"
    provisional = [row.get("provisional_label", "").strip().lower() for row in rows]
    if not all(label in DECISIONS for label in provisional):
        raise ValueError("neither complete adjudicated nor valid provisional labels are available")
    return provisional, "provisional-regulation-grounded"


def _method_predictions(rows: list[dict[str, str]], method: str) -> list[str]:
    values = [row.get(method, "").strip().lower() for row in rows]
    invalid = [index for index, value in enumerate(values) if value not in DECISIONS]
    if invalid:
        raise ValueError(f"{method}: invalid/missing decision at rows {invalid[:5]}")
    return values


def _percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _bootstrap_metrics(
    truth: list[str],
    predicted: list[str],
    *,
    samples: int,
    seed: int,
) -> dict[str, dict[str, float]]:
    rng = random.Random(seed)
    n = len(truth)
    distributions = {name: [] for name in CI_METRICS}
    for _ in range(samples):
        idx = [rng.randrange(n) for _ in range(n)]
        metrics = classification_metrics(
            [truth[i] for i in idx],
            [predicted[i] for i in idx],
        )
        for name in CI_METRICS:
            distributions[name].append(float(metrics[name]))
    point = classification_metrics(truth, predicted)
    return {
        name: {
            "estimate": float(point[name]),
            "ci95_low": _percentile(distributions[name], 0.025),
            "ci95_high": _percentile(distributions[name], 0.975),
        }
        for name in CI_METRICS
    }


def _paired_accuracy_difference(
    truth: list[str],
    reference: list[str],
    baseline: list[str],
    *,
    samples: int,
    seed: int,
) -> dict[str, float]:
    rng = random.Random(seed)
    n = len(truth)
    diffs: list[float] = []
    for _ in range(samples):
        idx = [rng.randrange(n) for _ in range(n)]
        ref = fmean(reference[i] == truth[i] for i in idx)
        base = fmean(baseline[i] == truth[i] for i in idx)
        diffs.append(ref - base)
    point = fmean(reference[i] == truth[i] for i in range(n)) - fmean(
        baseline[i] == truth[i] for i in range(n)
    )
    return {
        "estimate": point,
        "ci95_low": _percentile(diffs, 0.025),
        "ci95_high": _percentile(diffs, 0.975),
    }


def _mcnemar_exact(
    truth: list[str],
    reference: list[str],
    baseline: list[str],
) -> dict[str, float | int]:
    ref_only = sum(
        reference[i] == truth[i] and baseline[i] != truth[i]
        for i in range(len(truth))
    )
    base_only = sum(
        reference[i] != truth[i] and baseline[i] == truth[i]
        for i in range(len(truth))
    )
    discordant = ref_only + base_only
    if discordant == 0:
        p_value = 1.0
    else:
        k = min(ref_only, base_only)
        tail = sum(math.comb(discordant, i) for i in range(k + 1)) / (2**discordant)
        p_value = min(1.0, 2.0 * tail)
    return {
        "reference_correct_baseline_wrong": ref_only,
        "reference_wrong_baseline_correct": base_only,
        "discordant": discordant,
        "p_value_two_sided": p_value,
    }


def _holm_bonferroni(raw: dict[str, float]) -> dict[str, float]:
    ordered = sorted(raw.items(), key=lambda item: item[1])
    adjusted: dict[str, float] = {}
    running = 0.0
    m = len(ordered)
    for rank, (name, p_value) in enumerate(ordered):
        candidate = min(1.0, (m - rank) * p_value)
        running = max(running, candidate)
        adjusted[name] = min(1.0, running)
    return adjusted


def build_report(
    rows: list[dict[str, str]],
    methods: list[str],
    *,
    samples: int,
    seed: int,
) -> dict[str, object]:
    truth, label_status = _truth(rows)
    predictions = {method: _method_predictions(rows, method) for method in methods}
    metrics = {
        method: _bootstrap_metrics(
            truth,
            predicted,
            samples=samples,
            seed=seed + index * 1009,
        )
        for index, (method, predicted) in enumerate(predictions.items())
    }

    reference_name = "veriweave" if "veriweave" in predictions else methods[0]
    reference = predictions[reference_name]
    comparisons: dict[str, dict[str, object]] = {}
    raw_p: dict[str, float] = {}
    for index, (method, predicted) in enumerate(predictions.items()):
        if method == reference_name:
            continue
        mcnemar = _mcnemar_exact(truth, reference, predicted)
        raw_p[method] = float(mcnemar["p_value_two_sided"])
        comparisons[method] = {
            "accuracy_difference_reference_minus_baseline": _paired_accuracy_difference(
                truth,
                reference,
                predicted,
                samples=samples,
                seed=seed + 50000 + index * 1009,
            ),
            "mcnemar_exact": mcnemar,
        }
    adjusted = _holm_bonferroni(raw_p)
    for method, p_value in adjusted.items():
        comparisons[method]["mcnemar_holm_adjusted_p"] = p_value

    per_domain: dict[str, object] = {}
    for domain in sorted({row["domain"] for row in rows}):
        idx = [i for i, row in enumerate(rows) if row["domain"] == domain]
        per_domain[domain] = {
            method: classification_metrics(
                [truth[i] for i in idx],
                [predicted[i] for i in idx],
            )
            for method, predicted in predictions.items()
        }

    return {
        "schema": "veriweave-publication-statistics/v1",
        "label_status": label_status,
        "configuration": {
            "cases": len(rows),
            "bootstrap_samples": samples,
            "bootstrap_seed": seed,
            "confidence_level": 0.95,
            "reference_method": reference_name,
            "multiple_testing": "Holm-Bonferroni over exact two-sided McNemar comparisons",
        },
        "metrics": metrics,
        "paired_comparisons": comparisons,
        "per_domain": per_domain,
        "scientific_boundary": (
            "Confidence intervals and significance tests are final-paper statistics only "
            "when label_status is human-adjudicated. With provisional labels they are "
            "development diagnostics and must not be presented as human-validated evidence."
        ),
    }


def render_html(report: dict[str, object]) -> str:
    rows = []
    for method, metrics in report["metrics"].items():
        accuracy = metrics["accuracy"]
        macro_f1 = metrics["macro_f1"]
        false_allow = metrics["false_allow_rate"]
        rows.append(
            "<tr>"
            f"<td><b>{html.escape(method)}</b></td>"
            f"<td>{accuracy['estimate']:.4f} [{accuracy['ci95_low']:.4f}, {accuracy['ci95_high']:.4f}]</td>"
            f"<td>{macro_f1['estimate']:.4f} [{macro_f1['ci95_low']:.4f}, {macro_f1['ci95_high']:.4f}]</td>"
            f"<td>{false_allow['estimate']:.4f} [{false_allow['ci95_low']:.4f}, {false_allow['ci95_high']:.4f}]</td>"
            "</tr>"
        )
    comparison_rows = []
    for method, values in report["paired_comparisons"].items():
        diff = values["accuracy_difference_reference_minus_baseline"]
        mcnemar = values["mcnemar_exact"]
        comparison_rows.append(
            "<tr>"
            f"<td>{html.escape(method)}</td>"
            f"<td>{diff['estimate']:+.4f} [{diff['ci95_low']:+.4f}, {diff['ci95_high']:+.4f}]</td>"
            f"<td>{mcnemar['reference_correct_baseline_wrong']}</td>"
            f"<td>{mcnemar['reference_wrong_baseline_correct']}</td>"
            f"<td>{mcnemar['p_value_two_sided']:.6g}</td>"
            f"<td>{values['mcnemar_holm_adjusted_p']:.6g}</td>"
            "</tr>"
        )
    status = html.escape(str(report["label_status"]))
    boundary = html.escape(str(report["scientific_boundary"]))
    reference = html.escape(str(report["configuration"]["reference_method"]))
    return f"""<!doctype html><meta charset="utf-8">
<title>VeriWeave publication statistics</title>
<style>
body{{font:15px system-ui;max-width:1200px;margin:40px auto;padding:0 20px;color:#172033}}
table{{width:100%;border-collapse:collapse;margin:16px 0 28px}}td,th{{padding:10px;border-bottom:1px solid #ddd;text-align:left}}
.note{{padding:14px;background:#fff8e1;border-left:5px solid #d29b00}}code{{background:#f3f4f6;padding:2px 5px;border-radius:4px}}
</style>
<h1>VeriWeave publication statistics</h1>
<p><b>Label status:</b> <code>{status}</code></p>
<p class="note">{boundary}</p>
<h2>Bootstrap 95% confidence intervals</h2>
<table><tr><th>Method</th><th>Accuracy</th><th>Macro-F1</th><th>False-Allow</th></tr>{''.join(rows)}</table>
<h2>Paired comparisons against {reference}</h2>
<table><tr><th>Baseline</th><th>Accuracy difference [95% CI]</th><th>{reference} only correct</th><th>Baseline only correct</th><th>McNemar p</th><th>Holm-adjusted p</th></tr>{''.join(comparison_rows)}</table>
<p>Bootstrap samples: <b>{report['configuration']['bootstrap_samples']}</b> · seed: <b>{report['configuration']['bootstrap_seed']}</b></p>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute publication statistics")
    parser.add_argument(
        "--predictions",
        type=Path,
        default=Path("results/publication/predictions.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/publication/statistics.json"),
    )
    parser.add_argument("--samples", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20260817)
    args = parser.parse_args()
    if args.samples < 1000:
        raise ValueError("use at least 1000 bootstrap samples for publication statistics")
    rows, methods = load_predictions(args.predictions)
    report = build_report(rows, methods, samples=args.samples, seed=args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    html_path = args.output.with_suffix(".html")
    html_path.write_text(render_html(report), encoding="utf-8")
    print(
        f"Publication statistics written for {report['configuration']['cases']} cases "
        f"using {report['label_status']} labels"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
