"""Validation-selected binary intrusion detector; preserves the paper baseline.

Run: python -m src.improved_detector (writes separate improved artifacts).
The historical test split has already been examined, so it is not a pristine holdout.
"""
from __future__ import annotations
import hashlib, json, platform
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import confusion_matrix, roc_auc_score, average_precision_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder
from src.preprocessing import FEATURE_COLUMNS, CATEGORICAL_COLUMNS, NUMERICAL_COLUMNS, load_dataset_files

ROOT = Path(__file__).resolve().parents[1]
SEED = 42
MAX_FPR = 0.05

def choose_threshold(y, scores, max_fpr=MAX_FPR):
    """Highest recall on validation subject to empirical normal false-alarm limit."""
    y, scores = np.asarray(y), np.asarray(scores)
    if y.ndim != 1 or scores.ndim != 1 or len(y) != len(scores) or not np.isfinite(scores).all():
        raise ValueError('Labels and finite scores must be matching one-dimensional arrays')
    if not 0 <= max_fpr <= 1 or not np.isin(y, [0, 1]).all():
        raise ValueError('Expected binary labels and a false-positive limit between 0 and 1')
    if not ((y == 0).any() and (y == 1).any()):
        raise ValueError('Both normal and attack validation examples are required')
    candidates = np.r_[np.nextafter(scores.max(), np.inf), np.unique(scores)[::-1]]
    normal = np.sort(scores[y == 0]); attacks = np.sort(scores[y == 1])
    fp = len(normal) - np.searchsorted(normal, candidates, side='left')
    tp = len(attacks) - np.searchsorted(attacks, candidates, side='left')
    valid = fp / len(normal) <= max_fpr
    best = np.flatnonzero(valid)[np.argmax(tp[valid])]
    return float(candidates[best])

def metrics(y, scores, threshold):
    pred = (scores >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {'normal': int(tn+fp), 'attacks': int(tp+fn), 'true_normal': int(tn), 'false_alarms': int(fp), 'missed_attacks': int(fn), 'detected_attacks': int(tp), 'accuracy': float((tn+tp)/len(y)), 'false_positive_rate': float(fp/(tn+fp)), 'attack_recall': float(tp/(tp+fn)), 'attack_precision': float(tp/(tp+fp)) if tp+fp else 0., 'roc_auc': float(roc_auc_score(y,scores)), 'average_precision': float(average_precision_score(y,scores))}

def make_model():
    prep = ColumnTransformer([('category', OneHotEncoder(handle_unknown='ignore', sparse_output=False), CATEGORICAL_COLUMNS), ('numeric', 'passthrough', NUMERICAL_COLUMNS)])
    return make_pipeline(prep, HistGradientBoostingClassifier(max_iter=200, learning_rate=0.08, max_leaf_nodes=15, min_samples_leaf=30, l2_regularization=2., early_stopping=False, random_state=SEED))

def grouped_split(train):
    """Stratify labels approximately while keeping identical features together."""
    groups = pd.util.hash_pandas_object(train[FEATURE_COLUMNS], index=False).to_numpy()
    splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
    train_idx, validation_idx = next(splitter.split(train, train['label'], groups))
    if set(groups[train_idx]) & set(groups[validation_idx]):
        raise AssertionError('Identical feature groups crossed the split')
    return train.iloc[train_idx], train.iloc[validation_idx]

def run():
    train, test = load_dataset_files()
    train_part, validation = grouped_split(train)
    model = make_model()
    model.fit(train_part[FEATURE_COLUMNS], (train_part.label != 'normal').astype(int))
    val_y = (validation.label != 'normal').astype(int).to_numpy()
    val_score = model.predict_proba(validation[FEATURE_COLUMNS])[:, 1]
    threshold = choose_threshold(val_y, val_score)
    test_y = (test.label != 'normal').astype(int).to_numpy()
    scores = model.predict_proba(test[FEATURE_COLUMNS])[:, 1]
    known = set(train_part.label) - {'normal'}
    unseen = (~test.label.isin(known | {'normal'})).to_numpy()
    per_attack = {}
    for label in sorted(set(test.label) - {'normal'}):
        mask = (test.label == label).to_numpy()
        per_attack[label] = {'support': int(mask.sum()), 'detected': int((scores[mask] >= threshold).sum()), 'recall': float((scores[mask] >= threshold).mean()), 'seen_in_training': label in known}
    report = {'task':'binary normal vs attack; does not identify unknown attack types', 'seed':SEED, 'split':'stratified group fold by 41-feature hash', 'validation_absent_training_labels': sorted(set(train.label) - set(train_part.label)), 'train_rows':len(train_part), 'validation_rows':len(validation), 'test_rows':len(test), 'validation_fpr_target':MAX_FPR, 'threshold':threshold, 'validation':metrics(val_y,val_score,threshold), 'test':metrics(test_y,scores,threshold), 'unseen_test_attacks':{'support':int(unseen.sum()), 'detected_as_attack':int((scores[unseen]>=threshold).sum()), 'recall':float((scores[unseen]>=threshold).mean())}, 'per_attack':per_attack, 'versions':{'python':platform.python_version(), 'sklearn':sklearn.__version__, 'numpy':np.__version__, 'pandas':pd.__version__}, 'data_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'data/KDDTrain+.txt',ROOT/'data/KDDTest+.txt']}, 'limitations':'Some rare labels may not appear in either development partition. The test split was examined in prior work; results are exploratory rather than a pristine final holdout. Threshold controls validation FPR only, not test or deployment FPR. Not an unknown-class classifier.'}
    (ROOT/'models').mkdir(exist_ok=True); (ROOT/'results').mkdir(exist_ok=True)
    joblib.dump({'model':model,'threshold':threshold,'feature_columns':FEATURE_COLUMNS},ROOT/'models/grouped_binary_detector.joblib')
    (ROOT/'results/grouped_binary_results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['threshold','validation','test','unseen_test_attacks']},indent=2))

if __name__ == '__main__':
    run()
