import hashlib
from pathlib import Path

import numpy as np
import torch
from sklearn.preprocessing import OneHotEncoder, StandardScaler

import src.evaluate as baseline_evaluation
import src.preprocessing as preprocessing
import src.train_proposed as proposed_training
from src.evaluate_proposed import (
    CLASSIFICATION_REPORT_PATH as PROPOSED_REPORT_PATH,
    CONFUSION_MATRIX_PATH as PROPOSED_CONFUSION_PATH,
    EVALUATION_PATH as PROPOSED_EVALUATION_PATH,
)
from src.model import build_model
from src.train_proposed import (
    CLASS_WEIGHTS_PATH,
    HISTORY_PATH,
    MODEL_PATH,
    PREPROCESSING_PATH,
    calculate_class_weights,
    load_proposed_training_data,
    train_proposed_model,
)


def test_class_weights_are_finite_and_absent_class_is_zero():
    class_ids = np.array([0, 0, 1, 1, 1, 2], dtype=np.int64)
    counts, weights = calculate_class_weights(class_ids)

    assert counts.shape == (24,)
    assert weights.shape == (24,)
    assert np.all(np.isfinite(weights))
    assert weights[23] == 0.0
    assert counts[23] == 0
    assert np.isclose(np.dot(counts, weights) / len(class_ids), 1.0)


def test_proposed_training_is_separate_and_uses_expected_history(tmp_path):
    rng = np.random.default_rng(41)
    X_train = rng.normal(size=(12, 122)).astype(np.float32)
    class_ids = np.array([0, 0, 0, 1, 1, 2, 2, 2, 2, 3, 3, 3])
    Y_train = np.eye(24, dtype=np.float32)[class_ids]
    _, weights = calculate_class_weights(class_ids)
    model_path = tmp_path / "proposed_ann_model.pth"
    history_path = tmp_path / "proposed_training_history.csv"

    model, history = train_proposed_model(
        X_train,
        Y_train,
        weights,
        seed=19,
        model_path=model_path,
        history_path=history_path,
    )

    assert model.input_dim == 122
    assert model.hidden_dim == 500
    assert model.output_dim == 24
    assert list(history.columns) == ["epoch", "objective", "loss", "accuracy"]
    assert len(history) == 10
    assert model_path.is_file()
    assert history_path.is_file()
    with torch.no_grad():
        probabilities = model(torch.as_tensor(X_train[:3], dtype=torch.float32))
    assert probabilities.shape == (3, 24)
    assert torch.allclose(probabilities.sum(dim=1), torch.ones(3), atol=1e-6)


def test_proposed_data_uses_saved_artifact_without_fitting_or_mutating_baseline(monkeypatch):
    artifact_path = preprocessing.MODEL_PATH
    baseline_model_path = baseline_evaluation.MODEL_PATH
    artifact_hash = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    baseline_model_hash = hashlib.sha256(baseline_model_path.read_bytes()).hexdigest()
    train_df, _ = preprocessing.load_dataset_files()
    monkeypatch.setattr(
        proposed_training,
        "load_dataset_files",
        lambda: (train_df.iloc[[0]].copy(), train_df.iloc[0:0].copy()),
    )

    def reject_fit(*args, **kwargs):
        raise AssertionError("Proposed training must not fit saved preprocessing objects.")

    monkeypatch.setattr(OneHotEncoder, "fit", reject_fit)
    monkeypatch.setattr(StandardScaler, "fit", reject_fit)
    X_train, Y_train, artifacts = load_proposed_training_data()

    assert X_train.shape == (1, 122)
    assert Y_train.shape == (1, 24)
    assert artifacts["output_classes"] == 24
    assert hashlib.sha256(artifact_path.read_bytes()).hexdigest() == artifact_hash
    assert hashlib.sha256(baseline_model_path.read_bytes()).hexdigest() == baseline_model_hash


def test_proposed_output_paths_are_separate_from_frozen_baseline():
    baseline_paths = {
        baseline_evaluation.MODEL_PATH.resolve(),
        preprocessing.MODEL_PATH.resolve(),
        baseline_evaluation.EVALUATION_PATH.resolve(),
        baseline_evaluation.CLASSIFICATION_REPORT_PATH.resolve(),
        baseline_evaluation.CONFUSION_MATRIX_PATH.resolve(),
    }
    proposed_output_paths = {
        Path(MODEL_PATH).resolve(),
        Path(HISTORY_PATH).resolve(),
        Path(CLASS_WEIGHTS_PATH).resolve(),
        Path(PROPOSED_EVALUATION_PATH).resolve(),
        Path(PROPOSED_REPORT_PATH).resolve(),
        Path(PROPOSED_CONFUSION_PATH).resolve(),
    }
    assert Path(PREPROCESSING_PATH).resolve() not in proposed_output_paths
    assert proposed_output_paths.isdisjoint(baseline_paths)
