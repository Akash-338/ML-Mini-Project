import math
import pytest
import app

def test_metadata_and_prediction_use_grouped_model():
    metadata = app.metadata()
    assert len(metadata['features']) == 41
    for example in metadata['examples'].values():
        prediction = app.predict(example)
        assert prediction['prediction'] in {'normal', 'attack'}
        assert math.isfinite(prediction['attack_score_percent'])
        assert 0 <= prediction['threshold_percent'] <= 100
        assert (prediction['attack_score_percent'] >= prediction['threshold_percent']) == (prediction['prediction'] == 'attack')

def test_prediction_rejects_missing_features():
    with pytest.raises(Exception) as exc:
        app.predict({})
    assert exc.value.status_code == 422
