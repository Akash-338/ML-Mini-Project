# Model development and evaluation workflow

This document describes the retained detector and the historical experiments. The current repository contains one deployable research-demo model: `models/grouped_binary_detector.joblib`. The baseline and weighted ANNs were removed from the current tree, but earlier code and outputs are available in Git history. The demo is not a production network monitoring system.

## 1. Define the task

Given one NSL-KDD traffic record, the current model predicts **normal** or **attack**. A false positive is a normal record predicted as attack; a false negative is an attack predicted as normal. Track attack recall and the normal false-positive rate together, because reducing one may worsen the other.

The score is a model decision score, not a validated probability. The retained model has no attack-name or unknown-attack output. Detecting an attack whose name was unseen in training is different from recognizing that its attack type is unknown.

## 2. Obtain and inspect the data

The project uses the supplied NSL-KDD `data/KDDTrain+.txt` and `data/KDDTest+.txt`. Earlier project notes record a public mirror; they do not independently verify origin or license. Run `python -m src.data_audit` for row counts, missing/non-finite values, categorical values, duplicate feature rows, label distributions and SHA-256 hashes. The complete ordered schema is in `src/preprocessing.py`.

There are 41 original inputs: 38 numeric plus the categorical `protocol_type`, `service` and `flag`. Both the text label and difficulty column are excluded from inputs. The binary target maps `normal` to 0 and every attack label to 1. No external data was collected for the current experiment.

## 3. Reserve test data and split development data

The saved detector uses the first fold of `StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)` on KDDTrain+. It hashes all 41 feature values as a group and tries to stratify by the original attack label. Identical feature hashes cannot cross the model-training and validation partitions; hash collision is theoretically possible.

| Partition | Rows | Use |
|---|---:|---|
| Model training, from KDDTrain+ | 100,778 | Fit encoder and classifier |
| Validation, from KDDTrain+ | 25,195 | Select attack-score threshold |
| Supplied KDDTest+ | 22,544 | Exploratory reporting after threshold selection |

The earlier ANN experiments used the full 125,973-row KDDTrain+ as their training set and did not use this validation partition. They share the supplied test file, but the methods and training data differ, so comparison is descriptive rather than a controlled study.

The test file has been inspected during earlier work. Moreover, 664 test rows have feature vectors also present in the full training file. This does not prove the events themselves are duplicates. Use an independent and representative dataset for a stronger final evaluation; do not tune on the current test results.

## 4. Fit preprocessing and train

For the retained model, `OneHotEncoder(handle_unknown="ignore")` fits the categorical features on model-training rows only. Numeric values pass through without scaling. A scikit-learn `HistGradientBoostingClassifier` is trained on the binary target with 200 iterations, learning rate 0.08, maximum 15 leaf nodes, minimum 30 samples per leaf, L2 regularization 2.0, and model seed 42. The pipeline is stored with its feature order and decision threshold in the joblib bundle.

The historical ANN used 122 encoded inputs, 500 sigmoid hidden units and 24 softmax outputs. It used mean log-likelihood, batch size 1,000, learning rate 0.5 and 10 epochs. The paper names regularization but does not specify a method or coefficient; the reproduction omitted it. The ANN is therefore a partial reproduction, not an exact copy of the paper's experimental implementation.

## 5. Select the threshold

The classifier supplies an attack score. On validation rows, the code considers score thresholds, calculates the false-positive rate among normal rows and selects the threshold with highest attack recall subject to **at most 5% empirical validation false positives**. In the saved run the threshold is approximately 0.010879, validation recall 99.99% and validation false-positive rate 2.84%.

The same validation set selects and measures that threshold, so its figures are optimistic. The test false-positive rate was 9.27%; the 5% constraint does not guarantee test or deployment performance. The score is not calibrated as a probability of attack.

## 6. Evaluate and inspect errors

