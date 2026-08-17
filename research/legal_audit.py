from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

VALIDATION_FILES = (
    "public-administration-1.csv",
    "public-administration-2.csv",
    "enterprise-it-devops-1.csv",
    "enterprise-it-devops-2.csv",
    "data-ai-governance-1.csv",
    "data-ai-governance-2.csv",
)
EXPECTED_DOMAINS = {
    "public-administration": 50,
    "enterprise-it-devops": 50,
    "data-ai-governance": 50,
}
EXPECTED_LABELS = {"allow": 50, "review": 50, "deny": 50}
PRIMARY_SOURCE_HOSTS = {"eur-lex.europa.eu", "www.ris.bka.gv.at", "ris.bka.gv.at"}
AI_ACT_ANNEX_III_DATE = "2027-12-02"
AI_ACT_FUTURE_IDS = {
    "EU-AIA-6-ANNEXIII",
    "EU-AIA-13-14",
    "EU-AIA-26",
    "EU-AIA-27",
}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def audit(validation_dir: Path) -> dict[str, object]:
    registry_path = validation_dir / "regulatory_sources.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    snapshot = _parse_date(registry["snapshot_date"])
    sources = {item["id"]: item for item in registry["sources"]}

    rows: list[dict[str, str]] = []
    partition_counts: dict[str, int] = {}
    for filename in VALIDATION_FILES:
        partition = _read_csv(validation_dir / filename)
        partition_counts[filename] = len(partition)
        rows.extend(partition)

    errors: list[str] = []
    warnings: list[str] = []

    if len(rows) != 150:
        errors.append(f"expected 150 cases, received {len(rows)}")
    if any(count != 25 for count in partition_counts.values()):
        errors.append(f"each review partition must contain 25 cases: {partition_counts}")

    domain_counts = Counter(row["domain"] for row in rows)
    if dict(domain_counts) != EXPECTED_DOMAINS:
        errors.append(f"expected 50 cases per domain, received {dict(domain_counts)}")

    label_counts = Counter(row["provisional_label"] for row in rows)
    if dict(label_counts) != EXPECTED_LABELS:
        errors.append(f"expected balanced provisional labels, received {dict(label_counts)}")

    case_ids = [row["case_id"] for row in rows]
    if len(case_ids) != len(set(case_ids)):
        errors.append("case_id values must be unique")

    if "EU-AIA-OMNIBUS-2026-1744" not in sources:
        errors.append("Digital Omnibus Regulation (EU) 2026/1744 is missing from source registry")
    for source_id in AI_ACT_FUTURE_IDS:
        source = sources.get(source_id)
        if not source:
            errors.append(f"missing required AI Act source: {source_id}")
            continue
        if source.get("applicable_from") != AI_ACT_ANNEX_III_DATE:
            errors.append(
                f"{source_id} must reflect Regulation (EU) 2026/1744 Annex III date "
                f"{AI_ACT_ANNEX_III_DATE}, received {source.get('applicable_from')}"
            )

    for source_id, source in sources.items():
        host = urlparse(str(source["url"])).hostname or ""
        if host not in PRIMARY_SOURCE_HOSTS:
            errors.append(f"{source_id}: non-primary source host {host!r}")
        verified_on = _parse_date(str(source["verified_on"]))
        if verified_on > snapshot:
            errors.append(f"{source_id}: verified_on is after registry snapshot")
        _parse_date(str(source["applicable_from"]))

    temporal_cases = 0
    for row in rows:
        evaluation_date = _parse_date(row["evaluation_date"])
        source_ids = [item for item in row["source_ids"].split("|") if item]
        if not source_ids:
            errors.append(f"{row['case_id']}: no legal-source provenance")
            continue
        for source_id in source_ids:
            source = sources.get(source_id)
            if source is None:
                errors.append(f"{row['case_id']}: unknown source {source_id}")
                continue
            applicable_from = _parse_date(str(source["applicable_from"]))
            if evaluation_date < applicable_from:
                errors.append(
                    f"{row['case_id']}: evaluation date {evaluation_date} predates "
                    f"{source_id} applicability {applicable_from}"
                )
            if evaluation_date > snapshot:
                temporal_cases += 1
        if evaluation_date > snapshot and "future" not in row["legal_status"]:
            warnings.append(
                f"{row['case_id']}: post-snapshot evaluation should be explicitly marked future"
            )

    return {
        "schema": "veriweave-legal-audit/v1",
        "snapshot_date": registry["snapshot_date"],
        "status": "pass" if not errors else "fail",
        "cases": len(rows),
        "partition_counts": partition_counts,
        "domain_counts": dict(domain_counts),
        "provisional_label_counts": dict(label_counts),
        "source_count": len(sources),
        "primary_source_hosts": sorted(PRIMARY_SOURCE_HOSTS),
        "temporal_source_references": temporal_cases,
        "ai_act_annex_iii_application_date": AI_ACT_ANNEX_III_DATE,
        "errors": errors,
        "warnings": warnings,
        "scientific_boundary": (
            "This audit verifies dataset/source consistency and temporal applicability. "
            "It does not determine legal compliance and does not replace expert annotation."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit publication legal-source snapshot")
    parser.add_argument(
        "--validation-dir",
        type=Path,
        default=Path("research/validation"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/publication/legal-audit.json"),
    )
    args = parser.parse_args()
    report = audit(args.validation_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    if report["status"] != "pass":
        for error in report["errors"]:
            print(f"ERROR: {error}")
        return 1
    print(
        f"Legal-source audit passed: {report['cases']} cases, "
        f"{report['source_count']} primary-law source records"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
