"""Create plots from the saved experiment results without retraining."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_ROOT / "results"
TRAINING_HISTORY_PATH = RESULTS_DIR / "training_history.csv"
EVALUATION_RESULTS_PATH = RESULTS_DIR / "evaluation_results.json"
CLASSIFICATION_REPORT_PATH = RESULTS_DIR / "classification_report.csv"
CONFUSION_MATRIX_PATH = RESULTS_DIR / "confusion_matrix.csv"


def _require_file(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Required saved result file not found: {path}")


def generate_visualizations() -> list[Path]:
    """Load saved experiment artifacts and generate the five requested plots."""
    for path in (
        TRAINING_HISTORY_PATH,
        EVALUATION_RESULTS_PATH,
        CLASSIFICATION_REPORT_PATH,
        CONFUSION_MATRIX_PATH,
    ):
        _require_file(path)

    history = pd.read_csv(TRAINING_HISTORY_PATH)
    with EVALUATION_RESULTS_PATH.open("r", encoding="utf-8") as result_file:
        evaluation = json.load(result_file)
    report = pd.read_csv(CLASSIFICATION_REPORT_PATH, index_col="class")
    confusion = pd.read_csv(CONFUSION_MATRIX_PATH, index_col="actual")
    class_names = confusion.columns.tolist()

    if len(class_names) != 24 or confusion.shape != (24, 24):
        raise ValueError(f"Expected a 24 x 24 confusion matrix; received {confusion.shape}.")
    if "training_objective" not in history or "training_accuracy" not in history:
        raise ValueError("Training history must contain training_objective and training_accuracy columns.")
    if not all(name in report.index for name in class_names):
        raise ValueError("Classification report is missing one or more confusion-matrix classes.")

    outputs = [
        RESULTS_DIR / "training_loss.png",
        RESULTS_DIR / "training_accuracy.png",
        RESULTS_DIR / "confusion_matrix.png",
        RESULTS_DIR / "per_class_f1.png",
        RESULTS_DIR / "accuracy_comparison.png",
    ]

    epochs = history["epoch"]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(epochs, history["training_objective"], marker="o")
    ax.set(title="Training objective (mean log-likelihood) vs epoch", xlabel="Epoch", ylabel="Mean log-likelihood")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(outputs[0], dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(epochs, history["training_accuracy"] * 100, marker="o")
    ax.set(title="Training accuracy vs epoch", xlabel="Epoch", ylabel="Accuracy (%)")
    ax.set_ylim(0, 100)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(outputs[1], dpi=180)
    plt.close(fig)

    matrix = confusion.to_numpy(dtype=np.int64)
    fig, ax = plt.subplots(figsize=(14, 12))
    image = ax.imshow(matrix, interpolation="nearest", cmap="Blues")
    fig.colorbar(image, ax=ax, label="Number of samples")
    ax.set(
        title="Test confusion matrix (counts)",
        xlabel="Predicted class",
        ylabel="Actual class",
    )
    ticks = np.arange(len(class_names))
    ax.set_xticks(ticks, labels=class_names, rotation=65, ha="right", fontsize=7)
    ax.set_yticks(ticks, labels=class_names, fontsize=7)
    fig.tight_layout()
    fig.savefig(outputs[2], dpi=200)
    plt.close(fig)

    f1 = report.loc[class_names, "f1-score"].astype(float)
    fig, ax = plt.subplots(figsize=(13, 6))
    ax.bar(class_names, f1)
    ax.set(title="Per-class F1-score (additional diagnostic)", xlabel="Class", ylabel="F1-score")
    ax.set_ylim(0, 1.05)
    ax.tick_params(axis="x", labelrotation=65, labelsize=8)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(outputs[3], dpi=180)
    plt.close(fig)

    metric_keys = (
        ("Training\nmulticlass", "training_multiclass_accuracy"),
        ("Test\nmulticlass", "test_multiclass_accuracy"),
        ("Training\nnormal vs abnormal", "training_normal_vs_abnormal_accuracy"),
        ("Test\nnormal vs abnormal", "test_normal_vs_abnormal_accuracy"),
    )
    values = [float(evaluation[key]["accuracy"]) * 100 for _, key in metric_keys]
    labels = [label for label, _ in metric_keys]
    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(labels, values, color=["#4472C4", "#ED7D31", "#70AD47", "#A5A5A5"])
    ax.set(title="Main accuracy results", ylabel="Accuracy (%)")
    ax.set_ylim(0, 100)
    ax.bar_label(bars, fmt="%.2f%%", padding=3)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(outputs[4], dpi=180)
    plt.close(fig)

    return outputs


if __name__ == "__main__":
    for output in generate_visualizations():
        print(f"Generated: {output}")
