import torch
from torch import nn

from src.model import SecurityAttackDetectionANN, build_model


def test_model_architecture_and_probabilities():
    model = build_model()

    assert isinstance(model, SecurityAttackDetectionANN)
    assert model.input_dim == 122
    assert model.hidden_dim == 500
    assert model.output_dim == 24
    assert isinstance(model.hidden_activation, nn.Sigmoid)
    assert isinstance(model.output_activation, nn.Softmax)

    dummy_input = torch.randn(5, 122)
    with torch.no_grad():
        output = model(dummy_input)

    assert output.shape == (5, 24)
    assert torch.all(output >= 0)
    assert torch.all(output <= 1)
    assert torch.allclose(output.sum(dim=1), torch.ones(5), atol=1e-6)
