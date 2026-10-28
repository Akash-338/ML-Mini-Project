"""Local demonstration of the group-aware binary intrusion detector."""
from functools import lru_cache
import math
from pathlib import Path
from typing import Any
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from src.preprocessing import CATEGORICAL_COLUMNS, DATA_DIR, FEATURE_COLUMNS, NSL_KDD_COLUMNS, NUMERICAL_COLUMNS

ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / 'models' / 'grouped_binary_detector.joblib'
app = FastAPI(title='Traffic Inspector', description='Local NSL-KDD binary detector demonstration.')

@lru_cache(maxsize=1)
def resources():
    if not MODEL_PATH.is_file():
        raise HTTPException(status_code=503, detail='Trained detector is missing. Run python -m src.improved_detector first.')
    try:
        bundle = joblib.load(MODEL_PATH)
        if bundle['feature_columns'] != FEATURE_COLUMNS:
            raise ValueError('Model feature schema does not match the application.')
        return bundle
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=503, detail='Unable to load detector artifacts.') from exc

@app.get('/', response_class=HTMLResponse)
def index():
    return HTMLResponse((ROOT / 'templates' / 'index.html').read_text(encoding='utf-8'))

@app.get('/metadata')
def metadata():
    bundle = resources()
    encoder = bundle['model'].named_steps['columntransformer'].named_transformers_['category']
    categories = {name: [str(v) for v in values] for name, values in zip(CATEGORICAL_COLUMNS, encoder.categories_)}
    sample = pd.read_csv(DATA_DIR / 'KDDTrain+.txt', header=None, names=NSL_KDD_COLUMNS, nrows=256)
    examples = {}
    for name, mask in [('normal', sample.label == 'normal'), ('attack', sample.label != 'normal')]:
        matches = sample.loc[mask]
        if matches.empty:
            raise HTTPException(status_code=503, detail=f'No {name} example available.')
        row = matches.iloc[0]
        examples[name] = {c: str(row[c]) if c in CATEGORICAL_COLUMNS else float(row[c]) for c in FEATURE_COLUMNS}
    return {'features': FEATURE_COLUMNS, 'categorical_columns': CATEGORICAL_COLUMNS,
            'numerical_columns': NUMERICAL_COLUMNS, 'categories': categories, 'examples': examples,
            'model_information': {'architecture': 'Gradient-boosted trees', 'dataset': 'NSL-KDD',
                                  'test_normal_vs_abnormal_accuracy': '87.56%'}}

@app.post('/predict')
def predict(payload: dict[str, Any]):
    bundle = resources()
    missing = set(FEATURE_COLUMNS) - payload.keys()
    extra = payload.keys() - set(FEATURE_COLUMNS)
    if missing or extra:
        raise HTTPException(status_code=422, detail=f'Missing: {sorted(missing)}; unexpected: {sorted(extra)}')
    encoder = bundle['model'].named_steps['columntransformer'].named_transformers_['category']
    categories = {name: {str(v) for v in values} for name, values in zip(CATEGORICAL_COLUMNS, encoder.categories_)}
    row = {}
    for name in FEATURE_COLUMNS:
        value = payload[name]
        if name in CATEGORICAL_COLUMNS:
            if not isinstance(value, str) or value not in categories[name]:
                raise HTTPException(status_code=422, detail=f'Invalid category for {name}.')
            row[name] = value
        else:
            if isinstance(value, bool):
                raise HTTPException(status_code=422, detail=f'{name} must be a finite number.')
            try:
                row[name] = float(value)
            except (ValueError, TypeError) as exc:
                raise HTTPException(status_code=422, detail=f'{name} must be a finite number.') from exc
            if not math.isfinite(row[name]):
                raise HTTPException(status_code=422, detail=f'{name} must be a finite number.')
    score = float(bundle['model'].predict_proba(pd.DataFrame([row], columns=FEATURE_COLUMNS))[0, 1])
    return {'prediction': 'attack' if score >= bundle['threshold'] else 'normal',
            'attack_score_percent': score * 100, 'threshold_percent': float(bundle['threshold'] * 100)}
