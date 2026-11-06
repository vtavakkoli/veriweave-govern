"""Audit paired annotation records and disclosures without inventing study facts."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from research.human_eval import cohen_kappa

DECISIONS = {"allow", "review", "deny"}
DISCLOSURES = (
    "relationship_to_authors", "professional_expertise", "legal_governance_experience",
    "recruitment", "pilot_or_training", "case_difficulty_selection",
)


def _read(path: Path) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    ids = [row["case_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError(f"duplicate case ID in {path.name}")
    for row in rows:
        if row["decision"] not in DECISIONS:
            raise ValueError("all decisions must be completed before an annotation audit")
        confidence = row.get("confidence_1_to_5", "")
        if confidence not in {"1", "2", "3", "4", "5"}:
            raise ValueError("each completed annotation requires confidence 1-5")
    return {row["case_id"]: row for row in rows}


def audit_annotations(a_path: Path, b_path: Path, disclosure_path: Path) -> dict[str, object]:
    a, b = _read(a_path), _read(b_path)
    if not a or set(a) != set(b):
        raise ValueError("annotation sheets must have identical, nonempty case ID sets")
    disclosures = json.loads(disclosure_path.read_text(encoding="utf-8"))
    missing = [field for field in DISCLOSURES if disclosures.get(field) in (None, "", [])]
    ids = sorted(a)
    confidence = {
        name: dict(sorted(Counter(row["confidence_1_to_5"] for row in sheet.values()).items()))
        for name, sheet in (("A", a), ("B", b))
    }
    return {
        "schema": "veriweave-annotation-audit/v1", "cases": len(ids),
        "raw_agreement": sum(a[i]["decision"] == b[i]["decision"] for i in ids) / len(ids),
        "cohen_kappa": cohen_kappa([a[i]["decision"] for i in ids], [b[i]["decision"] for i in ids]),
        "confidence_distributions": confidence,
        "confidence_casewise_agreement": sum(
            a[i]["confidence_1_to_5"] == b[i]["confidence_1_to_5"] for i in ids
        ) / len(ids),
        "disagreements": [i for i in ids if a[i]["decision"] != b[i]["decision"]],
        "input_sha256": {
            name: hashlib.sha256(path.read_bytes()).hexdigest()
            for name, path in (("annotator_a", a_path), ("annotator_b", b_path), ("disclosures", disclosure_path))
        },
        "disclosures": disclosures, "missing_disclosures": missing,
        "disclosure_complete": not missing,
        "boundary": "Worksheet agreement does not establish author independence or legal expertise.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotator-a", type=Path, required=True)
    parser.add_argument("--annotator-b", type=Path, required=True)
    parser.add_argument("--disclosures", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = audit_annotations(args.annotator_a, args.annotator_b, args.disclosures)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True))
    print(json.dumps({"cases": report["cases"], "disclosure_complete": report["disclosure_complete"]}))
    return 0 if report["disclosure_complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
