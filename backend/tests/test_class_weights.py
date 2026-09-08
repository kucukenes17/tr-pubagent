import pytest

from ml.class_weights import balanced_class_weights


def test_balanced_weights_are_inverse_frequency():
    weights = balanced_class_weights([0, 0, 0, 1], 2)
    assert weights == pytest.approx([4 / 6, 2.0])
    weighted_mass = [weights[0] * 3, weights[1] * 1]
    assert weighted_mass[0] == pytest.approx(weighted_mass[1])


@pytest.mark.parametrize("labels,count", [([], 2), ([0], 0), ([0, 0], 2)])
def test_balanced_weights_reject_incomplete_training_labels(labels, count):
    with pytest.raises(ValueError):
        balanced_class_weights(labels, count)
