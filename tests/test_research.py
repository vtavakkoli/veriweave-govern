from __future__ import annotations

from consulting.readiness import vgri
from research.calibration import train_calibrator
from research.dataset import generate_governbench
from research.governor import counterfactuals, decide, governance_certificate
from research.human_eval import cohen_kappa
from research.metrics import classification_metrics


def test_governbench_generator_is_deterministic():
    assert [c.to_dict() for c in generate_governbench(9, 30)] == [c.to_dict() for c in generate_governbench(9, 30)]


def test_governance_safety_properties():
    cases = generate_governbench(seed=3, cases=180)
    model = train_calibrator(cases[:120], epochs=250)
    conflict = next(c for c in cases if c.category == "policy-conflict")
    assert decide(conflict, model).decision == "deny"
    assert all(decide(c, model).decision != "allow" for c in cases if c.category == "missing-evidence")
    ood = next(c for c in cases if c.category == "ood")
    assert decide(ood, model).decision == "review"
    for case in (c for c in cases if c.category == "temporal"):
        assert decide(case, model).decision == case.ground_truth


def test_counterfactual_certificate_metrics_and_consulting_index():
    cases = generate_governbench(seed=4, cases=90)
    model = train_calibrator(cases[:60], epochs=200)
    case = next(c for c in cases if c.category == "allow")
    assert any(item["decision"] == "deny" for item in counterfactuals(case, model))
    assert governance_certificate(case, model)["schema"] == "veriweave-governance-certificate/v1"
    assert classification_metrics(["deny", "review", "allow"], ["allow", "allow", "allow"])["false_allow_rate"] > 0
    assert vgri({"policy_coverage":80,"evidence_quality":70,"human_oversight":90,"auditability":90,"security":75,"resilience":65,"operational_readiness":70}) > 70
    assert cohen_kappa(["allow", "deny"], ["allow", "deny"]) == 1.0
