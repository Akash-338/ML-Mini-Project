# Network traffic attack detection

A local NSL-KDD research demo using a **histogram gradient-boosted binary classifier**. It predicts normal or attack traffic. It does not identify the attack type or determine whether an attack is unknown. This is not a production intrusion detection system.

## Data and workflow

The provided `data/KDDTrain+.txt` has 125,973 rows and `data/KDDTest+.txt` has 22,544. Each contains 41 input features, a label and a difficulty field; label and difficulty are excluded from inputs. The data source recorded by the project is described in [DATASET_VERIFICATION.md](DATASET_VERIFICATION.md). The reference paper remains in `reference/`.

The training code groups identical feature vectors in the development split, one-hot encodes the three categorical features using the training partition, and trains histogram gradient boosting. A decision threshold is chosen on validation data to maximize attack recall subject to a 5% empirical validation false-positive rate. The threshold, preprocessing and model are saved together in `models/grouped_binary_detector.joblib`.

## Saved results

The current saved evaluation is in `results/grouped_binary_results.json`:

| Test measure | Result |
|---|---:|
| Binary accuracy | 87.56% |
| Attack recall | 85.16% |
| False-positive rate | 9.27% |
| Unseen-label attacks detected as attacks | 2,996 / 3,750 |

The 5% target applies only to validation data. The test set has been inspected during development, and 664 test records share feature vectors with training records. These results are exploratory; independent representative traffic is needed for reliable external validation. Some attack types are poorly detected, and the detector does not identify unknown attacks as unknown.

## Setup and run

In PowerShell, from the project root:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt pytest
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. Replace `.venv` with `.venv-new` if that is your environment. Dependencies are unpinned; saved scikit-learn models may not load across different versions. Only load trusted joblib artifacts.

To audit the data or retrain the model:

```powershell
.\.venv\Scripts\python.exe -m src.data_audit
.\.venv\Scripts\python.exe -m src.improved_detector
```

The first command overwrites `results/data_audit.json`. The second overwrites the grouped model and results. Restart the demo after retraining because it caches the model in memory.

## Files

- `src/preprocessing.py`: dataset schema and loading.
- `src/data_audit.py`: dataset audit.
- `src/improved_detector.py`: group-aware split, training, threshold selection and evaluation.
- `models/grouped_binary_detector.joblib`: current fitted detector and preprocessing.
- `results/`: data audit and model evaluation.
- `app.py`, `templates/`: local demo.
- `tests/`: detector and application tests.

Further work includes evaluating across grouped splits and seeds, analyzing rare attacks, calibrating scores, and testing on independent, current network data.
