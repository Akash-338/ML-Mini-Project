"""Read-only dataset audit. Writes a separate machine-readable analysis report."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from src.preprocessing import (DATA_DIR, FEATURE_COLUMNS, CATEGORICAL_COLUMNS,
                               NUMERICAL_COLUMNS, load_dataset_files)

ROOT = Path(__file__).resolve().parents[1]

def summarize(df):
    numeric = df[NUMERICAL_COLUMNS].apply(pd.to_numeric, errors='coerce')
    return {'rows':len(df), 'columns':len(df.columns),
            'missing_values':int(df.isna().sum().sum()),
            'non_numeric_or_missing_numeric':int(numeric.isna().sum().sum()),
            'non_finite_numeric':int((~np.isfinite(numeric.to_numpy())).sum()),
            'duplicate_full_rows':int(df.duplicated().sum()),
            'duplicate_feature_rows':int(df.duplicated(FEATURE_COLUMNS).sum()),
            'label_counts':{str(k):int(v) for k,v in df.label.value_counts().items()},
            'categorical_values':{c:sorted(df[c].astype(str).unique().tolist()) for c in CATEGORICAL_COLUMNS},
            'constant_numeric_features':[c for c in NUMERICAL_COLUMNS if numeric[c].nunique(dropna=False)==1]}

def main():
    train,test=load_dataset_files()
    train_keys=set(map(tuple,train[FEATURE_COLUMNS].to_numpy()))
    test_overlap=test[FEATURE_COLUMNS].apply(tuple,axis=1).isin(train_keys)
    known=set(train.label)-{'normal'}
    report={'train':summarize(train),'test':summarize(test),
            'test_rows_with_features_seen_in_train':int(test_overlap.sum()),
            'test_unseen_labels':sorted(set(test.label)-set(train.label)),
            'test_unseen_attack_rows':int((~test.label.isin(known | {'normal'})).sum()),
            'unseen_categorical_values':{c:sorted(set(test[c].astype(str))-set(train[c].astype(str))) for c in CATEGORICAL_COLUMNS},
            'sha256':{name:hashlib.sha256((DATA_DIR/name).read_bytes()).hexdigest() for name in ['KDDTrain+.txt','KDDTest+.txt']},
            'notes':'Feature overlaps are identical feature vectors, not necessarily identical labels or independent network events. No external data provenance or deployment suitability is established.'}
    path=ROOT/'results'/'data_audit.json'
    path.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['test_rows_with_features_seen_in_train','test_unseen_labels','test_unseen_attack_rows','unseen_categorical_values']},indent=2))
    print('Saved',path)

if __name__=='__main__': main()
