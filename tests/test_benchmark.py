from benchmark.runner import (
    HttpResult,
    ScenarioResult,
    build_report,
    percentile,
    render_html_report,
    validate_response,
)


def test_percentile_interpolates_values() -> None:
    assert percentile([1.0, 2.0, 3.0, 4.0], 0.5) == 2.5
    assert percentile([], 0.95) == 0.0


def test_validate_response_accepts_expected_governance_result() -> None:
    scenario = {
        "expect": {
            "status": 200,
            "decision": "allow",
            "review_queue": None,
            "matched_rules": ["allow-low-risk-read"],
            "min_accepted_evidence": 1,
            "min_evidence_score": 0.9,
            "audit_signature": True,
            "policy_set_hash": True,
        }
    }
    response = HttpResult(
        status=200,
        latency_ms=2.5,
        body={
            "decision": "allow",
            "review_queue": None,
            "matched_rules": [
                {"rule_id": "allow-low-risk-read", "missing_evidence": []}
            ],
            "evidence_assessments": [{"accepted": True, "score": 0.965}],
            "audit": {"signature": "signed"},
            "policy_set_hash": "abc123",
            "reasons": ["allowed"],
        },
    )

    errors, extracted = validate_response(scenario, response)

    assert errors == []
    assert extracted["actual_decision"] == "allow"
    assert extracted["matched_rules"] == ["allow-low-risk-read"]


def test_validate_response_reports_missing_expectations() -> None:
    scenario = {
        "expect": {
            "status": 200,
            "decision": "deny",
            "matched_rules": ["prohibit-secret-exfiltration"],
        }
    }
    response = HttpResult(status=200, latency_ms=1.0, body={"decision": "review"})

    errors, _ = validate_response(scenario, response)

    assert "expected decision 'deny', received 'review'" in errors
    assert "expected matched rule 'prohibit-secret-exfiltration'" in errors


def test_report_marks_invalid_audit_as_failure() -> None:
    scenario = ScenarioResult(
        scenario_id="example",
        name="Example scenario",
        category="allow",
        description="Example",
        passed=True,
        expected_status=200,
        actual_status=200,
        expected_decision="allow",
        actual_decision="allow",
        review_queue=None,
        matched_rules=["allow-low-risk-read"],
        evidence_scores=[0.95],
        latency_ms=2.0,
        errors=[],
        request={"agent_id": "agent"},
        response={"decision": "allow"},
    )
    performance = {
        "requests": 1,
        "concurrency": 1,
        "iterations_per_scenario": 1,
        "duration_seconds": 0.01,
        "requests_per_second": 100.0,
        "mean_ms": 2.0,
        "median_ms": 2.0,
        "p95_ms": 2.0,
        "p99_ms": 2.0,
        "max_ms": 2.0,
        "decision_distribution": {"allow": 1},
        "failures": [],
        "scenarios": [
            {
                "scenario_id": "example",
                "name": "Example scenario",
                "requests": 1,
                "mean_ms": 2.0,
                "median_ms": 2.0,
                "p95_ms": 2.0,
                "max_ms": 2.0,
            }
        ],
    }

    report = build_report(
        "http://govern:8080",
        {"status": "ok"},
        {"policy_set_hash": "abc"},
        [scenario],
        performance,
        {"valid": False, "records": 1},
    )
    rendered = render_html_report(report)

    assert report["summary"]["overall_passed"] is False
    assert "FAILED" in rendered
    assert "Example scenario" in rendered
