# Intrusion detection: end-to-end ML workflow

## 1. Define the problem
The improved model is a binary traffic classifier: detect attack versus normal. Report attack recall, false-positive rate and precision together. A 5% validation false-positive-rate target is an experimental operating point, not a production guarantee. Classifying attack types and detecting novel attack families are separate tasks.

## 2. Collect and document data
The project uses the existing NSL-KDD KDDTrain+ and KDDTest+ files, 125,973 and 22,544 rows. The existing DATASET_VERIFICATION.md records a public mirror; the new data audit records SHA-256 hashes. Dataset origin, licensing and suitability for a specific deployment require separate verification. No new external traffic was collected.

## 3. Audit and understand data
Run `python -m src.data_audit` to write results/data_audit.json. The audit reports labels, missing/nonfinite numeric values, categorical values, duplicates and cross-split feature overlap. It finds 17 attack names absent from training and 3,750 corresponding test rows. 664 test rows have identical 41-feature vectors in training; this does not prove the underlying network events are duplicates. Inspect label counts and class-wise metrics, especially rare classes.

## 4. Split before fitting transformations
The current improved experiment splits KDDTrain+ 80/20 by attack label using seed 42. KDDTest+ is evaluated separately, but has been inspected before and is not an untouched final holdout. Six validation rows have feature vectors present in the training partition; ideally use group-aware splitting for duplicate feature vectors and repeat experiments across splits. An additional independent dataset is needed for a stronger generalization claim. Temporal, host or network-group splits should be used when the source data supports them.

## 5. Transform features
Drop label and difficulty from inputs. The improved model fits one-hot encoding only on the training partition, ignores previously unseen categorical values, and passes numerical features to a tree-based model without scaling. Its fitted preprocessing and estimator are stored together. This differs from the baseline ANN, which uses standardized numeric features.

## 6. Train and select
The improved experiment fits histogram gradient boosting on the training partition. Its chosen hyperparameters are an initial experiment, not a validation search or proof of an optimal model. Select a binary score threshold on validation data to maximize attack recall under a 5% empirical normal false-positive-rate constraint. Avoid fitting to the test set. Assess multiple seeds and use a separate calibration/selection procedure before final selection.

## 7. Evaluate
Report confusion counts, attack recall, attack precision, false-positive rate, accuracy, ROC AUC, average precision, and recall by attack label. Separate known from unseen attack labels. The existing improved results are exploratory: 90.84% binary accuracy, 88.26% attack recall, 5.75% normal false-positive rate, and 82.24% binary attack recall on the 3,750 unseen-label rows. These do not show that the model identifies which attacks are unknown. Test-set use in prior experimentation and feature overlaps limit the strength of the comparison.

## 8. Package and monitor
The saved joblib bundle contains the estimator, preprocessing, feature ordering and threshold; loading serialized models must be restricted to trusted artifacts. Validate feature schema and permissible ranges before production use. Integrate the new detector into the demo only after evaluating it; the current app uses the baseline ANN. Monitor feature drift, attack recall, false alerts, latency and feedback on representative data. Do not deploy on the strength of this benchmark alone.

## 9. Reproduce
Activate the working environment or invoke `.venv-new/Scripts/python.exe` directly. Run `python -m src.data_audit`, `python -m pytest -q`, then `python -m src.improved_detector`. The last command overwrites the separate improved model and results; it does not overwrite the paper baseline. Record environment versions and hashes, already included in the improved results. Pin a tested environment before sharing.

## Remaining work
- Group-aware validation, repeated seeds and comparisons with simple baselines.
- Hold out attack families during development to evaluate novelty robustness without using the final test for selection.
- Validate threshold stability and score calibration; define an operational false-alarm budget.
- Independently collected or otherwise independent test data and representative modern traffic.
- Attack-family or multiclass analysis, input validation, and optional demo integration.
- Presentation only after user confirmation.
