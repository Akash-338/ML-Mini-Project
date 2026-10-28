"""Evaluate a saved ANN on NSL-KDD training and test data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import classification_report, confusion_matrix

from src.model import SecurityAttackDetectionANN, build_model
from src.preprocessing import (
    load_dataset_files,
    load_preprocessing_objects,
    transform_dataset,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "ann_model.pth"
RESULTS_DIR = PROJECT_ROOT / "results"
EVALUATION_PATH = RESULTS_DIR / "evaluation_results.json"
CLASSIFICATION_REPORT_PATH = RESULTS_DIR / "classification_report.csv"
CONFUSION_MATRIX_PATH = RESULTS_DIR / "confusion_matrix.csv"
NUM_CLASSES = 24
PREDICTION_BATCH_SIZE = 8192


def _predicted_classes(model: SecurityAttackDetectionANN, features: np.ndarray) -> np.ndarray:
    if features.ndim != 2 or features.shape[1] != 122:
        raise ValueError(f"Features must have shape (n, 122); received {features.shape}")

    model.eval()
    predictions = []
    with torch.no_grad():
        for start in range(0, features.shape[0], PREDICTION_BATCH_SIZE):
            batch = torch.as_tensor(
                features[start : start + PREDICTION_BATCH_SIZE],
                dtype=torch.float32,
            )
            predictions.append(model(batch).argmax(dim=1).cpu().numpy())
    if not predictions:
        return np.empty(0, dtype=np.int64)
    return np.concatenate(predictions)


def _accuracy_result(expected: np.ndarray, predicted: np.ndarray) -> Dict[str, Any]:
    if expected.shape != predicted.shape:
        raise ValueError(f"Expected and predicted labels must have matching shapes: {expected.shape} != {predicted.shape}")
    correct = int(np.count_nonzero(expected == predicted))
    total = int(expected.size)
    return {
        "correct_predictions": correct,
        "total_predictions": total,
        "accuracy": correct / total if total else 0.0,
    }


def evaluate_predictions(
    train_predictions: np.ndarray,
    train_truth: np.ndarray,
    test_predictions: np.ndarray,
    test_truth: np.ndarray,
    label_mapping: Dict[str, int],
) -> Tuple[Dict[str, Any], pd.DataFrame, pd.DataFrame]:
    """Calculate paper-main accuracy measures and additional diagnostics."""
    for name, values in (
        ("train_predictions", train_predictions),
        ("train_truth", train_truth),
        ("test_predictions", test_predictions),
        ("test_truth", test_truth),
    ):
        if values.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional; received {values.shape}")
        if np.any((values < 0) | (values >= NUM_CLASSES)):
            raise ValueError(f"{name} contains a class outside 0–23.")

    train_multiclass = _accuracy_result(train_truth, train_predictions)
    test_multiclass = _accuracy_result(test_truth, test_predictions)
    train_binary_truth = (train_truth != 0).astype(np.int64)
    train_binary_predictions = (train_predictions != 0).astype(np.int64)
    test_binary_truth = (test_truth != 0).astype(np.int64)
    test_binary_predictions = (test_predictions != 0).astype(np.int64)

    train_binary = _accuracy_result(train_binary_truth, train_binary_predictions)
    test_binary = _accuracy_result(test_binary_truth, test_binary_predictions)

    unknown_mask = test_truth == NUM_CLASSES - 1
    unknown_total = int(np.count_nonzero(unknown_mask))
    unknown_correct = int(np.count_nonzero(test_predictions[unknown_mask] == NUM_CLASSES - 1))
    unknown_diagnostic = {
        "total_samples": unknown_total,
        "correctly_predicted_as_other": unknown_correct,
        "accuracy": unknown_correct / unknown_total if unknown_total else 0.0,
        "note": "Additional diagnostic; not a metric explicitly defined by the paper.",
    }

    class_names = ["normal"] + [
        label for label, class_id in sorted(label_mapping.items(), key=lambda item: item[1])
        if 1 <= class_id <= 22
    ] + ["other/unknown"]
    if len(class_names) != NUM_CLASSES:
        raise ValueError(f"Expected 24 class names from label mapping; found {len(class_names)}.")

    report = classification_report(
        test_truth,
        test_predictions,
        labels=np.arange(NUM_CLASSES),
        target_names=class_names,
        output_dict=True,
        zero_division=0,
    )
    report_df = pd.DataFrame(report).transpose()
    matrix = confusion_matrix(test_truth, test_predictions, labels=np.arange(NUM_CLASSES))
    confusion_df = pd.DataFrame(
        matrix,
        index=class_names,
        columns=class_names,
    )
    confusion_df.index.name = "actual"
    confusion_df.columns.name = "predicted"

    results = {
        "training_multiclass_accuracy": train_multiclass,
        "test_multiclass_accuracy": test_multiclass,
        "training_normal_vs_abnormal_accuracy": train_binary,
        "test_normal_vs_abnormal_accuracy": test_binary,
        "unknown_other_test_diagnostic": unknown_diagnostic,
        "additional_diagnostics": {
            "classification_report": "Precision, recall, F1-score, and support for all 24 classes.",
            "confusion_matrix": "24 x 24 test-set confusion matrix.",
        },
    }
    return results, report_df, confusion_df


def evaluate_model(
    model: SecurityAttackDetectionANN,
    X_train: np.ndarray,
    Y_train: np.ndarray,
    X_test: np.ndarray,
    Y_test: np.ndarray,
    label_mapping: Dict[str, int],
) -> Tuple[Dict[str, Any], pd.DataFrame, pd.DataFrame, np.ndarray, np.ndarray]:
    if Y_train.shape != (X_train.shape[0], NUM_CLASSES):
        raise ValueError(f"Y_train must have shape ({X_train.shape[0]}, 24); received {Y_train.shape}")
    if Y_test.shape != (X_test.shape[0], NUM_CLASSES):
        raise ValueError(f"Y_test must have shape ({X_test.shape[0]}, 24); received {Y_test.shape}")

    train_predictions = _predicted_classes(model, X_train)
    test_predictions = _predicted_classes(model, X_test)
    train_truth = Y_train.argmax(axis=1)
    test_truth = Y_test.argmax(axis=1)
    results, report_df, confusion_df = evaluate_predictions(
        train_predictions,
        train_truth,
        test_predictions,
        test_truth,
        label_mapping,
    )
    return results, report_df, confusion_df, train_predictions, test_predictions


def load_evaluation_data() -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Dict[str, int]]:
    """Load both splits using the persisted training-fitted preprocessing objects."""
    train_df, test_df = load_dataset_files()
    artifacts = load_preprocessing_objects()
    X_train, Y_train = transform_dataset(train_df, artifacts)
    X_test, Y_test = transform_dataset(test_df, artifacts)
    return X_train, X_test, Y_train, Y_test, artifacts["label_mapping"]


def run_evaluation() -> Dict[str, Any]:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Trained model not found: {MODEL_PATH}")

    X_train, X_test, Y_train, Y_test, label_mapping = load_evaluation_data()
    model = build_model()
    model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu", weights_only=True))

    results, report_df, confusion_df, _, _ = evaluate_model(
        model,
        X_train,
        Y_train,
        X_test,
        Y_test,
        label_mapping,
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with EVALUATION_PATH.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    report_df.to_csv(CLASSIFICATION_REPORT_PATH, index_label="class")
    confusion_df.to_csv(CONFUSION_MATRIX_PATH)

    print(f"TRAINING MULTICLASS ACCURACY: {results['training_multiclass_accuracy']['accuracy']:.6f}")
    print(f"TEST MULTICLASS ACCURACY: {results['test_multiclass_accuracy']['accuracy']:.6f}")
    print(
        "TRAINING NORMAL-vs-ABNORMAL ACCURACY: "
        f"{results['training_normal_vs_abnormal_accuracy']['accuracy']:.6f}"
    )
    print(
        "TEST NORMAL-vs-ABNORMAL ACCURACY: "
        f"{results['test_normal_vs_abnormal_accuracy']['accuracy']:.6f}"
    )
    unknown = results["unknown_other_test_diagnostic"]
    print(f"UNKNOWN/OTHER TEST SAMPLES: {unknown['total_samples']}")
    print(f"UNKNOWN/OTHER CORRECTLY DETECTED: {unknown['correctly_predicted_as_other']}")
    print("Per-class report and confusion matrix are additional diagnostics beyond the paper's two main accuracies.")
    print(f"Saved evaluation results to: {EVALUATION_PATH}")
    print(f"Saved classification report to: {CLASSIFICATION_REPORT_PATH}")
    print(f"Saved confusion matrix to: {CONFUSION_MATRIX_PATH}")
    return results


if __name__ == "__main__":
    run_evaluation()
