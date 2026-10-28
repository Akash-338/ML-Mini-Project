"""Train a separate class-weighted ANN using the frozen baseline pipeline."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import torch

from src.model import SecurityAttackDetectionANN, build_model
from src.preprocessing import (
    load_dataset_files,
    load_preprocessing_objects,
    transform_dataset,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PREPROCESSING_PATH = PROJECT_ROOT / "models" / "preprocessing_artifacts.pkl"
MODEL_PATH = PROJECT_ROOT / "models" / "proposed_ann_model.pth"
HISTORY_PATH = PROJECT_ROOT / "results" / "proposed_training_history.csv"
CLASS_WEIGHTS_PATH = PROJECT_ROOT / "results" / "class_weights.csv"
LEARNING_RATE = 0.5
BATCH_SIZE = 1000
EPOCHS = 10
SEED = 42
NUM_CLASSES = 24


def _set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def calculate_class_weights(labels: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Calculate N / (K_positive * count) weights, leaving absent classes at zero."""
    if labels.ndim == 2:
        if labels.shape[1] != NUM_CLASSES:
            raise ValueError(f"Labels must have 24 columns; received {labels.shape}.")
        if not np.all(np.isfinite(labels)) or not np.allclose(labels.sum(axis=1), 1.0):
            raise ValueError("One-hot labels must be finite and sum to one for every sample.")
        class_ids = labels.argmax(axis=1)
    elif labels.ndim == 1:
        class_ids = labels.astype(np.int64, copy=False)
    else:
        raise ValueError(f"Labels must be one- or two-dimensional; received {labels.shape}.")

    if class_ids.size == 0:
        raise ValueError("Cannot calculate class weights for an empty label array.")
    if np.any((class_ids < 0) | (class_ids >= NUM_CLASSES)):
        raise ValueError("Labels contain a class outside 0–23.")

    counts = np.bincount(class_ids, minlength=NUM_CLASSES).astype(np.int64)
    positive_classes = int(np.count_nonzero(counts))
    weights = np.zeros(NUM_CLASSES, dtype=np.float64)
    positive_mask = counts > 0
    weights[positive_mask] = class_ids.size / (positive_classes * counts[positive_mask])
    if not np.all(np.isfinite(weights)):
        raise ValueError("Calculated class weights contain non-finite values.")
    return counts, weights


def _weighted_mean_log_likelihood(
    model: SecurityAttackDetectionANN,
    features: torch.Tensor,
    labels: torch.Tensor,
    class_weights: torch.Tensor,
) -> torch.Tensor:
    probabilities = model(features)
    log_probabilities = torch.log(probabilities.clamp_min(torch.finfo(probabilities.dtype).tiny))
    sample_log_likelihood = (labels * log_probabilities).sum(dim=1)
    sample_weights = class_weights[labels.argmax(dim=1)]
    return (sample_weights * sample_log_likelihood).mean()


def _write_class_weights(
    counts: np.ndarray,
    weights: np.ndarray,
    label_mapping: Dict[str, int],
    output_path: Path = CLASS_WEIGHTS_PATH,
) -> None:
    names_by_id = {class_id: name for name, class_id in label_mapping.items()}
    names_by_id[23] = "other/unknown"
    if set(names_by_id) != set(range(NUM_CLASSES)):
        raise ValueError("Saved label mapping must name all 24 classes.")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "class_id": class_id,
                "class_name": names_by_id[class_id],
                "sample_count": int(counts[class_id]),
                "class_weight": float(weights[class_id]),
            }
            for class_id in range(NUM_CLASSES)
        ]
    ).to_csv(output_path, index=False)


def load_proposed_training_data() -> tuple[np.ndarray, np.ndarray, Dict[str, object]]:
    """Transform only training rows with the persisted baseline preprocessing."""
    train_df, _ = load_dataset_files()
    artifacts = load_preprocessing_objects(PREPROCESSING_PATH)
    X_train, Y_train = transform_dataset(train_df, artifacts)
    return X_train, Y_train, artifacts


def train_proposed_model(
    X_train: np.ndarray,
    Y_train: np.ndarray,
    class_weights: np.ndarray,
    *,
    seed: int = SEED,
    model_path: Path = MODEL_PATH,
    history_path: Path = HISTORY_PATH,
) -> tuple[SecurityAttackDetectionANN, pd.DataFrame]:
    if X_train.ndim != 2 or X_train.shape[1] != 122:
        raise ValueError(f"X_train must have shape (n, 122); received {X_train.shape}")
    if Y_train.shape != (X_train.shape[0], NUM_CLASSES):
        raise ValueError(f"Y_train must have shape ({X_train.shape[0]}, 24); received {Y_train.shape}")
    if X_train.shape[0] == 0:
        raise ValueError("Training data must contain at least one sample.")
    if class_weights.shape != (NUM_CLASSES,) or not np.all(np.isfinite(class_weights)):
        raise ValueError("class_weights must contain 24 finite values.")
    if np.any(class_weights < 0):
        raise ValueError("class_weights cannot be negative.")

    _set_seed(seed)
    model = build_model()
    features = torch.as_tensor(X_train, dtype=torch.float32)
    labels = torch.as_tensor(Y_train, dtype=torch.float32)
    weights = torch.as_tensor(class_weights, dtype=torch.float32)
    history: List[Dict[str, float]] = []

    for epoch in range(1, EPOCHS + 1):
        model.train()
        for start in range(0, features.shape[0], BATCH_SIZE):
            batch_features = features[start : start + BATCH_SIZE]
            batch_labels = labels[start : start + BATCH_SIZE]

            model.zero_grad(set_to_none=True)
            objective = _weighted_mean_log_likelihood(model, batch_features, batch_labels, weights)
            if not torch.isfinite(objective):
                raise FloatingPointError(f"Non-finite weighted training objective at epoch {epoch}.")
            objective.backward()
            with torch.no_grad():
                for parameter in model.parameters():
                    parameter.add_(parameter.grad, alpha=LEARNING_RATE)

        model.eval()
        with torch.no_grad():
            objective = _weighted_mean_log_likelihood(model, features, labels, weights).item()
            predictions = model(features).argmax(dim=1)
            expected = labels.argmax(dim=1)
            accuracy = (predictions == expected).float().mean().item()
        if not np.isfinite(objective) or not np.isfinite(accuracy):
            raise FloatingPointError(f"Non-finite training metric at epoch {epoch}.")
        history.append(
            {
                "epoch": epoch,
                "objective": objective,
                "loss": -objective,
                "accuracy": accuracy,
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


def run_training() -> tuple[SecurityAttackDetectionANN, pd.DataFrame]:
    """Load saved preprocessing objects and train only the proposed model."""
    X_train, Y_train, artifacts = load_proposed_training_data()
    counts, weights = calculate_class_weights(Y_train)
    _write_class_weights(counts, weights, artifacts["label_mapping"])

    model, history = train_proposed_model(X_train, Y_train, weights)
    print(f"Training objective after {EPOCHS} epochs: {history.iloc[-1]['objective']:.6f}")
    print(f"Training accuracy after {EPOCHS} epochs: {history.iloc[-1]['accuracy']:.6f}")
    print(f"Saved proposed model to: {MODEL_PATH}")
    print(f"Saved proposed training history to: {HISTORY_PATH}")
    print(f"Saved class weights to: {CLASS_WEIGHTS_PATH}")
    return model, history


if __name__ == "__main__":
    run_training()
