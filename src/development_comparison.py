"""Compare training choices on grouped development data only; never reads test data."""
import json
import warnings
from pathlib import Path
import numpy as np
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.linear_model import LogisticRegression
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
import pandas as pd
from src.preprocessing import DATA_DIR, FEATURE_COLUMNS, CATEGORICAL_COLUMNS, NUMERICAL_COLUMNS, _load_dataset
from src.improved_detector import choose_threshold, make_model, metrics

ROOT=Path(__file__).resolve().parents[1]

def run():
    train=_load_dataset(DATA_DIR/'KDDTrain+.txt')
    groups=pd.util.hash_pandas_object(train[FEATURE_COLUMNS], index=False).to_numpy()
    outcomes=[]
    for seed in (42, 17):
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', message='The least populated class')
            splitter=StratifiedGroupKFold(n_splits=5,shuffle=True,random_state=seed)
            tr, val=next(splitter.split(train,train.label,groups))
        training, validation=train.iloc[tr],train.iloc[val]
        x=training[FEATURE_COLUMNS]; y=(training.label!='normal').astype(int).to_numpy()
        v=validation[FEATURE_COLUMNS]; truth=(validation.label!='normal').astype(int).to_numpy()
        counts=training.label.value_counts()
        weights=np.array([min(10., np.sqrt(len(training)/(len(counts)*counts[label]))) for label in training.label])
        weights /= weights.mean()
        cat=OneHotEncoder(handle_unknown='ignore',sparse_output=False)
        prep=ColumnTransformer([('category',cat,CATEGORICAL_COLUMNS),('numeric',StandardScaler(),NUMERICAL_COLUMNS)])
        options=[('boosted',make_model(),{}),('weighted_boosted',make_model(),{'histgradientboostingclassifier__sample_weight':weights}),('logistic',make_pipeline(prep,LogisticRegression(max_iter=300,random_state=seed)),{})]
        for name,model,kwargs in options:
            model.fit(x,y,**kwargs)
            score=model.predict_proba(v)[:,1]; threshold=choose_threshold(truth,score)
            result=metrics(truth,score,threshold)
            by_label={}
            for label in sorted(set(validation.label)-{'normal'}):
                mask=(validation.label==label).to_numpy()
                by_label[label]={'support':int(mask.sum()),'recall':float((score[mask]>=threshold).mean())}
            outcomes.append({'split_seed':seed,'model':name,'threshold':threshold,'metrics':result,'per_attack':by_label})
            print(seed,name,'recall',round(result['attack_recall'],4),'fpr',round(result['false_positive_rate'],4),flush=True)
    out={'description':'Development-only comparison; threshold and metrics share the validation split, and this is not an independent evaluation. Test data was not read. Rare class estimates are unreliable.','runs':outcomes}
    (ROOT/'results/development_comparison.json').write_text(json.dumps(out,indent=2),encoding='utf-8')

if __name__=='__main__': run()
