# NSL-KDD intrusion detection experiments

This project reproduces parts of the supplied paper, **Using Neural Network for Security Attacks Detection**, and evaluates two separate proposed approaches. It is a research and demonstration project, not a production intrusion detection system.

## Models and completed work

- **Paper baseline:** 122 → 500 → 24 ANN, sigmoid hidden layer and softmax output, trained with mini-batch gradient ascent. It is a partial reproduction: the paper does not specify enough detail to reproduce its regularization and unknown-attack method.
- **Class-weighted ANN:** same architecture and split, with inverse-frequency class weights and separate saved outputs. It predicts individual known attack labels and a reserved unknown output.
- **Gradient-boosted detector:** a separate histogram gradient boosting model that predicts **normal versus attack**, using a validation-selected score threshold. It does not predict attack names or identify whether an attack is unknown.
- Audited the supplied NSL-KDD files, added reproducible data analysis, saved model artifacts and metrics, and provided a local FastAPI demo of the **baseline ANN**. The demo does not currently use the boosted detector.

## Data and limitations

`data/KDDTrain+.txt` has 125,973 rows; `data/KDDTest+.txt` has 22,544. Each has 41 features, an attack label and a difficulty column. The data source recorded by the project is in [DATASET_VERIFICATION.md](DATASET_VERIFICATION.md); verify provenance, redistribution rights and suitability before reuse. The paper is in `reference/81970400.pdf`.

The test file contains 17 attack names not present in training (3,750 rows). The ANN's reserved unknown output has no positive training examples and neither ANN correctly predicted it for these rows. Binary attack detection and identifying an unknown class are different tasks.

The test set has been examined repeatedly, so the results below are **exploratory**, not an unbiased final benchmark. The audit found 664 test rows with feature vectors also found in training. Validation and test results do not establish real-world deployment performance. See [MODEL_WORKFLOW.md](MODEL_WORKFLOW.md).

## Saved results

All figures below are from the project's saved NSL-KDD test evaluation; lower false-positive rate is better. The ANN binary result groups every non-normal prediction as an attack.

| Metric | Baseline ANN | Class-weighted ANN | Gradient boosting |
|---|---:|---:|---:|
| Binary accuracy | 71.68% | 83.68% | 90.84% |
| Attack recall | 55.58% | 82.82% | 88.26% |
| False-positive rate on normal traffic | 7.04% | 15.19% | 5.75% |
| Multiclass accuracy | 68.39% | 68.76% | Not applicable |

The boosted model detected 3,084 of 3,750 unseen-label attacks as attacks (82.24%); it did not identify them as unknown. Its threshold was selected to target a maximum 5% false-positive rate on its validation split, not on the test set or future traffic. The paper reports approximately 70% multiclass and 80% normal/abnormal accuracy; differences in methods and incomplete paper details prevent a strict apples-to-apples comparison.

Detailed outputs: `results/evaluation_results.json`, `results/proposed_evaluation_results.json`, `results/improved_binary_results.json`, and `results/data_audit.json`. Saved confusion matrices and per-class reports are also in `results/`.

## Setup (Windows PowerShell)

Install Python 3.10 or newer and Git, then open a terminal in this folder. If you obtained the project from a Git remote, clone it first and change to its folder. Confirm that the data files and saved models are present; downloading a source-only repository may not include them.

```powershell
py --version
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt pytest
```

Use `.venv-new` instead of `.venv` if that is the environment you already created. Dependencies are currently unpinned, so version changes may affect reproducibility. Do not load pickle or joblib files from untrusted sources.

## Run the project

Run commands from the project root using the Python executable in your environment:

```powershell
# Analyze dataset structure and save results/data_audit.json
.\.venv\Scripts\python.exe -m src.data_audit

# Test the project
.\.venv\Scripts\python.exe -m pytest -q

# Train and evaluate the gradient-boosted binary detector
.\.venv\Scripts\python.exe -m src.improved_detector

# Start the baseline ANN demonstration
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000` for the demo. The boosted training command overwrites `models/improved_binary_detector.joblib` and `results/improved_binary_results.json`. It does not overwrite baseline artifacts.

To rerun the weighted ANN, first ensure the baseline preprocessing artifact exists, then run:

```powershell
.\.venv\Scripts\python.exe -m src.train_proposed
.\.venv\Scripts\python.exe -m src.evaluate_proposed
```

These commands overwrite the corresponding `proposed_` model and result files. To recreate the baseline, use `python -m src.train` followed by `python -m src.evaluate`; these overwrite baseline model, preprocessing and evaluation artifacts. See [MODEL_WORKFLOW.md](MODEL_WORKFLOW.md) for the full sequence and remaining work.

## Layout

- `src/`: preprocessing, models, training, evaluation and data audit.
- `data/`: provided NSL-KDD files.
- `models/`: saved model and preprocessing artifacts.
- `results/`: metrics, confusion matrices and plots.
- `tests/`: automated tests.
- `app.py`, `templates/`: local demonstration using the baseline model.
- `reference/`: supplied research paper.

## Next steps

Use group-aware validation to keep identical feature vectors together; compare multiple seeds and simpler baselines; evaluate threshold stability, calibration and attack-family performance; and assess on independent representative traffic. Add input validation and connect the improved model to the demo only after the model has been suitably evaluated. The requested presentation is deferred until the user confirms.
