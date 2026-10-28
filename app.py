"""Local web demo for the saved NSL-KDD attack-detection ANN."""

from __future__ import annotations

import logging
import math
import pickle
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from src.model import SecurityAttackDetectionANN, build_model
from src.preprocessing import (
    CATEGORICAL_COLUMNS,
    DATA_DIR,
    FEATURE_COLUMNS,
    NSL_KDD_COLUMNS,
    load_preprocessing_objects,
    transform_dataset,
)


PROJECT_ROOT = Path(__file__).resolve().parent
MODEL_PATH = PROJECT_ROOT / "models" / "ann_model.pth"
PREPROCESSING_PATH = PROJECT_ROOT / "models" / "preprocessing_artifacts.pkl"
HTML_PATH = PROJECT_ROOT / "templates" / "index.html"
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Using Neural Network for Security Attacks Detection",
    description="A local demonstration using the saved NSL-KDD ANN model.",
)


@lru_cache(maxsize=1)
def _load_demo_resources() -> tuple[SecurityAttackDetectionANN, dict[str, Any]]:
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(f"Trained model not found: {MODEL_PATH}")
    if not PREPROCESSING_PATH.is_file():
        raise FileNotFoundError(f"Saved preprocessing artifacts not found: {PREPROCESSING_PATH}")

    artifacts = load_preprocessing_objects(PREPROCESSING_PATH)
    model = build_model()
    state = torch.load(MODEL_PATH, map_location="cpu", weights_only=True)
    model.load_state_dict(state)
    model.eval()
    return model, artifacts


def _resources_or_503() -> tuple[SecurityAttackDetectionANN, dict[str, Any]]:
    try:
        return _load_demo_resources()
    except (FileNotFoundError, OSError, RuntimeError, ValueError, pickle.UnpicklingError) as exc:
        logger.exception("Unable to load the saved model or preprocessing artifacts.")
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def _load_dataset_examples(artifacts: dict[str, Any]) -> dict[str, dict[str, Any]]:
    dataset_path = DATA_DIR / "KDDTrain+.txt"
    if not dataset_path.is_file():
        raise FileNotFoundError(f"Training dataset required for examples not found: {dataset_path}")

    sample = pd.read_csv(
        dataset_path,
        header=None,
        names=NSL_KDD_COLUMNS,
        nrows=256,
    )
    examples: dict[str, dict[str, Any]] = {}
    for key, label_match in (("normal", sample["label"] == "normal"), ("attack", sample["label"] != "normal")):
        matches = sample.loc[label_match]
        if matches.empty:
            raise ValueError(f"No {key} example found in the first 256 training records.")
        row = matches.iloc[0]
        examples[key] = {
            column: str(row[column]) if column in CATEGORICAL_COLUMNS else float(row[column])
            for column in artifacts["feature_columns"]
        }
    return examples


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    if not HTML_PATH.is_file():
        raise HTTPException(status_code=500, detail=f"Web interface not found: {HTML_PATH}")
    return HTMLResponse(HTML_PATH.read_text(encoding="utf-8"))


@app.get("/metadata")
def metadata() -> dict[str, Any]:
    _, artifacts = _resources_or_503()
    encoder = artifacts["categorical_encoder"]
    category_options = {
        name: [str(value) for value in categories]
        for name, categories in zip(encoder.feature_names_in_, encoder.categories_)
    }
    try:
        examples = _load_dataset_examples(artifacts)
    except (FileNotFoundError, OSError, ValueError, KeyError) as exc:
        logger.exception("Unable to load valid dataset examples for the demo.")
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {
        "features": artifacts["feature_columns"],
        "categorical_columns": artifacts["categorical_columns"],
        "numerical_columns": artifacts["numerical_columns"],
        "categories": category_options,
        "examples": examples,
        "label_mapping": artifacts["label_mapping"],
        "model_information": {
            "architecture": "122 → 500 → 24",
            "hidden_activation": "Sigmoid",
            "output_activation": "Softmax",
            "dataset": "NSL-KDD",
            "test_multiclass_accuracy": "68.3907%",
            "test_normal_vs_abnormal_accuracy": "71.6776%",
        },
    }


@app.post("/predict")
def predict(payload: dict[str, Any]) -> dict[str, Any]:
    model, artifacts = _resources_or_503()
    feature_columns = list(artifacts["feature_columns"])
    missing = [column for column in feature_columns if column not in payload]
    extra = [column for column in payload if column not in feature_columns]
    if missing:
        raise HTTPException(status_code=422, detail=f"Missing required feature values: {missing}")
    if extra:
        raise HTTPException(status_code=422, detail=f"Unexpected feature values: {extra}")

    row: dict[str, Any] = {}
    encoder = artifacts["categorical_encoder"]
    category_options = {
        name: {str(value) for value in values}
        for name, values in zip(encoder.feature_names_in_, encoder.categories_)
    }
    for column in feature_columns:
        value = payload[column]
        if column in artifacts["categorical_columns"]:
            if not isinstance(value, str) or not value.strip():
                raise HTTPException(status_code=422, detail=f"{column} must be a non-empty categorical value.")
            if value not in category_options[column]:
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid {column} value. Choose one of: {sorted(category_options[column])}",
                )
            row[column] = value
            continue

        if isinstance(value, bool):
            raise HTTPException(status_code=422, detail=f"{column} must be a finite number.")
        try:
            numeric_value = float(value)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=f"{column} must be a finite number.") from exc
        if not math.isfinite(numeric_value):
            raise HTTPException(status_code=422, detail=f"{column} must be a finite number.")
        row[column] = numeric_value

    row["label"] = "normal"
    input_frame = pd.DataFrame([row], columns=[*feature_columns, "label"])
    try:
        features, _ = transform_dataset(input_frame, artifacts)
        model_input = torch.as_tensor(features, dtype=torch.float32)
        with torch.no_grad():
            probabilities = model(model_input)[0]
    except (ValueError, TypeError, KeyError, RuntimeError) as exc:
        logger.exception("Preprocessing or inference failed for a prediction request.")
        raise HTTPException(status_code=422, detail=f"Unable to process this traffic record: {exc}") from exc

    if probabilities.shape != (24,) or not torch.isfinite(probabilities).all():
        logger.error("The saved model returned an invalid probability vector: %s", tuple(probabilities.shape))
        raise HTTPException(status_code=500, detail="The saved model returned invalid prediction probabilities.")

    class_id = int(torch.argmax(probabilities).item())
    confidence = float(probabilities[class_id].item())
    names_by_id = {int(index): name for name, index in artifacts["label_mapping"].items()}
    predicted_class = names_by_id.get(class_id)
    if predicted_class is None:
        raise HTTPException(status_code=500, detail=f"No saved label name exists for class {class_id}.")
    if class_id == 23:
        predicted_class = "other/unknown"

    is_normal = class_id == 0
    return {
        "prediction": "normal" if is_normal else "attack",
        "status": "✓ NORMAL TRAFFIC" if is_normal else "⚠ ATTACK DETECTED",
        "predicted_class": predicted_class,
        "class_id": class_id,
        "confidence": confidence,
        "confidence_percent": confidence * 100,
    }
