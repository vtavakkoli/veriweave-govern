import csv
import json

import pytest

from research.annotation_audit import audit_annotations


def test_equal_mean_confidence_does_not_imply_casewise_equality(tmp_path):
    for name, confidence in (("a", [4, 5]), ("b", [5, 4])):
        with (tmp_path / f"{name}.csv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=("case_id", "decision", "confidence_1_to_5"))
            writer.writeheader()
            writer.writerows(
                {"case_id": str(i), "decision": label, "confidence_1_to_5": confidence[i]}
                for i, label in enumerate(("allow", "deny"))
            )
    disclosures = tmp_path / "disclosures.json"
    disclosures.write_text(json.dumps({"relationship_to_authors": None}))
    report = audit_annotations(tmp_path / "a.csv", tmp_path / "b.csv", disclosures)
    assert report["cohen_kappa"] == 1
    assert report["confidence_distributions"]["A"] == report["confidence_distributions"]["B"]
    assert report["confidence_casewise_agreement"] == 0
    assert not report["disclosure_complete"]
    assert "relationship_to_authors" in report["missing_disclosures"]
    with (tmp_path / "a.csv").open("a") as handle:
        handle.write("0,allow,4\n")
    with pytest.raises(ValueError, match="duplicate"):
        audit_annotations(tmp_path / "a.csv", tmp_path / "b.csv", disclosures)
