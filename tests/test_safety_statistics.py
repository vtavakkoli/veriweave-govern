import math

import pytest

from research.metrics import classification_metrics, exact_binomial_interval, safety_metrics
from research.publication_statistics import build_report


def test_zero_events_have_nonzero_exact_uncertainty():
    bound = exact_binomial_interval(0, 70)
    assert bound["ci95_low"] == 0
    assert bound["ci95_high"] == pytest.approx(1 - 0.025 ** (1 / 70))
    assert bound["upper_one_sided"] == pytest.approx(1 - 0.05 ** (1 / 70))
    assert bound["ci95_high"] > bound["upper_one_sided"] > 0


def test_conditional_metric_is_prevalence_independent_and_empty_is_undefined():
    a = classification_metrics(["allow", "deny", "review"], ["allow", "allow", "review"])
    b = classification_metrics(
        ["allow"] * 20 + ["deny", "review"], ["allow"] * 21 + ["review"],
    )
    assert a["conditional_unsafe_allow_rate"] == b["conditional_unsafe_allow_rate"] == 0.5
    assert a["false_allow_rate"] != b["false_allow_rate"]
    empty = safety_metrics(["allow"], ["allow"])["conditional_unsafe_allow_rate"]
    assert empty["estimate"] is None and empty["ci95_high"] is None


def test_nonzero_exact_interval_and_parameter_validation():
    interval = exact_binomial_interval(5, 10)
    assert interval["ci95_low"] == pytest.approx(0.1870860284)
    assert interval["ci95_high"] == pytest.approx(0.8129139716)
    assert interval["upper_one_sided"] > 0.5
    assert exact_binomial_interval(10, 10)["ci95_high"] == 1
    assert math.isclose(exact_binomial_interval(10, 10)["ci95_low"], 0.025 ** 0.1)
    with pytest.raises(ValueError):
        exact_binomial_interval(2, 1)


def test_report_preserves_denominator_and_does_not_bootstrap_zero_risk():
    rows = [
        {"case_id": str(i), "domain": "test", "provisional_label": truth,
         "veriweave": truth, "adjudicated_label": ""}
        for i, truth in enumerate(["allow"] * 80 + ["review"] * 20 + ["deny"] * 50)
    ]
    report = build_report(rows, ["veriweave"], samples=1000, seed=17)
    metric = report["metrics"]["veriweave"]["conditional_unsafe_allow_rate"]
    assert metric["events"] == 0 and metric["trials"] == 70
    assert metric["ci95_high"] > 0.05
