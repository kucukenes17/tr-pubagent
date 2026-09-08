"""Dependency-light class-weight calculations for risk training."""

from collections import Counter


def balanced_class_weights(label_ids: list[int], class_count: int) -> list[float]:
    if class_count < 1 or not label_ids:
        raise ValueError("Training labels and at least one class are required")
    counts = Counter(label_ids)
    missing = set(range(class_count)) - counts.keys()
    if missing:
        raise ValueError(f"Training split has no examples for classes: {sorted(missing)}")
    total = len(label_ids)
    return [total / (class_count * counts[index]) for index in range(class_count)]
