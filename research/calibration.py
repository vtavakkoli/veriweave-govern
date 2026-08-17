from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import asdict, dataclass

from research.model import Evidence, GovernCase

REFERENCE_TERMS = ("section", "article", "control", "policy", "requirement", "clause")


def _features(item: Evidence) -> list[float]:
    text = item.content.lower()
    return [
        item.authority / 100.0,
        1.0 if item.current else 0.0,
        1.0 if item.signed else 0.0,
        min(len(item.content.split()) / 24.0, 1.0),
        1.0 if any(term in text for term in REFERENCE_TERMS) else 0.0,
        1.0 if item.contradiction else 0.0,
    ]


def _sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


@dataclass
class EvidenceCalibrationModel:
    weights: list[float]
    bias: float
    threshold: float
    feature_names: tuple[str, ...] = (
        "authority",
        "current",
        "signed",
        "substantive_content",
        "policy_reference_language",
        "contradiction",
    )

    def predict_proba(self, item: Evidence) -> float:
        score = self.bias + sum(w * x for w, x in zip(self.weights, _features(item), strict=True))
        return _sigmoid(score)

    def accepts(self, item: Evidence) -> bool:
        return self.predict_proba(item) >= self.threshold

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def evidence_rows(cases: Iterable[GovernCase]) -> list[Evidence]:
    return [item for case in cases for item in case.evidence]


def train_calibrator(
    cases: Iterable[GovernCase],
    *,
    epochs: int = 120,
    learning_rate: float = 0.35,
    l2: float = 0.001,
) -> EvidenceCalibrationModel:
    rows = evidence_rows(cases)
    if not rows:
        return EvidenceCalibrationModel([0.0] * 6, 0.0, 0.5)

    weights = [0.0] * 6
    bias = 0.0
    n = float(len(rows))
    for _ in range(epochs):
        grad_w = [0.0] * len(weights)
        grad_b = 0.0
        for item in rows:
            x = _features(item)
            y = 1.0 if item.label_valid else 0.0
            p = _sigmoid(bias + sum(w * value for w, value in zip(weights, x, strict=True)))
            error = p - y
            for i, value in enumerate(x):
                grad_w[i] += error * value
            grad_b += error
        for i in range(len(weights)):
            grad_w[i] = grad_w[i] / n + l2 * weights[i]
            weights[i] -= learning_rate * grad_w[i]
        bias -= learning_rate * grad_b / n

    provisional = EvidenceCalibrationModel(weights, bias, 0.5)
    best_threshold = 0.5
    best_cost = float("inf")
    for step in range(20, 91):
        threshold = step / 100.0
        false_accept = 0
        false_reject = 0
        for item in rows:
            pred = provisional.predict_proba(item) >= threshold
            false_accept += int(pred and not item.label_valid)
            false_reject += int((not pred) and item.label_valid)
        cost = 3 * false_accept + false_reject
        if cost < best_cost:
            best_cost = cost
            best_threshold = threshold
    provisional.threshold = best_threshold
    return provisional
