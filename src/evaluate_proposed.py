"""Evaluate only the proposed class-weighted ANN experiment."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import classification_report, confusion_matrix

from src.model import build_model
from src.preprocessing import (
    load_dataset_files,
    load_preprocessing_objects,
    transform_dataset,
)
from src.train_proposed import NUM_CLASSES, PREPROCESSING_PATH, PROJECT_ROOT


MODEL_PATH = PROJECT_ROOT / "models" / "proposed_ann_model.pth"
RESULTS_DIR = PROJECT_ROOT / "results"
EVALUATION_PATH = RESULTS_DIR / "proposed_evaluation_results.json"
CLASSIFICATION_REPORT_PATH = RESULTS_DIR / "proposed_classification_report.csv"
CONFUSION_MATRIX_PATH = RESULTS_DIR / "proposed_confusion_matrix.csv"
PREDICTION_BATCH_SIZE = 8192


def _predict(model: torch.nn.Module, features: np.ndarray) -> np.ndarray:
    if features.ndim != 2 or features.shape[1] != 122:
        raise ValueError(f"Features must have shape (n, 122); received {features.shape}")
    model.eval()
    predictions: list[np.ndarray] = []
    with torch.no_grad():
        for start in range(0, features.shape[0], PREDICTION_BATCH_SIZE):
            batch = torch.as_tensor(
                features[start : start + PREDICTION_BATCH_SIZE],
                dtype=torch.float32,
            )
            predictions.append(model(batch).argmax(dim=1).cpu().numpy())
    return np.concatenate(predictions) if predictions else np.empty(0, dtype=np.int64)


def _accuracy(expected: np.ndarray, predicted: np.ndarray) -> dict[str, int | float]:
    if expected.shape != predicted.shape:
        raise ValueError(f"Expected matching label shapes; got {expected.shape} and {predicted.shape}.")
    return {
        "correct_predictions": int(np.count_nonzero(expected == predicted)),
        "total_predictions": int(expected.size),
        "accuracy": float(np.mean(expected == predicted)) if expected.size else 0.0,
    }


def _multiclass_metrics(
    truth: np.ndarray,
    predicted: np.ndarray,
    class_names: list[str],
) -> tuple[dict[str, Any], pd.DataFrame]:
    if truth.ndim != 1 or predicted.ndim != 1:
        raise ValueError("Truth and predicted classes must be one-dimensional.")
    report = classification_report(
        truth,
        predicted,
        labels=np.arange(NUM_CLASSES),
        target_names=class_names,
        output_dict=True,
        zero_division=0,
    )
    report_df = pd.DataFrame(report).transpose()
    summary = {
        "accuracy": _accuracy(truth, predicted)["accuracy"],
        "macro_precision": float(report["macro avg"]["precision"]),
        "macro_recall": float(report["macro avg"]["recall"]),
        "macro_f1": float(report["macro avg"]["f1-score"]),
        "weighted_precision": float(report["weighted avg"]["precision"]),
        "weighted_recall": float(report["weighted avg"]["recall"]),
        "weighted_f1": float(report["weighted avg"]["f1-score"]),
        "per_class": {
            name: {
                "precision": float(report[name]["precision"]),
                "recall": float(report[name]["recall"]),
                "f1": float(report[name]["f1-score"]),
                "support": int(report[name]["support"]),
            }
            for name in class_names
        },
    }
    return summary, report_df


def evaluate_proposed(
    model: torch.nn.Module,
    X_train: np.ndarray,
    Y_train: np.ndarray,
    X_test: np.ndarray,
    Y_test: np.ndarray,
    label_mapping: dict[str, int],
) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    if Y_train.shape != (X_train.shape[0], NUM_CLASSES):
        raise ValueError(f"Y_train must have shape ({X_train.shape[0]}, 24); received {Y_train.shape}")
    if Y_test.shape != (X_test.shape[0], NUM_CLASSES):
        raise ValueError(f"Y_test must have shape ({X_test.shape[0]}, 24); received {Y_test.shape}")

    names_by_id = {int(class_id): name for name, class_id in label_mapping.items()}
    names_by_id[23] = "other/unknown"
    if set(names_by_id) != set(range(NUM_CLASSES)):
        raise ValueError("Saved label mapping must name all 24 classes.")
    class_names = [names_by_id[class_id] for class_id in range(NUM_CLASSES)]

    train_predictions = _predict(model, X_train)
    test_predictions = _predict(model, X_test)
    train_truth = Y_train.argmax(axis=1)
    test_truth = Y_test.argmax(axis=1)
    train_metrics, train_report = _multiclass_metrics(train_truth, train_predictions, class_names)
    test_metrics, test_report = _multiclass_metrics(test_truth, test_predictions, class_names)

    train_binary = _accuracy((train_truth != 0).astype(np.int64), (train_predictions != 0).astype(np.int64))
    test_binary = _accuracy((test_truth != 0).astype(np.int64), (test_predictions != 0).astype(np.int64))
    unknown_mask = test_truth == 23
    unknown_total = int(np.count_nonzero(unknown_mask))
    unknown_correct = int(np.count_nonzero(test_predictions[unknown_mask] == 23))

    report_df = pd.concat(
        {
            "training": train_report,
            "test": test_report,
        },
        names=["split", "class"],
    ).reset_index()
    matrix = confusion_matrix(test_truth, test_predictions, labels=np.arange(NUM_CLASSES))
    confusion_df = pd.DataFrame(matrix, index=class_names, columns=class_names)
    confusion_df.index.name = "actual"
    confusion_df.columns.name = "predicted"

    results = {
        "training_multiclass": train_metrics,
        "test_multiclass": test_metrics,
        "training_normal_vs_abnormal": train_binary,
        "test_normal_vs_abnormal": test_binary,
        "unknown_other_test_diagnostic": {
            "total_samples": unknown_total,
            "correctly_predicted_as_other": unknown_correct,
            "note": "Diagnostic for test labels mapped to class 23; it does not establish unknown-attack detection.",
        },
        "additional_diagnostics": {
            "classification_report": "Precision, recall, F1-score, and support for all 24 classes on train and test.",
            "confusion_matrix": "24 x 24 test-set confusion matrix.",
        },
    }
    return results, report_df, confusion_df


def run_evaluation() -> dict[str, Any]:
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(f"Proposed trained model not found: {MODEL_PATH}")
    train_df, test_df = load_dataset_files()
    artifacts = load_preprocessing_objects(PREPROCESSING_PATH)
    X_train, Y_train = transform_dataset(train_df, artifacts)
    X_test, Y_test = transform_dataset(test_df, artifacts)

    model = build_model()
    model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu", weights_only=True))
    results, report_df, confusion_df = evaluate_proposed(
        model,
        X_train,
        Y_train,
        X_test,
        Y_test,
        artifacts["label_mapping"],
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    EVALUATION_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
    report_df.to_csv(CLASSIFICATION_REPORT_PATH, index=False)
    confusion_df.to_csv(CONFUSION_MATRIX_PATH)
    for split in ("training_multiclass", "test_multiclass"):
        print(
            f"{split.upper()} ACCURACY: {results[split]['accuracy']:.6f}; "
            f"macro F1: {results[split]['macro_f1']:.6f}; "
            f"weighted F1: {results[split]['weighted_f1']:.6f}"
        )
    print(f"UNKNOWN/OTHER TEST SAMPLES: {results['unknown_other_test_diagnostic']['total_samples']}")
    print(f"Saved proposed evaluation results to: {EVALUATION_PATH}")
    return results


if __name__ == "__main__":
    run_evaluation()
