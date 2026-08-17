from __future__ import annotations

import random
from collections.abc import Iterable
from statistics import fmean

CLASSES = ("allow", "review", "deny")


def classification_metrics(truth: list[str], predicted: list[str]) -> dict[str, float]:
    if len(truth) != len(predicted):
        raise ValueError("truth and predicted lengths differ")
    n = max(len(truth), 1)
    accuracy = sum(t == p for t, p in zip(truth, predicted, strict=True)) / n
    f1s: list[float] = []
    for label in CLASSES:
        tp = sum(t == label and p == label for t, p in zip(truth, predicted, strict=True))
        fp = sum(t != label and p == label for t, p in zip(truth, predicted, strict=True))
        fn = sum(t == label and p != label for t, p in zip(truth, predicted, strict=True))
        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        f1s.append(2 * precision * recall / max(precision + recall, 1e-12))
    return {
        "accuracy": accuracy,
        "macro_f1": fmean(f1s),
        "false_allow_rate": sum(t != "allow" and p == "allow" for t, p in zip(truth, predicted, strict=True)) / n,
        "false_deny_rate": sum(t == "allow" and p == "deny" for t, p in zip(truth, predicted, strict=True)) / n,
        "false_review_rate": sum(t == "allow" and p == "review" for t, p in zip(truth, predicted, strict=True)) / n,
    }


def attack_success_rate(truth: list[str], predicted: list[str], is_attack: list[bool]) -> float:
    eligible = [i for i, attacked in enumerate(is_attack) if attacked and truth[i] != "allow"]
    if not eligible:
        return 0.0
    return sum(predicted[i] == "allow" for i in eligible) / len(eligible)


def brier_score(labels: list[int], probabilities: list[float]) -> float:
    return fmean((p - y) ** 2 for y, p in zip(labels, probabilities, strict=True)) if labels else 0.0


def expected_calibration_error(labels: list[int], probabilities: list[float], bins: int = 10) -> float:
    if not labels:
        return 0.0
    total = len(labels)
    error = 0.0
    for b in range(bins):
        low, high = b / bins, (b + 1) / bins
        idx = [i for i, p in enumerate(probabilities) if low <= p < high or (b == bins - 1 and p == 1.0)]
        if idx:
            confidence = fmean(probabilities[i] for i in idx)
            accuracy = fmean(labels[i] for i in idx)
            error += len(idx) / total * abs(confidence - accuracy)
    return error


def roc_auc(labels: list[int], scores: list[float]) -> float:
    positives = [s for y, s in zip(labels, scores, strict=True) if y == 1]
    negatives = [s for y, s in zip(labels, scores, strict=True) if y == 0]
    if not positives or not negatives:
        return 0.0
    wins = sum(1.0 if p > n else 0.5 if p == n else 0.0 for p in positives for n in negatives)
    return wins / (len(positives) * len(negatives))


def pr_auc(labels: list[int], scores: list[float]) -> float:
    pairs = sorted(zip(scores, labels, strict=True), reverse=True)
    positives = sum(labels)
    if positives == 0:
        return 0.0
    tp = fp = 0
    prev_recall = area = 0.0
    for _, label in pairs:
        tp += int(label == 1)
        fp += int(label == 0)
        recall = tp / positives
        precision = tp / max(tp + fp, 1)
        area += (recall - prev_recall) * precision
        prev_recall = recall
    return area


def bootstrap_ci(values: list[float], confidence: float = 0.95, samples: int = 2000, seed: int = 7) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    if len(values) == 1:
        return values[0], values[0]
    rng = random.Random(seed)
    means = sorted(fmean([rng.choice(values) for _ in values]) for _ in range(samples))
    alpha = (1.0 - confidence) / 2.0
    return means[int(alpha * (len(means) - 1))], means[int((1.0 - alpha) * (len(means) - 1))]


def summarize_runs(rows: Iterable[dict[str, float]], metrics: tuple[str, ...]) -> dict[str, dict[str, float]]:
    rows = list(rows)
    result: dict[str, dict[str, float]] = {}
    for name in metrics:
        values = [row[name] for row in rows]
        lo, hi = bootstrap_ci(values)
        result[name] = {"mean": fmean(values), "ci95_low": lo, "ci95_high": hi}
    return result
