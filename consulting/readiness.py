from __future__ import annotations

import argparse
import json
from pathlib import Path

WEIGHTS = {
    "policy_coverage": 0.20,
    "evidence_quality": 0.20,
    "human_oversight": 0.15,
    "auditability": 0.15,
    "security": 0.10,
    "resilience": 0.10,
    "operational_readiness": 0.10,
}


def vgri(scores: dict[str, float]) -> float:
    missing = set(WEIGHTS) - set(scores)
    if missing:
        raise ValueError(f"missing VGRI dimensions: {sorted(missing)}")
    for key, value in scores.items():
        if key in WEIGHTS and not 0 <= float(value) <= 100:
            raise ValueError(f"{key} must be between 0 and 100")
    return round(sum(float(scores[key]) * weight for key, weight in WEIGHTS.items()), 2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Calculate the VeriWeave Governance Readiness Index")
    parser.add_argument("assessment", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.assessment.read_text(encoding="utf-8"))
    payload["vgri"] = vgri(payload["scores"])
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
