"""Training procedure for the paper's 122 -> 500 -> 24 ANN."""

from __future__ import annotations

import random
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import torch

from src.model import SecurityAttackDetectionANN, build_model
from src.preprocessing import MODEL_PATH as PREPROCESSING_OBJECTS_PATH
from src.preprocessing import preprocess_data


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "ann_model.pth"
HISTORY_PATH = PROJECT_ROOT / "results" / "training_history.csv"
LEARNING_RATE = 0.5
BATCH_SIZE = 1000
EPOCHS = 10


def _set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def _mean_log_likelihood(
    model: SecurityAttackDetectionANN,
    features: torch.Tensor,
    labels: torch.Tensor,
) -> torch.Tensor:
    probabilities = model(features)
    log_probabilities = torch.log(probabilities.clamp_min(torch.finfo(probabilities.dtype).tiny))
    return (labels * log_probabilities).sum(dim=1).mean()


def train_model(
    X_train: np.ndarray,
    Y_train: np.ndarray,
    *,
    seed: int = 42,
    model_path: Path = MODEL_PATH,
    history_path: Path = HISTORY_PATH,
) -> Tuple[SecurityAttackDetectionANN, pd.DataFrame]:
    """Train for the paper's fixed 10 epochs using mini-batch gradient ascent.

    The paper does not specify the regularization method or coefficient, so
    this implementation performs unregularized ascent rather than inventing
    either value. Training records are consumed in their existing order;
    shuffling is not described in the paper.
    """
    if X_train.ndim != 2 or X_train.shape[1] != 122:
        raise ValueError(f"X_train must have shape (n, 122); received {X_train.shape}")
    if Y_train.ndim != 2 or Y_train.shape != (X_train.shape[0], 24):
        raise ValueError(f"Y_train must have shape ({X_train.shape[0]}, 24); received {Y_train.shape}")
    if X_train.shape[0] == 0:
        raise ValueError("Training data must contain at least one sample.")

    _set_seed(seed)
    model = build_model()
    features = torch.as_tensor(X_train, dtype=torch.float32)
    labels = torch.as_tensor(Y_train, dtype=torch.float32)
    history: List[Dict[str, float]] = []

    for epoch in range(1, EPOCHS + 1):
        model.train()
        for start in range(0, features.shape[0], BATCH_SIZE):
            batch_features = features[start : start + BATCH_SIZE]
            batch_labels = labels[start : start + BATCH_SIZE]

            model.zero_grad(set_to_none=True)
            objective = _mean_log_likelihood(model, batch_features, batch_labels)
            objective.backward()
            with torch.no_grad():
                for parameter in model.parameters():
                    parameter.add_(parameter.grad, alpha=LEARNING_RATE)

        model.eval()
        with torch.no_grad():
            objective = _mean_log_likelihood(model, features, labels).item()
            predictions = model(features).argmax(dim=1)
            expected = labels.argmax(dim=1)
            accuracy = (predictions == expected).float().mean().item()

        history.append(
            {
                "epoch": epoch,
                "training_objective": objective,
                "training_accuracy": accuracy,
            }
        )

    history_df = pd.DataFrame(history)
    model_path = Path(model_path)
    history_path = Path(history_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), model_path)
    history_df.to_csv(history_path, index=False)
    return model, history_df


def run_training(seed: int = 42) -> Tuple[SecurityAttackDetectionANN, pd.DataFrame]:
    """Load paper-preprocessed data and train the ANN without test evaluation."""
    X_train, _, Y_train, _, _, _ = preprocess_data()
    if not PREPROCESSING_OBJECTS_PATH.exists():
        raise FileNotFoundError(
            "The preprocessing pipeline did not save its fitted encoder and scaler at "
            f"{PREPROCESSING_OBJECTS_PATH}"
        )

    model, history = train_model(X_train, Y_train, seed=seed)
    last_epoch = history.iloc[-1]
    print(f"Training objective after {EPOCHS} epochs: {last_epoch['training_objective']:.6f}")
    print(f"Training accuracy after {EPOCHS} epochs: {last_epoch['training_accuracy']:.6f}")
    print(f"Saved model to: {MODEL_PATH}")
    print(f"Saved preprocessing objects to: {PREPROCESSING_OBJECTS_PATH}")
    print(f"Saved training history to: {HISTORY_PATH}")
    return model, history


if __name__ == "__main__":
    run_training()
