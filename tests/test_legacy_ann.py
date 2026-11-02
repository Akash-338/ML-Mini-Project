import numpy as np
import pytest

torch = pytest.importorskip('torch')
from legacy_ann.src.model import build_model
from legacy_ann.src.train_proposed import calculate_class_weights


def test_historical_ann_output_shape_and_probabilities():
    model = build_model()
    with torch.no_grad():
        output = model(torch.zeros(2, 122))
    assert output.shape == (2, 24)
    assert torch.allclose(output.sum(dim=1), torch.ones(2), atol=1e-6)


def test_historical_class_weights_exclude_absent_unknown_class():
    counts, weights = calculate_class_weights(np.array([0, 0, 1]))
    assert counts[23] == 0
    assert weights[23] == 0
    assert weights[1] > weights[0]
