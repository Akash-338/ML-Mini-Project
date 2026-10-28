from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder, StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
MODEL_DIR = PROJECT_ROOT / "models"
MODEL_PATH = MODEL_DIR / "preprocessing_artifacts.pkl"

NSL_KDD_COLUMNS = [
    "duration",
    "protocol_type",
    "service",
    "flag",
    "src_bytes",
    "dst_bytes",
    "land",
    "wrong_fragment",
    "urgent",
    "hot",
    "num_failed_logins",
    "logged_in",
    "num_compromised",
    "root_shell",
    "su_attempted",
    "num_root",
    "num_file_creations",
    "num_shells",
    "num_access_files",
    "num_outbound_cmds",
    "is_host_login",
    "is_guest_login",
    "count",
    "srv_count",
    "serror_rate",
    "srv_serror_rate",
    "rerror_rate",
    "srv_rerror_rate",
    "same_srv_rate",
    "diff_srv_rate",
    "srv_diff_host_rate",
    "dst_host_count",
    "dst_host_srv_count",
    "dst_host_same_srv_rate",
    "dst_host_diff_srv_rate",
    "dst_host_same_src_port_rate",
    "dst_host_srv_diff_host_rate",
    "dst_host_serror_rate",
    "dst_host_srv_serror_rate",
    "dst_host_rerror_rate",
    "dst_host_srv_rerror_rate",
    "label",
    "difficulty",
]

FEATURE_COLUMNS = NSL_KDD_COLUMNS[:-2]
CATEGORICAL_COLUMNS = ["protocol_type", "service", "flag"]
NUMERICAL_COLUMNS = [col for col in FEATURE_COLUMNS if col not in CATEGORICAL_COLUMNS]
TARGET_COLUMN = "label"


def _load_dataset(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, header=None, names=NSL_KDD_COLUMNS)
    if df.shape[1] != 43:
        raise ValueError(f"Unexpected dataset shape for {path.name}: {df.shape}. Expected 43 columns.")
    return df


def _build_label_mapping(train_labels: pd.Series) -> Dict[str, int]:
    known_attack_labels = sorted({label for label in train_labels if label != "normal"})
    if len(known_attack_labels) != 22:
        raise ValueError(
            "Training dataset does not contain exactly 22 known attack labels after excluding 'normal'. "
            f"Found {len(known_attack_labels)}: {known_attack_labels}"
        )

    label_to_index = {"normal": 0}
    for idx, attack_label in enumerate(known_attack_labels, start=1):
        label_to_index[attack_label] = idx
    label_to_index["other"] = 23
    return label_to_index


def _encode_labels(labels: pd.Series, label_to_index: Dict[str, int]) -> np.ndarray:
    encoded = np.array([label_to_index.get(label, label_to_index["other"]) for label in labels], dtype=np.int64)
    return encoded


def _one_hot_encode_labels(encoded_labels: np.ndarray, num_classes: int = 24) -> np.ndarray:
    return np.eye(num_classes, dtype=np.float64)[encoded_labels]


