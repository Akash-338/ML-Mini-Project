# Network traffic attack detection

A PES University ML mini project by **Akash Kiran Vernekar** (PES1UG24AM338) and **Dhanraj Rathod** (PES1UG24AM359).

The current project uses a **histogram gradient-boosted binary classifier** to classify NSL-KDD records as normal or attack. It is a research demonstration, not a production intrusion detection system. It does not identify the attack type or tell whether an attack is unknown.

## Project history and model choice

The project began with the supplied paper, *Using Neural Network for Security Attacks Detection*. The original baseline reproduced its 122-input, 500-hidden-unit, 24-output ANN as far as the paper allowed. The paper names a regularized training method but does not specify its regularizer. The reproduction did not apply an invented regularizer and should be described as a partial reproduction.

Two alternatives were explored:

1. **Class-weighted ANN:** the same network architecture with inverse-frequency training weights. We tried it because rare attacks contribute little to an unweighted loss. It increased attack recall, but its false-alarm rate increased and the largest weights made training unstable. It could predict known attack labels, but its reserved unknown class had no positive training examples.
2. **Gradient-boosted detector:** an ensemble of decision trees trained for normal-versus-attack detection. We tried it because tree ensembles can learn nonlinear patterns in tabular data and provide an attack score for a chosen threshold. In the recorded comparison it detected more attacks than either ANN. It cannot name the attack and misses important attack types.

The baseline and weighted ANN files were removed in the project cleanup. Their historical code and outputs remain accessible through Git history, including commit `394c8f4`. Only the group-aware boosted detector remains in the current tree. [MODEL_WORKFLOW.md](MODEL_WORKFLOW.md) gives the detailed method and limitations.

## Data and workflow

The provided NSL-KDD files contain 125,973 `KDDTrain+` and 22,544 `KDDTest+` records. Each record has 41 input features, a label and a difficulty field. The model excludes the label and difficulty from its inputs. See [DATASET_VERIFICATION.md](DATASET_VERIFICATION.md) for the schema and audit.

The current training script groups records with identical feature hashes and uses the first fold of a five-fold stratified group split, seed 42. For the saved run this gives **100,778 training** and **25,195 validation** records from KDDTrain+. It fits the categorical encoder and detector on the training partition, then chooses a score threshold on validation. KDDTest+ supplies **22,544 test** records. The earlier ANN experiments instead used the full KDDTrain+ set and had no separate validation split.

The threshold maximizes validation attack recall subject to an empirical validation false-positive rate of at most 5%. This does not guarantee a 5% rate on test or future traffic. The test set was inspected during development, so the test numbers are exploratory. Identical feature vectors appear in 664 test rows and somewhere in the full training file; this does not establish that the original events are duplicates.

## Current saved detector results

These figures come from [grouped_binary_results.json](results/grouped_binary_results.json), using the saved decision threshold. The file contains per-attack metrics and the model hash.

| Test measure | Result |
|---|---:|
| Normal-versus-attack accuracy | 87.56% |
| Attack recall | 85.16% |
| Attack precision | 92.39% |
| False-positive rate on normal traffic | 9.27% |
| Missed attacks | 1,905 / 12,833 |
| Unseen-label records detected as attacks | 2,996 / 3,750 |

The last row measures whether attacks with names absent from training were flagged as attacks. It does **not** measure identifying them as unknown. Important weak classes include `guess_passwd` (223/1,231 detected), `snmpgetattack` (0/178) and `snmpguess` (7/331).

The 9-slide [presentation](presentation/PES_ML_Intrusion_Detection.pptx) compares the three last-run models. Its weighted ANN numbers come from a later rerun, which differs slightly from the archived `394c8f4` run documented in [MODEL_WORKFLOW.md](MODEL_WORKFLOW.md); the historical runs are not claimed to be identical.

## Setup and run

From the project folder in Windows PowerShell:

```powershell
py --version
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt pytest
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. If the environment already exists as `.venv-new`, use that path instead. The direct dependencies are pinned to the saved model's tested versions, with Python 3.13.14 used for the recorded run. They are not a complete transitive lockfile. Load only trusted joblib files.

The demo loads a normal or attack example from training data, checks inputs and returns the binary prediction, attack score and threshold. The score is not a calibrated probability. The app displays test accuracy only when the report's model hash matches the model file.

## Re-run experiments

Run each command from the project root using the environment's Python:

```powershell
# Audit raw data; overwrites results/data_audit.json
.\.venv\Scripts\python.exe -m src.data_audit

# Train and evaluate the retained model; overwrites the model and its result report
.\.venv\Scripts\python.exe -m src.improved_detector

# Compare candidates using only development data; overwrites development_comparison.json
.\.venv\Scripts\python.exe -m src.development_comparison

# Report test results with and without feature overlap; overwrites overlap_diagnostics.json
.\.venv\Scripts\python.exe -m src.overlap_diagnostics
```

Restart the app after retraining because it caches the loaded model. The development comparison uses the same validation partition to select thresholds and report metrics, so its scores are optimistic. The overlap diagnostic uses the already examined test set and is not an independent evaluation.

## Project files

- `src/preprocessing.py`: data schema and loading.
- `src/data_audit.py`: data quality and overlap audit.
- `src/improved_detector.py`: split, train, threshold selection and evaluation.
- `src/development_comparison.py`, `src/overlap_diagnostics.py`: diagnostic experiments.
- `models/grouped_binary_detector.joblib`: saved preprocessing, estimator and threshold.
- `results/`: audit and evaluation reports.
- `app.py`, `templates/`: local demo; `tests/`: automated checks.
- `reference/`: supplied paper; `presentation/`: project presentation.

## Limitations and next steps

The data is a benchmark rather than representative live network traffic. The score has not been calibrated, the 5% target did not hold on test, and the classifier misses many examples of some attacks. Evaluate a frozen procedure on independent and more representative data, repeat grouped validation across splits, investigate rare classes, and verify a real feature-extraction pipeline before considering deployment.