`src.improved_detector` evaluates the frozen model and threshold on the provided test file, saves confusion counts and aggregate metrics, and reports detection recall for each attack name. The saved test result is 87.56% binary accuracy, 85.16% attack recall, 92.39% attack precision and 9.27% normal false-positive rate. It misses 1,905 of 12,833 attacks and raises 900 alarms on 9,711 normal records. Among 3,750 test records with names absent from model training, it flags 2,996 as attacks; this is binary detection, not unknown-class identification.

The aggregate result hides major failures: `guess_passwd` recall is 223/1,231 (18.12%), `snmpgetattack` 0/178, and `snmpguess` 7/331 (2.11%). Small class sizes also make some per-class estimates unreliable.

`src/overlap_diagnostics.py` separately reports subsets with and without feature overlap. The non-overlapping test subset has 84.71% attack recall and 9.12% normal false-positive rate. These remain exploratory measurements, not independent verification. `src/development_comparison.py` compares ordinary boosting, weighted boosting and logistic regression on two grouped development splits only. It does not read the test file, but chooses and assesses each threshold on the same validation fold, so its metrics are optimistic.

## 7. Why the two alternatives were explored

**Class-weighted ANN.** The training data is highly imbalanced, so inverse-frequency class weighting was tested to give rare classes more influence in the objective. The weighted model kept the ANN's known attack-name outputs. Its recorded binary recall increased, but its false-alarm rate was much higher. Weights reached thousands for classes with only a few examples and the training objective fluctuated. Neither ANN had positive examples for its reserved unknown output, so neither learned an unknown-attack classifier.

**Gradient boosting.** The decision-tree ensemble was explored as an alternative for nonlinear patterns in tabular data and as a binary score-based detector. In the recorded comparison it detected more attacks than the two ANN runs, at a false-positive rate between them. It cannot name attacks, its validation target did not hold on test, and its rare-attack detection remains poor. It is the model kept in the repository and used by the demo.

## 8. Historical comparison

The following historical ANN figures are recomputed from the confusion matrices and result JSON at Git commit `394c8f4`. The current boosted values come from `results/grouped_binary_results.json`. Both are exploratory on the same previously inspected test set.

| Test measure | Baseline ANN at `394c8f4` | Weighted ANN at `394c8f4` | Current boosted detector |
|---|---:|---:|---:|
| Binary accuracy | 71.68% | 83.68% | 87.56% |
| Attack recall | 55.58% | 82.82% | 85.16% |
| Normal false-positive rate | 7.04% | 15.19% | 9.27% |
| Exact normal/attack-name accuracy | 68.39% | 68.76% | Not applicable |
| Unseen-label records flagged as attacks | 653 / 3,750 | 2,313 / 3,750 | 2,996 / 3,750 |

The presentation records a subsequent weighted ANN rerun: 83.67% binary accuracy, 82.79% attack recall, 15.17% false-positive rate, 68.77% exact-class accuracy and 2,312/3,750 unseen-label attacks flagged. That rerun differs slightly from the archived commit above. Its model and reports were removed in the later cleanup; the slide is a record of the previously observed rerun, not an assertion that its numbers match commit `394c8f4`.

## 9. Run, validate and maintain

Install the pinned direct dependencies from `requirements.txt` and `pytest`, then use `python -m pytest -q`. Execute `python -m src.improved_detector` to retrain; it overwrites the grouped model and results. It records package versions, data hashes and the model hash. Use only trusted joblib files; serialized model formats can execute code when loaded.

The FastAPI app validates the feature schema, categorical values, nonnegative numeric fields, integer counts, binary indicators and rate ranges. It uses the saved model threshold. Its accuracy display is available only if the result's model hash matches the artifact. Restart the app after replacing the model, because it caches resources. The demo accepts manually entered features; it does not extract them from live packets.

The dependency file pins direct package versions but is not a complete environment lock. Future work should establish independent data, group- or time-aware evaluation appropriate to the data source, repeated splits and seeds, score calibration, robust rare-attack metrics and a validated live feature pipeline. Do not deploy based solely on these benchmark results.
