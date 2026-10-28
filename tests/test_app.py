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

def test_prediction_rejects_invalid_feature_values():
    from fastapi import HTTPException
    original = app.metadata()['examples']['normal']
    for field, invalid in [('duration', -1), ('count', 1.5), ('serror_rate', 1.1), ('land', 2)]:
        row = dict(original, **{field: invalid})
        with pytest.raises(HTTPException) as error:
            app.predict(row)
        assert error.value.status_code == 422

def test_displayed_accuracy_requires_matching_model_hash(monkeypatch, tmp_path):
    import json
    from pathlib import Path
    (tmp_path / 'results').mkdir()
    report = {'model_sha256': 'incorrect', 'test': {'accuracy': 1}}
    (tmp_path / 'results' / 'grouped_binary_results.json').write_text(json.dumps(report))
    (tmp_path / 'data').mkdir()
    monkeypatch.setattr(app, 'ROOT', tmp_path)
    monkeypatch.setattr(app, 'DATA_DIR', Path(__file__).resolve().parents[1] / 'data')
    assert app.metadata()['model_information']['test_normal_vs_abnormal_accuracy'] == 'Unavailable'
