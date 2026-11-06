"""Generate the revision's LaTeX tables directly from recorded implementation outputs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def generate(results: Path, paper: Path) -> None:
    report = json.loads((results / "validation.json").read_text())
    table_dir = paper / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)
    groups = (
        ("Audit faults and checkpoint control", report["audit_faults"]),
        ("Historical replay", report["temporal_replay"]),
        ("Authenticated evidence fixtures", report["evidence_admission"]),
    )
    rows = [
        f"{name} & {sum(bool(row['passed']) for row in values)}/{len(values)} " + r"\\"
        for name, values in groups
    ]
    concurrent = report["concurrent_snapshot"]
    rows.append(f"Concurrent decision/hash mismatches & {concurrent['bundle_decision_mismatches']} / "
                f"{concurrent['requests']} " + r"\\")
    total = sum(row["requests"] for row in report["scale"])
    errors = sum(row["failures"] for row in report["scale"])
    rows.append(f"Scale decision failures & {errors} / {total} " + r"\\")
    (table_dir / "revision_validation.tex").write_text(
        r"\begin{table}[t]" + "\n" +
        r"\caption{New implementation experiments (researcher-authored fixtures).}" + "\n" +
        r"\label{tab:revision-validation}\centering\footnotesize" + "\n" +
        r"\begin{tabular}{lr}\toprule Check & Result \\\midrule" + "\n" +
        "\n".join(rows) + "\n" + r"\bottomrule\end{tabular}\end{table}" + "\n"
    )
    scale_rows = [
        f"{row['rules']:,} & {row['evidence_items']} & {row['mean_ms']:.2f} & {row['p95_ms']:.2f} " + r"\\"
        for row in report["scale"]
    ]
    (table_dir / "revision_scale.tex").write_text(
        r"\begin{table}[t]" + "\n" +
        r"\caption{Single-process engine plus JSONL append; 100 sequential calls per cell.}" + "\n" +
        r"\label{tab:revision-scale}\centering\footnotesize" + "\n" +
        r"\begin{tabular}{rrrr}\toprule Rules & Evidence & Mean (ms) & P95 (ms) \\\midrule" + "\n" +
        "\n".join(scale_rows) + "\n" + r"\bottomrule\end{tabular}\end{table}" + "\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=Path("results/revision-2026-11"))
    parser.add_argument("--paper", type=Path, default=Path("paper"))
    args = parser.parse_args()
    generate(args.results, args.paper)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