def _save_preprocessing_objects(artifacts: Dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as f:
        pickle.dump(artifacts, f)


def load_dataset_files() -> Tuple[pd.DataFrame, pd.DataFrame]:
    train_path = DATA_DIR / "KDDTrain+.txt"
    test_path = DATA_DIR / "KDDTest+.txt"
    if not train_path.exists() or not test_path.exists():
        raise FileNotFoundError(
            "Required NSL-KDD files are missing. Expected: "
            f"{train_path} and {test_path}"
        )
    return _load_dataset(train_path), _load_dataset(test_path)


def load_preprocessing_objects(path: Path | None = None) -> Dict[str, Any]:
    artifact_path = MODEL_PATH if path is None else Path(path)
    if not artifact_path.is_file():
        raise FileNotFoundError(f"Saved preprocessing objects not found: {artifact_path}")
    with artifact_path.open("rb") as f:
        artifacts = pickle.load(f)
    required_keys = {
        "categorical_encoder",
        "numeric_scaler",
        "feature_columns",
        "categorical_columns",
        "numerical_columns",
        "label_mapping",
        "output_classes",
    }
    missing = required_keys.difference(artifacts)
    if missing:
        raise ValueError(f"Preprocessing artifact is missing required entries: {sorted(missing)}")
    return artifacts


def transform_dataset(
    df: pd.DataFrame,
    artifacts: Dict[str, Any],
) -> Tuple[np.ndarray, np.ndarray]:
    """Transform records with persisted training-fitted preprocessing objects."""
    feature_columns = artifacts["feature_columns"]
    categorical_columns = artifacts["categorical_columns"]
    numerical_columns = artifacts["numerical_columns"]
    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Dataset must include the {TARGET_COLUMN!r} column.")
    missing_columns = set(feature_columns).difference(df.columns)
    if missing_columns:
        raise ValueError(f"Dataset is missing required feature columns: {sorted(missing_columns)}")
    if artifacts["output_classes"] != 24:
        raise ValueError(f"Expected 24 output classes; artifact declares {artifacts['output_classes']}.")

    features = df[feature_columns]
    numeric_values = artifacts["numeric_scaler"].transform(
        features[numerical_columns].astype(np.float64)
    )
    categorical_values = artifacts["categorical_encoder"].transform(
        features[categorical_columns].astype(str)
    )
    X = np.hstack([numeric_values, categorical_values])
    Y = _one_hot_encode_labels(
        _encode_labels(df[TARGET_COLUMN], artifacts["label_mapping"]),
        num_classes=artifacts["output_classes"],
    )
    if X.shape[1] != 122:
        raise ValueError(f"Transformed feature count must be 122; observed {X.shape[1]}.")
    if Y.shape[1] != 24:
        raise ValueError(f"Transformed label count must be 24; observed {Y.shape[1]}.")
    return X, Y


def preprocess_data() -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Dict[str, Any], Dict[str, int]]:
    train_df, test_df = load_dataset_files()

    train_features = train_df[FEATURE_COLUMNS].copy()
    test_features = test_df[FEATURE_COLUMNS].copy()

    if train_features.shape[1] != 41 or test_features.shape[1] != 41:
        raise ValueError(
            f"Feature matrix should have 41 columns before preprocessing. "
            f"Observed: train={train_features.shape[1]}, test={test_features.shape[1]}"
        )

    label_mapping = _build_label_mapping(train_df[TARGET_COLUMN])

    train_numeric = train_features[NUMERICAL_COLUMNS].astype(np.float64)
    test_numeric = test_features[NUMERICAL_COLUMNS].astype(np.float64)

    cat_encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False, dtype=np.float64)
    train_categorical = cat_encoder.fit_transform(train_features[CATEGORICAL_COLUMNS].astype(str))
    test_categorical = cat_encoder.transform(test_features[CATEGORICAL_COLUMNS].astype(str))

    # Fit the scaler only on the training data.
    scaler = StandardScaler()
    train_numeric_scaled = scaler.fit_transform(train_numeric)
    test_numeric_scaled = scaler.transform(test_numeric)

    X_train = np.hstack([train_numeric_scaled, train_categorical])
    X_test = np.hstack([test_numeric_scaled, test_categorical])
    train_y_int = _encode_labels(train_df[TARGET_COLUMN], label_mapping)
    test_y_int = _encode_labels(test_df[TARGET_COLUMN], label_mapping)
    train_y = _one_hot_encode_labels(train_y_int, num_classes=24)
    test_y = _one_hot_encode_labels(test_y_int, num_classes=24)

    if X_train.shape[1] != 122:
        raise ValueError(f"X_train.shape[1] != 122. Observed: {X_train.shape[1]}")
    if X_test.shape[1] != 122:
        raise ValueError(f"X_test.shape[1] != 122. Observed: {X_test.shape[1]}")
    if train_y.shape[1] != 24:
        raise ValueError(f"Y_train.shape[1] != 24. Observed: {train_y.shape[1]}")
    if test_y.shape[1] != 24:
        raise ValueError(f"Y_test.shape[1] != 24. Observed: {test_y.shape[1]}")

    preprocessing_objects = {
        "categorical_encoder": cat_encoder,
        "numeric_scaler": scaler,
        "feature_columns": FEATURE_COLUMNS,
        "categorical_columns": CATEGORICAL_COLUMNS,
        "numerical_columns": NUMERICAL_COLUMNS,
        "known_attack_labels": sorted({label for label in train_df[TARGET_COLUMN] if label != "normal"}),
        "label_mapping": label_mapping,
        "output_classes": 24,
    }

    _save_preprocessing_objects(preprocessing_objects, MODEL_PATH)

    known_train_attack_classes = sorted({label for label in train_df[TARGET_COLUMN] if label != "normal"})
    unknown_test_count = int(np.sum(test_y_int == label_mapping["other"]))

    print(f"Training samples: {len(train_df)}")
    print(f"Test samples: {len(test_df)}")
    print(f"X_train shape: {X_train.shape}")
    print(f"X_test shape: {X_test.shape}")
    print(f"Y_train shape: {train_y.shape}")
    print(f"Y_test shape: {test_y.shape}")
    print(f"Number of known attack classes: {len(known_train_attack_classes)}")
    print(f"Number of unknown test attacks mapped to 'other': {unknown_test_count}")

    return X_train, X_test, train_y, test_y, preprocessing_objects, label_mapping


if __name__ == "__main__":
    preprocess_data()
