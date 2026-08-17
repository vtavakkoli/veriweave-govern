from __future__ import annotations

from research.publication_statistics import build_report


def _row(index: int, truth: str, veriweave: str, baseline: str) -> dict[str, str]:
    return {
        "case_id": f"case-{index:03d}",
        "domain": "public-administration" if index < 50 else "enterprise-it-devops",
        "family": "test",
        "provisional_label": truth,
        "annotator_a": "",
        "annotator_b": "",
        "adjudicated_label": "",
        "veriweave": veriweave,
        "rbac": baseline,
    }


def test_publication_statistics_are_reproducible_and_mark_provisional_labels():
    truths = ["allow", "review", "deny"] * 40
    rows = [
        _row(
            index,
            truth,
            truth,
            truth if index % 4 else "review" if truth != "review" else "allow",
        )
        for index, truth in enumerate(truths)
    ]
    report_a = build_report(rows, ["veriweave", "rbac"], samples=1000, seed=77)
    report_b = build_report(rows, ["veriweave", "rbac"], samples=1000, seed=77)
    assert report_a == report_b
    assert report_a["label_status"] == "provisional-regulation-grounded"
    assert report_a["metrics"]["veriweave"]["accuracy"]["estimate"] == 1.0
    assert (
        report_a["paired_comparisons"]["rbac"]
        ["accuracy_difference_reference_minus_baseline"]["estimate"]
        > 0
    )
    assert 0.0 <= report_a["paired_comparisons"]["rbac"]["mcnemar_holm_adjusted_p"] <= 1.0


def test_complete_adjudication_becomes_the_only_final_truth_source():
    rows = [
        {
            "case_id": f"case-{index}",
            "domain": "data-ai-governance",
            "family": "test",
            "provisional_label": "allow",
            "annotator_a": "deny",
            "annotator_b": "deny",
            "adjudicated_label": "deny",
            "veriweave": "deny",
            "rbac": "allow",
        }
        for index in range(12)
    ]
    report = build_report(rows, ["veriweave", "rbac"], samples=1000, seed=99)
    assert report["label_status"] == "human-adjudicated"
    assert report["metrics"]["veriweave"]["accuracy"]["estimate"] == 1.0
    assert report["metrics"]["rbac"]["accuracy"]["estimate"] == 0.0
