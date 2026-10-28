import numpy as np
import torch

from src.model import build_model
from src.train import EPOCHS, train_model


def test_training_pipeline_saves_model_and_history(tmp_path):
    rng = np.random.default_rng(17)
    X_train = rng.normal(size=(12, 122)).astype(np.float32)
    class_ids = np.arange(12) % 24
    Y_train = np.eye(24, dtype=np.float32)[class_ids]

    torch.manual_seed(17)
    initial_model = build_model()
    initial_parameters = [parameter.detach().clone() for parameter in initial_model.parameters()]
    model_path = tmp_path / "ann_model.pth"
    history_path = tmp_path / "training_history.csv"

    model, history = train_model(
        X_train,
        Y_train,
        seed=17,
        model_path=model_path,
        history_path=history_path,
    )

    assert len(history) == EPOCHS == 10
    assert list(history.columns) == ["epoch", "training_objective", "training_accuracy"]
    assert history["epoch"].tolist() == list(range(1, 11))
    assert any(
        not torch.equal(initial, trained.detach())
        for initial, trained in zip(initial_parameters, model.parameters())
    )
    assert model_path.exists()
    assert history_path.exists()

    loaded_model = build_model()
    loaded_state = torch.load(model_path, map_location="cpu", weights_only=True)
    loaded_model.load_state_dict(loaded_state)
    for trained, loaded in zip(model.parameters(), loaded_model.parameters()):
        assert torch.equal(trained.detach(), loaded.detach())
