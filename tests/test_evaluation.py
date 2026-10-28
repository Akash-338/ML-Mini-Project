import numpy as np
import pandas as pd
import pytest
from sklearn.preprocessing import OneHotEncoder, StandardScaler

import src.evaluate as evaluation
import src.preprocessing as preprocessing
from src.evaluate import evaluate_model
from src.model import build_model
from src.preprocessing import (
    CATEGORICAL_COLUMNS,
    FEATURE_COLUMNS,
    NSL_KDD_COLUMNS,
    NUMERICAL_COLUMNS,
    _save_preprocessing_objects,
)


def test_evaluation_shapes_and_metrics():
    rng = np.random.default_rng(29)
    X_train = rng.normal(size=(8, 122)).astype(np.float32)
    X_test = rng.normal(size=(5, 122)).astype(np.float32)
    Y_train = np.eye(24, dtype=np.float32)[np.arange(8)]
    Y_test = np.eye(24, dtype=np.float32)[np.array([0, 1, 2, 22, 23])]
    label_mapping = {
        "normal": 0,
        **{f"attack_{index}": index for index in range(1, 23)},
        "other": 23,
    }

    results, report, confusion, train_predictions, test_predictions = evaluate_model(
        build_model(),
        X_train,
        Y_train,
        X_test,
        Y_test,
        label_mapping,
    )

    assert train_predictions.shape == (len(X_train),)
    assert test_predictions.shape == (len(X_test),)
    assert np.all((train_predictions >= 0) & (train_predictions <= 23))
    assert np.all((test_predictions >= 0) & (test_predictions <= 23))
    assert 0 <= results["training_multiclass_accuracy"]["accuracy"] <= 1
    assert 0 <= results["test_multiclass_accuracy"]["accuracy"] <= 1
    assert 0 <= results["training_normal_vs_abnormal_accuracy"]["accuracy"] <= 1
    assert 0 <= results["test_normal_vs_abnormal_accuracy"]["accuracy"] <= 1
    assert confusion.shape == (24, 24)
    assert len(report) == 24 + 3
    assert "other/unknown" in report.index


def test_evaluation_uses_persisted_preprocessing_without_refitting(tmp_path, monkeypatch):
    service_categories = [f"service_{index}" for index in range(70)]
    protocol_categories = ["icmp", "tcp", "udp"]
    flag_categories = [f"flag_{index}" for index in range(11)]
    train_rows = []
    for index, service in enumerate(service_categories):
        row = {column: float(index + column_index) for column_index, column in enumerate(NUMERICAL_COLUMNS)}
        row.update(
            {
                "protocol_type": protocol_categories[index % len(protocol_categories)],
                "service": service,
                "flag": flag_categories[index % len(flag_categories)],
                "label": "normal",
                "difficulty": 1,
            }
        )
        train_rows.append(row)
    train_df = pd.DataFrame(train_rows, columns=NSL_KDD_COLUMNS)
    test_row = train_rows[-1].copy()
    test_row["label"] = "unseen_test_attack"
    test_df = pd.DataFrame([test_row], columns=NSL_KDD_COLUMNS)

    encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    encoder.fit(train_df[CATEGORICAL_COLUMNS].astype(str))
    scaler = StandardScaler()
    scaler.fit(train_df[NUMERICAL_COLUMNS].astype(np.float64))
    label_mapping = {
        "normal": 0,
        **{f"attack_{index}": index for index in range(1, 23)},
        "other": 23,
    }
    artifacts = {
        "categorical_encoder": encoder,
        "numeric_scaler": scaler,
        "feature_columns": FEATURE_COLUMNS,
        "categorical_columns": CATEGORICAL_COLUMNS,
        "numerical_columns": NUMERICAL_COLUMNS,
        "known_attack_labels": [f"attack_{index}" for index in range(1, 23)],
        "label_mapping": label_mapping,
        "output_classes": 24,
    }
    artifact_path = tmp_path / "preprocessing_artifacts.pkl"
    _save_preprocessing_objects(artifacts, artifact_path)
    monkeypatch.setattr(preprocessing, "MODEL_PATH", artifact_path)
    monkeypatch.setattr(evaluation, "load_dataset_files", lambda: (train_df, test_df))

    def reject_fit(*args, **kwargs):
        raise AssertionError("Evaluation must not fit preprocessing objects.")

    monkeypatch.setattr(OneHotEncoder, "fit", reject_fit)
    monkeypatch.setattr(StandardScaler, "fit", reject_fit)

    X_train, X_test, Y_train, Y_test, loaded_mapping = evaluation.load_evaluation_data()

    assert X_train.shape == (70, 122)
    assert X_test.shape == (1, 122)
    assert Y_train.shape == (70, 24)
    assert Y_test.shape == (1, 24)
    assert Y_test[0, 23] == 1
    assert loaded_mapping == label_mapping
    assert np.allclose(X_test[0], X_train[-1])
