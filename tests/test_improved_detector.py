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
