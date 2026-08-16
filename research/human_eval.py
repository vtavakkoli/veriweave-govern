from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import fmean


def cohen_kappa(a: list[str], b: list[str]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    observed = sum(x == y for x, y in zip(a, b, strict=True)) / len(a)
    labels = sorted(set(a) | set(b))
    pa = {label: a.count(label) / len(a) for label in labels}
    pb = {label: b.count(label) / len(b) for label in labels}
    expected = sum(pa[label] * pb[label] for label in labels)
    return (observed - expected) / max(1.0 - expected, 1e-12)


def score_annotations(path: Path) -> dict[str, object]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    by_annotator: dict[str, dict[str, str]] = defaultdict(dict)
    durations: list[float] = []
    confidences: list[float] = []
    for row in rows:
        by_annotator[row["annotator_id"]][row["case_id"]] = row["decision"]
        if row.get("duration_seconds"):
            durations.append(float(row["duration_seconds"]))
        if row.get("confidence"):
            confidences.append(float(row["confidence"]))
    annotators = sorted(by_annotator)
    kappas: list[float] = []
    for i, left in enumerate(annotators):
        for right in annotators[i + 1:]:
            shared = sorted(set(by_annotator[left]) & set(by_annotator[right]))
            kappas.append(cohen_kappa([by_annotator[left][case] for case in shared], [by_annotator[right][case] for case in shared]))
    return {
        "annotators": len(annotators), "annotations": len(rows),
        "pairwise_cohen_kappa_mean": fmean(kappas) if kappas else 0.0,
        "mean_duration_seconds": fmean(durations) if durations else None,
        "mean_confidence": fmean(confidences) if confidences else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("annotations", type=Path)
    args = parser.parse_args()
    print(json.dumps(score_annotations(args.annotations), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
