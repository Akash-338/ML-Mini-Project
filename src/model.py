"""The paper's 122 -> 500 -> 24 feedforward neural network."""

from __future__ import annotations

import torch
from torch import nn


class SecurityAttackDetectionANN(nn.Module):
    """Single-hidden-layer ANN for the paper's 24-class task."""

    input_dim = 122
    hidden_dim = 500
    output_dim = 24

    def __init__(self) -> None:
        super().__init__()
        # The paper does not specify initialization; nn.Linear uses PyTorch defaults.
        self.hidden_layer = nn.Linear(self.input_dim, self.hidden_dim)
        self.hidden_activation = nn.Sigmoid()
        self.output_layer = nn.Linear(self.hidden_dim, self.output_dim)
        self.output_activation = nn.Softmax(dim=1)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        hidden = self.hidden_activation(self.hidden_layer(inputs))
        return self.output_activation(self.output_layer(hidden))


def build_model() -> SecurityAttackDetectionANN:
    """Create an untrained model instance."""
    return SecurityAttackDetectionANN()


if __name__ == "__main__":
    model = build_model()
    print(model)
    print(f"Trainable parameters: {sum(p.numel() for p in model.parameters() if p.requires_grad):,}")
