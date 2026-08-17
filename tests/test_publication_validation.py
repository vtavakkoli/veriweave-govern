from __future__ import annotations

from pathlib import Path

from research.calibration import train_calibrator
from research.dataset import generate_governbench
from research.governor import decide
from research.metrics import calibration_curve
from research.regulatory_validation import (
    load_rows,
    load_source_registry,
    load_validation_rows,
    prepare_annotation_files,
    row_to_case,
    validate_blind_annotation_sheet,
    validate_dataset,
)

ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "research" / "validation"


def test_regulatory_validation_set_is_complete_balanced_and_source_grounded():
    rows = load_validation_rows(VALIDATION)
    sources = load_source_registry(VALIDATION / "regulatory_sources.json")
    assert validate_dataset(rows, sources) == []
    assert len(rows) == 150


def test_generated_annotation_sheets_are_blind_and_cover_all_cases(tmp_path):
    master = load_validation_rows(VALIDATION)
    sources = load_source_registry(VALIDATION / "regulatory_sources.json")
    annotation_a = tmp_path / "annotator-a.csv"
    annotation_b = tmp_path / "annotator-b.csv"
    adjudication = tmp_path / "adjudication.csv"
    prepare_annotation_files(
        master,
        sources,
        annotation_a,
        annotation_b,
        adjudication,
    )
    expected = {row["case_id"] for row in master}
    for path in (annotation_a, annotation_b):
        rows = load_rows(path)
        assert validate_blind_annotation_sheet(rows, expected) == []
        assert all(not row["decision"] for row in rows)


def test_regulation_grounded_cases_execute_without_invalid_decisions():
    rows = load_validation_rows(VALIDATION)
    model = train_calibrator(generate_governbench(seed=911, cases=3000))
    cases = [row_to_case(row) for row in rows]
    predictions = [decide(case, model).decision for case in cases]
    assert len(predictions) == 150
    assert set(predictions) <= {"allow", "review", "deny"}


def test_explicit_prohibition_is_fail_closed():
    rows = load_validation_rows(VALIDATION)
    prohibited = next(row for row in rows if row["prohibition_reason"])
    model = train_calibrator(generate_governbench(seed=12, cases=180))
    trace = decide(row_to_case(prohibited), model)
    assert trace.decision == "deny"
    assert "explicit legal/policy prohibition" in trace.reasons[0]


def test_calibration_curve_accounts_for_every_sample():
    rows = calibration_curve([0, 0, 1, 1], [0.1, 0.4, 0.7, 0.95])
    assert sum(int(row["count"]) for row in rows) == 4
