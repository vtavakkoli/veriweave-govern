from __future__ import annotations

from pathlib import Path

import pytest

from benchmark.load_matrix import _concurrencies
from research.calibration import train_calibrator
from research.dataset import generate_governbench
from research.governor import decide
from research.legal_audit import audit
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
from research.reliability_report import render_svg

ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "research" / "validation"


def test_regulatory_validation_set_is_complete_balanced_and_source_grounded():
    rows = load_validation_rows(VALIDATION)
    sources = load_source_registry(VALIDATION / "regulatory_sources.json")
    assert validate_dataset(rows, sources) == []
    assert len(rows) == 150


def test_primary_law_temporal_audit_passes():
    report = audit(VALIDATION)
    assert report["status"] == "pass"
    assert report["errors"] == []
    assert report["warnings"] == []
    assert report["cases"] == 150
    assert report["source_count"] >= 20
    assert report["ai_act_annex_iii_application_date"] == "2027-12-02"


def test_digital_omnibus_source_is_pinned_and_future_cases_are_explicit():
    registry = load_source_registry(VALIDATION / "regulatory_sources.json")
    assert "EU-AIA-OMNIBUS-2026-1744" in registry
    for source_id in ("EU-AIA-6-ANNEXIII", "EU-AIA-13-14", "EU-AIA-26", "EU-AIA-27"):
        assert registry[source_id]["applicable_from"] == "2027-12-02"

    rows = load_validation_rows(VALIDATION)
    annex_iii_ids = {
        row["case_id"]
        for row in rows
        if "EU-AIA-6-ANNEXIII" in row["source_ids"].split("|")
    }
    assert annex_iii_ids
    by_id = {row["case_id"]: row for row in rows}
    assert all(by_id[case_id]["evaluation_date"] >= "2027-12-02" for case_id in annex_iii_ids)
    assert all("future" in by_id[case_id]["legal_status"] for case_id in annex_iii_ids)


def test_publication_uses_real_edge_ollama_model_contract():
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    external = (ROOT / "research" / "external_baselines.py").read_text(encoding="utf-8")
    assert "http://host.docker.internal:11434" in compose
    assert "OLLAMA_MODEL: ${OLLAMA_MODEL:-gemma4:e2b}" in compose
    assert 'os.getenv("OLLAMA_MODEL", "gemma4:e2b")' in external


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


def test_load_matrix_concurrency_parser_is_strict():
    assert _concurrencies("1,4,16,32") == [1, 4, 16, 32]
    with pytest.raises(ValueError):
        _concurrencies("1,0,4")


def test_reliability_svg_contains_accessible_labels_and_points():
    svg = render_svg(
        [
            {
                "bin_low": 0.7,
                "bin_high": 0.8,
                "count": 25,
                "mean_confidence": 0.76,
                "empirical_accuracy": 0.72,
            }
        ]
    )
    assert "Evidence reliability diagram" in svg
    assert "Mean trust score" in svg
    assert "circle" in svg
