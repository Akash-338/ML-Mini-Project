"""Audit the saved detector on the previously inspected test split, without retraining."""
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from src.improved_detector import metrics
from src.preprocessing import FEATURE_COLUMNS, load_dataset_files

ROOT=Path(__file__).resolve().parents[1]
def run():
    train,test=load_dataset_files()
    bundle=joblib.load(ROOT/'models/grouped_binary_detector.joblib')
    known=pd.util.hash_pandas_object(train[FEATURE_COLUMNS],index=False)
    overlap=pd.util.hash_pandas_object(test[FEATURE_COLUMNS],index=False).isin(set(known)).to_numpy()
    y=(test.label!='normal').astype(int).to_numpy()
    score=bundle['model'].predict_proba(test[FEATURE_COLUMNS])[:,1]
    report={'note':'Exploratory: test data has been used before. Feature overlap does not establish event identity. Neither subset is independent.', 'test_with_feature_overlap':metrics(y[overlap],score[overlap],bundle['threshold']), 'test_without_feature_overlap':metrics(y[~overlap],score[~overlap],bundle['threshold'])}
    (ROOT/'results/overlap_diagnostics.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
if __name__=='__main__': run()
