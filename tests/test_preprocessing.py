import numpy as np

import src.preprocessing as preprocessing
from src.preprocessing import preprocess_data


def test_preprocessing_shapes_and_label_encoding(tmp_path, monkeypatch):
    monkeypatch.setattr(preprocessing, "MODEL_PATH", tmp_path / "preprocessing_artifacts.pkl")
    X_train, X_test, Y_train, Y_test, _, label_mapping = preprocess_data()

    assert X_train.shape[1] == 122
    assert X_test.shape[1] == 122
    assert Y_train.shape[1] == 24
    assert Y_test.shape[1] == 24
    assert X_train.shape[1] == X_test.shape[1]

    assert np.allclose(Y_train.sum(axis=1), 1.0)
    assert np.allclose(Y_test.sum(axis=1), 1.0)

    assert np.any(Y_test[:, 23] == 1.0)

    label_values = list(label_mapping.keys())
    assert "normal" in label_values
    assert label_mapping["normal"] == 0
    assert label_mapping["other"] == 23
    assert (tmp_path / "preprocessing_artifacts.pkl").is_file()
