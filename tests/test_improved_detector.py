import numpy as np
from src.improved_detector import choose_threshold, metrics

def test_threshold_respects_validation_false_alarm_limit_and_maximizes_recall():
    y = np.array([0, 0, 0, 0, 1, 1, 1])
    scores = np.array([.1, .2, .3, .8, .35, .7, .9])
    threshold = choose_threshold(y, scores, .25)
    result = metrics(y, scores, threshold)
    assert result['false_alarms'] == 1
    assert result['detected_attacks'] == 3

def test_threshold_handles_tied_scores_without_exceeding_limit():
    y = np.array([0, 0, 1, 1])
    threshold = choose_threshold(y, np.array([.5, .5, .5, .9]), 0)
    assert threshold == .9

def test_threshold_rejects_invalid_inputs():
    import pytest
    with pytest.raises(ValueError):
        choose_threshold(np.array([0, 1]), np.array([0.1, np.nan]))
    with pytest.raises(ValueError):
        choose_threshold(np.array([0, 1]), np.array([0.1, 0.9]), 1.1)

def test_no_alert_threshold_is_finite():
    threshold = choose_threshold(np.array([0, 1]), np.array([0.9, 0.1]), 0)
    assert np.isfinite(threshold)
    assert threshold > 0.9

def test_grouped_split_keeps_duplicate_feature_rows_together():
    import pandas as pd
    from src.improved_detector import grouped_split
    from src.preprocessing import FEATURE_COLUMNS
    rows = []
    for i in range(30):
        row = {column: i for column in FEATURE_COLUMNS}
        row['label'] = 'normal' if i % 2 else 'attack'
        rows.extend([row.copy(), row.copy()])
    train, validation = grouped_split(pd.DataFrame(rows))
    assert set(train['duration']).isdisjoint(set(validation['duration']))
    assert len(train) + len(validation) == len(rows)
