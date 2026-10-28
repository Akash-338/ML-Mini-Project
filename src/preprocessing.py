from __future__ import annotations

from pathlib import Path
from typing import Tuple

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

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


def load_dataset_files() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Read the two provided NSL-KDD files without fitting transformations."""
    train_path, test_path = DATA_DIR / "KDDTrain+.txt", DATA_DIR / "KDDTest+.txt"
    if not train_path.is_file() or not test_path.is_file():
        raise FileNotFoundError("Expected KDDTrain+.txt and KDDTest+.txt in data/")
    return _load_dataset(train_path), _load_dataset(test_path)
