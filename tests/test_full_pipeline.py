from __future__ import annotations

from pathlib import Path

import pytest

from research.full_pipeline import _env_int, _ollama_model_names, build_stages


def test_ollama_model_names_accepts_name_and_model_fields():
    payload = {
        "models": [
            {"name": "gemma4:e2b", "model": "gemma4:e2b"},
            {"name": "qwen:latest"},
            {"model": "other:model"},
        ]
    }
    assert _ollama_model_names(payload) == {
        "gemma4:e2b",
        "qwen:latest",
        "other:model",
    }


def test_full_pipeline_plan_contains_all_publication_stages(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("GOVERNBENCH_SEEDS", "3")
    monkeypatch.setenv("GOVERNBENCH_CASES", "300")
    monkeypatch.setenv("PUBLICATION_BOOTSTRAP_SAMPLES", "1000")
    monkeypatch.setenv("LOAD_MATRIX_REQUESTS_PER_LEVEL", "1000")

    stages = build_stages(tmp_path)
    names = [name for name, _ in stages]
    assert names == [
        "governbench",
        "service-benchmark",
        "legal-audit",
        "publication-validation",
        "publication-statistics",
        "calibration-reliability",
        "load-matrix",
    ]

    publication = dict(stages)["publication-validation"]
    assert "--opa" in publication
    assert "--cedar" in publication
    assert "--ollama" in publication
    assert "--require-external" in publication

    flattened = " ".join(item for _, command in stages for item in command).lower()
    assert "ollama pull" not in flattened


def test_pipeline_rejects_too_small_bootstrap(monkeypatch):
    monkeypatch.setenv("PUBLICATION_BOOTSTRAP_SAMPLES", "999")
    with pytest.raises(ValueError, match="PUBLICATION_BOOTSTRAP_SAMPLES"):
        build_stages(Path("results"))


def test_env_int_allows_zero_when_requested(monkeypatch):
    monkeypatch.setenv("PUBLICATION_BOOTSTRAP_SEED", "0")
    assert _env_int("PUBLICATION_BOOTSTRAP_SEED", 1, 0) == 0
