from __future__ import annotations

import argparse
import csv
import html
import json
from collections import Counter
from pathlib import Path
from statistics import fmean

from research.baselines import abac, rbac
from research.calibration import evidence_rows, train_calibrator
from research.dataset import generate_governbench
from research.external_baselines import cedar_decision, ollama_decision, opa_decision
from research.governor import decide
from research.human_eval import cohen_kappa
from research.metrics import (
    brier_score,
    calibration_curve,
    classification_metrics,
    expected_calibration_error,
    pr_auc,
    roc_auc,
)
from research.model import Evidence, GovernCase

DECISIONS = ("allow", "review", "deny")
DOMAINS = ("public-administration", "enterprise-it-devops", "data-ai-governance")


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_validation_rows(path: Path) -> list[dict[str, str]]:
    if path.is_file():
        return load_rows(path)
    rows: list[dict[str, str]] = []
    for name in (
        "public-administration-1.csv",
        "public-administration-2.csv",
        "enterprise-it-devops-1.csv",
        "enterprise-it-devops-2.csv",
        "data-ai-governance-1.csv",
        "data-ai-governance-2.csv",
    ):
        rows.extend(load_rows(path / name))
    return rows


def load_source_registry(path: Path) -> dict[str, dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {item["id"]: item for item in payload["sources"]}


def validate_dataset(
    rows: list[dict[str, str]],
    sources: dict[str, dict[str, object]],
) -> list[str]:
    errors: list[str] = []
    if len(rows) != 150:
        errors.append(f"expected 150 cases, received {len(rows)}")
    counts = Counter(row["domain"] for row in rows)
    if any(counts[domain] != 50 for domain in DOMAINS):
        errors.append(f"expected 50 cases/domain, received {dict(counts)}")
    labels = Counter(row["provisional_label"] for row in rows)
    if labels != Counter({"allow": 50, "review": 50, "deny": 50}):
        errors.append(f"expected balanced labels, received {dict(labels)}")
    ids = [row["case_id"] for row in rows]
    if len(ids) != len(set(ids)):
        errors.append("case ids are not unique")
    for row in rows:
        if row["provisional_label"] not in DECISIONS:
            errors.append(f"{row['case_id']}: invalid provisional label")
        if row["provisional_label"] == "deny" and not row["prohibition_reason"]:
            errors.append(f"{row['case_id']}: deny case lacks prohibition_reason")
        for source_id in filter(None, row["source_ids"].split("|")):
            if source_id not in sources:
                errors.append(f"{row['case_id']}: unknown source {source_id}")
    return errors


def _write_annotation_sheet(
    path: Path,
    rows: list[dict[str, str]],
    sources: dict[str, dict[str, object]],
) -> None:
    if path.exists():
        return
    fields = [
        "case_id",
        "domain",
        "scenario",
        "action",
        "resource",
        "purpose",
        "impact",
        "environment",
        "data_classification",
        "external",
        "required_evidence",
        "evidence_state",
        "source_ids",
        "source_summaries",
        "source_urls",
        "evaluation_date",
        "legal_status",
        "decision",
        "confidence_1_to_5",
        "notes",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            source_ids = list(filter(None, row["source_ids"].split("|")))
            payload = {field: row.get(field, "") for field in fields}
            payload["source_summaries"] = " || ".join(
                f"{sid}: {sources[sid]['benchmark_summary']}" for sid in source_ids
            )
            payload["source_urls"] = " | ".join(
                str(sources[sid]["url"]) for sid in source_ids
            )
            payload["decision"] = ""
            payload["confidence_1_to_5"] = ""
            payload["notes"] = ""
            writer.writerow(payload)


def _write_adjudication(path: Path, rows: list[dict[str, str]]) -> None:
    if path.exists():
        return
    fields = [
        "case_id",
        "adjudicated_label",
        "adjudication_rationale",
        "adjudicator_id",
        "adjudicated_at",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({"case_id": row["case_id"]})


def prepare_annotation_files(
    rows: list[dict[str, str]],
    sources: dict[str, dict[str, object]],
    annotator_a: Path,
    annotator_b: Path,
    adjudication: Path,
) -> None:
    _write_annotation_sheet(annotator_a, rows, sources)
    _write_annotation_sheet(annotator_b, rows, sources)
    _write_adjudication(adjudication, rows)


def validate_blind_annotation_sheet(
    rows: list[dict[str, str]],
    expected_ids: set[str],
) -> list[str]:
    errors: list[str] = []
    ids = [row["case_id"] for row in rows]
    if len(ids) != len(expected_ids) or set(ids) != expected_ids:
        errors.append("annotation sheet does not exactly cover the benchmark")
    forbidden = {"provisional_label", "provisional_rationale", "prohibition_reason"}
    if rows and forbidden & set(rows[0]):
        errors.append("annotation sheet leaks provisional fields")
    for row in rows:
        decision = row.get("decision", "").strip().lower()
        if decision and decision not in DECISIONS:
            errors.append(f"{row['case_id']}: invalid annotation")
    return errors


def _decisions(path: Path, field: str) -> dict[str, str]:
    return {
        row["case_id"]: row.get(field, "").strip().lower()
        for row in load_rows(path)
    }


def _evidence(row: dict[str, str]) -> tuple[Evidence, ...]:
    if row["evidence_state"] == "missing":
        return ()
    required = tuple(filter(None, row["required_evidence"].split("|")))
    return tuple(
        Evidence(
            evidence_id=f"{row['case_id']}-ev-{index}",
            evidence_type=evidence_type,
            source_id="regulatory-validation-review-pack",
            authority=95,
            current=True,
            signed=True,
            content=(
                "Controlled review-pack evidence documents the required control, "
                "accountable owner and verification status."
            ),
            label_valid=True,
            metadata={"validation_case": row["case_id"]},
        )
        for index, evidence_type in enumerate(required)
    )


def row_to_case(row: dict[str, str]) -> GovernCase:
    return GovernCase(
        case_id=row["case_id"],
        seed=-1,
        domain=row["domain"],
        category=row["family"],
        action=row["action"],
        resource=row["resource"],
        purpose=row["purpose"],
        impact=row["impact"],
        environment=row["environment"],
        data_classification=row["data_classification"],
        external=row["external"].lower() == "true",
        required_evidence=tuple(filter(None, row["required_evidence"].split("|"))),
        evidence=_evidence(row),
        ground_truth=row["provisional_label"],
        notes=row["scenario"],
        prohibition_reason=row["prohibition_reason"] or None,
        legal_basis=tuple(filter(None, row["source_ids"].split("|"))),
        evaluation_date=row["evaluation_date"] or None,
    )


def _agreement(
    rows: list[dict[str, str]],
    a: dict[str, str],
    b: dict[str, str],
    adjudicated: dict[str, str],
) -> dict[str, object]:
    paired = [
        row["case_id"]
        for row in rows
        if a.get(row["case_id"]) in DECISIONS and b.get(row["case_id"]) in DECISIONS
    ]
    return {
        "status": "complete" if len(paired) == len(rows) else "pending",
        "paired_cases": len(paired),
        "required_cases": len(rows),
        "cohen_kappa": (
            cohen_kappa([a[x] for x in paired], [b[x] for x in paired])
            if paired
            else None
        ),
        "adjudicated_cases": sum(
            adjudicated.get(row["case_id"]) in DECISIONS for row in rows
        ),
    }


def _calibration_profile() -> dict[str, object]:
    cases = generate_governbench(seed=1708, cases=3000)
    train = [case for i, case in enumerate(cases) if i % 5 not in {0, 1}]
    test = [case for i, case in enumerate(cases) if i % 5 in {0, 1}]
    model = train_calibrator(train)
    evidence = evidence_rows(test)
    labels = [int(item.label_valid) for item in evidence]
    scores = [model.predict_proba(item) for item in evidence]
    return {
        "note": (
            "Held-out synthetic reliability profile. The evidence score is a "
            "thresholded trust score, not a claimed real-world probability."
        ),
        "brier": brier_score(labels, scores),
        "ece": expected_calibration_error(labels, scores),
        "auroc": roc_auc(labels, scores),
        "auprc": pr_auc(labels, scores),
        "threshold": model.threshold,
        "curve": calibration_curve(labels, scores),
    }


def _external_predictions(
    cases: list[GovernCase],
    sources: dict[str, dict[str, object]],
    enabled: tuple[bool, bool, bool],
) -> tuple[dict[str, list[str]], dict[str, object], list[dict[str, object]]]:
    runners = []
    if enabled[0]:
        runners.append(("opa", lambda case: opa_decision(case)))
    if enabled[1]:
        runners.append(("cedar", lambda case: cedar_decision(case)))
    if enabled[2]:
        runners.append(("ollama", lambda case: ollama_decision(case, sources)))
    predictions: dict[str, list[str]] = {}
    status: dict[str, object] = {}
    details: list[dict[str, object]] = []
    for name, runner in runners:
        results = [runner(case) for case in cases]
        predictions[name] = [result.decision for result in results]
        status[name] = {
            "available_cases": sum(result.available for result in results),
            "failed_cases": sum(not result.available for result in results),
            "mean_latency_ms": fmean(result.latency_ms for result in results),
        }
        details.extend(
            {
                "case_id": case.case_id,
                "baseline": name,
                "decision": result.decision,
                "available": result.available,
                "latency_ms": result.latency_ms,
                "detail": result.detail,
            }
            for case, result in zip(cases, results, strict=True)
        )
    return predictions, status, details


def _metrics(truth: list[str], predictions: dict[str, list[str]]) -> dict[str, object]:
    return {
        name: classification_metrics(truth, predicted)
        for name, predicted in predictions.items()
    }


def _per_domain(
    rows: list[dict[str, str]],
    truth: list[str],
    predictions: dict[str, list[str]],
) -> dict[str, object]:
    result = {}
    for domain in DOMAINS:
        idx = [i for i, row in enumerate(rows) if row["domain"] == domain]
        result[domain] = {
            name: classification_metrics(
                [truth[i] for i in idx],
                [predicted[i] for i in idx],
            )
            for name, predicted in predictions.items()
        }
    return result


def _render_html(report: dict[str, object]) -> str:
    agreement = report["human_annotation"]
    label = (
        "HUMAN VALIDATION COMPLETE"
        if report["label_status"] == "human-adjudicated"
        else "DRAFT — HUMAN VALIDATION REQUIRED"
    )
    rows = "".join(
        "<tr>"
        f"<td><b>{html.escape(name)}</b></td>"
        f"<td>{values['accuracy']:.4f}</td>"
        f"<td>{values['macro_f1']:.4f}</td>"
        f"<td>{values['false_allow_rate']:.4f}</td>"
        "</tr>"
        for name, values in report["metrics"].items()
    )
    kappa = agreement["cohen_kappa"]
    kappa_text = "pending" if kappa is None else f"{kappa:.4f}"
    return f"""<!doctype html><meta charset="utf-8">
<title>VeriWeave Publication Validation</title>
<style>
body{{font:15px system-ui;max-width:1100px;margin:40px auto;padding:0 20px;color:#172033}}
.note{{padding:14px;background:#f3f0ff;border-left:5px solid #5a46d6}}
.warn{{font-weight:800;color:#955900}}table{{width:100%;border-collapse:collapse}}
td,th{{padding:10px;border-bottom:1px solid #ddd;text-align:left}}
.card{{display:inline-block;margin:6px;padding:12px 16px;background:#f7f8fb;border-radius:10px}}
</style><h1>VeriWeave publication validation</h1><p class="warn">{label}</p>
<p class="note">{html.escape(report["scientific_boundary"])}</p>
<div class="card">Cases <b>{report["configuration"]["cases"]}</b></div>
<div class="card">Paired annotations <b>{agreement["paired_cases"]}/150</b></div>
<div class="card">Cohen's κ <b>{kappa_text}</b></div>
<h2>Method comparison</h2><table><tr><th>Method</th><th>Accuracy</th>
<th>Macro-F1</th><th>False-Allow</th></tr>{rows}</table>
<h2>Calibration</h2><p>{html.escape(report["calibration"]["note"])}</p>
<p>AUROC <b>{report["calibration"]["auroc"]:.4f}</b> ·
AUPRC <b>{report["calibration"]["auprc"]:.4f}</b> ·
Brier <b>{report["calibration"]["brier"]:.4f}</b> ·
ECE <b>{report["calibration"]["ece"]:.4f}</b></p>
<h2>Reproduce</h2><code>make publication</code>"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("research/validation"),
    )
    parser.add_argument(
        "--sources",
        type=Path,
        default=Path("research/validation/regulatory_sources.json"),
    )
    parser.add_argument("--annotator-a", type=Path)
    parser.add_argument("--annotator-b", type=Path)
    parser.add_argument("--adjudication", type=Path)
    parser.add_argument("--output", type=Path, default=Path("results/publication"))
    parser.add_argument("--opa", action="store_true")
    parser.add_argument("--cedar", action="store_true")
    parser.add_argument("--ollama", action="store_true")
    parser.add_argument("--require-external", action="store_true")
    args = parser.parse_args()

    rows = load_validation_rows(args.dataset)
    sources = load_source_registry(args.sources)
    errors = validate_dataset(rows, sources)
    annotator_a_path = args.annotator_a or args.output / "annotator-a.csv"
    annotator_b_path = args.annotator_b or args.output / "annotator-b.csv"
    adjudication_path = args.adjudication or args.output / "adjudication.csv"
    prepare_annotation_files(
        rows,
        sources,
        annotator_a_path,
        annotator_b_path,
        adjudication_path,
    )
    expected_ids = {row["case_id"] for row in rows}
    for path in (annotator_a_path, annotator_b_path):
        errors.extend(validate_blind_annotation_sheet(load_rows(path), expected_ids))
    if errors:
        raise SystemExit("validation errors:\n- " + "\n- ".join(errors))

    annotation_a = _decisions(annotator_a_path, "decision")
    annotation_b = _decisions(annotator_b_path, "decision")
    adjudicated = _decisions(adjudication_path, "adjudicated_label")
    adjudicated_labels = [adjudicated.get(row["case_id"], "") for row in rows]
    human_complete = all(label in DECISIONS for label in adjudicated_labels)
    truth = (
        adjudicated_labels
        if human_complete
        else [row["provisional_label"] for row in rows]
    )

    cases = [row_to_case(row) for row in rows]
    model = train_calibrator(generate_governbench(seed=911, cases=3000))
    predictions = {
        "rbac": [rbac(case) for case in cases],
        "abac": [abac(case) for case in cases],
        "veriweave": [decide(case, model).decision for case in cases],
    }
    external, external_status, details = _external_predictions(
        cases,
        sources,
        (args.opa, args.cedar, args.ollama),
    )
    predictions.update(external)

    if args.require_external:
        required = {"opa", "cedar", "ollama"}
        missing = required - set(external_status)
        failed = {
            name: info["failed_cases"]
            for name, info in external_status.items()
            if info["failed_cases"]
        }
        if missing or failed:
            raise SystemExit(
                f"external baselines incomplete: missing={sorted(missing)}, failed={failed}"
            )

    report = {
        "schema": "veriweave-publication-validation/v1",
        "scientific_boundary": (
            "Regulation-grounded scenario benchmark. Provisional labels are not "
            "human ground truth or legal advice; publish final performance only "
            "after two independent annotations and full adjudication."
        ),
        "label_status": (
            "human-adjudicated" if human_complete else "provisional-regulation-grounded"
        ),
        "configuration": {
            "cases": len(cases),
            "domains": dict(Counter(row["domain"] for row in rows)),
            "provisional_labels": dict(Counter(row["provisional_label"] for row in rows)),
            "calibration_training": "separate synthetic seed 911",
        },
        "human_annotation": _agreement(
            rows,
            annotation_a,
            annotation_b,
            adjudicated,
        ),
        "metrics": _metrics(truth, predictions),
        "per_domain": _per_domain(rows, truth, predictions),
        "external_status": external_status,
        "calibration": _calibration_profile(),
        "sources": list(sources.values()),
    }

    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (args.output / "report.html").write_text(_render_html(report), encoding="utf-8")
    with (args.output / "predictions.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        fields = [
            "case_id",
            "domain",
            "family",
            "provisional_label",
            "annotator_a",
            "annotator_b",
            "adjudicated_label",
            *predictions,
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for i, row in enumerate(rows):
            case_id = row["case_id"]
            writer.writerow(
                {
                    "case_id": case_id,
                    "domain": row["domain"],
                    "family": row["family"],
                    "provisional_label": row["provisional_label"],
                    "annotator_a": annotation_a.get(case_id, ""),
                    "annotator_b": annotation_b.get(case_id, ""),
                    "adjudicated_label": adjudicated.get(case_id, ""),
                    **{name: values[i] for name, values in predictions.items()},
                }
            )
    with (args.output / "external-details.jsonl").open("w", encoding="utf-8") as handle:
        for item in details:
            handle.write(json.dumps(item, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
