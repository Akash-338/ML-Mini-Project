# Final Reproduction Audit

## Scope and audit outcome

This audit inspected the preprocessing, model, training, evaluation, and visualization code; the tests; the saved data, model, preprocessing artifacts, and result files; and the dataset and final-results reports. No implementation code was changed, and the model was not retrained.

The complete test suite passed: **5 passed, 0 failed**.

## Component audit

### Dataset

- The expected NSL-KDD files are present: `data/KDDTrain+.txt` and `data/KDDTest+.txt`.
- Preprocessing loads the training and test split separately, uses the first 41 feature fields, and excludes the final `label` and `difficulty` fields from X.
- The audited dataset report records 125,973 training rows and 22,544 test rows, with 43 columns in each raw file: 41 features, label, and difficulty.
- Assessment: **Consistent with the selected NSL-KDD split and the paper's 41-feature description.**

### Preprocessing

- One-hot encoding is applied to `protocol_type`, `service`, and `flag`.
- The encoder is fit on training categorical data and used to transform test data.
- The scaler is fit on the 38 numerical training features and used to transform test data.
- Resulting feature width is 122 (38 + 3 + 70 + 11); labels are encoded as 24 columns.
- The label mapping puts normal at 0, the sorted 22 training attack labels at 1–22, and `"other"` at 23. Unknown test labels are mapped to 23.
- Important distinction: every training label is normal or one of the 22 known attacks. Consequently, training data contains **zero positive examples for class 23**.
- Assessment: feature pipeline matches the requested shape and train-only fitting; the 24th output category cannot be learned from a positive training example in this dataset setup.

### Model

- The inspected model has two linear layers, 122 → 500 and 500 → 24, with sigmoid after the first and softmax after the second.
- No other network layers or architectural modifications are present.
- Assessment: **Matches the requested architecture.**

### Training

- Code constants specify learning rate 0.5, batch size 1,000, and 10 epochs. The last batch is smaller where required.
- The code manually adds the gradient of mean softmax log-likelihood to parameters, i.e. performs gradient ascent without a descent optimizer.
- No Adam, RMSprop, momentum, schedule, or explicit regularizer is used.
- A seed parameter defaults to 42, and Python, NumPy, and Torch RNG seeds are set. The paper does not specify a seed. The actual run used the default when `python -m src.train` was executed; the seed is not written into the training-history CSV or evaluation JSON.
- The paper calls its method regularized, but provides no regularizer or coefficient. The implementation leaves regularization unapplied rather than inventing either.
- Assessment: **Partial** reproduction of the stated optimization because regularization could not be reproduced from the available paper details.

### Evaluation and results

- Evaluation computes train and test multiclass accuracy by argmax over the 24 softmax probabilities.
- It also computes train and test normal-versus-abnormal accuracy, grouping class 0 as normal and classes 1–23 as abnormal.
- It saves the requested 24-class classification report, confusion matrix, main accuracies, and unknown/other diagnostic.
- Confusion-matrix dimensions are 24 × 24; its cell total is 22,544 and its diagonal sum is 15,418, consistent with saved test multiclass accuracy.
- Saved metrics cross-check as follows:
  - Training multiclass: 122,399 / 125,973 = **97.1629%**
  - Test multiclass: 15,418 / 22,544 = **68.3907%**
  - Training normal-vs-abnormal: 122,705 / 125,973 = **97.4058%**
  - Test normal-vs-abnormal: 16,159 / 22,544 = **71.6776%**
  - Unknown/other test rows: 3,750; predicted as class 23: 0
- Per-class metrics and unknown/other accuracy are explicitly described as additional diagnostics, not metrics defined by the paper.
- Assessment: requested evaluation artifacts exist and are internally consistent. The paper's report is approximate, so numerical proximity does not prove an identical experiment.

### Reproducibility and generated artifacts

- The saved state dictionary loads successfully into the declared ANN.
- The saved preprocessing pickle loads successfully and contains the encoder, scaler, feature lists, and label mapping.
- The training history, evaluation JSON, classification report, confusion matrix, and requested visualization files are present.
- Evaluation now loads the persisted encoder, scaler, feature ordering, and label mapping, then transforms both splits without refitting preprocessing. This reuse is covered by a regression test that makes encoder/scaler `fit` calls fail during evaluation-data loading.
- The seed default is visible in code, but not persisted in the result artifacts.

## Tests

Command: `pytest -q`

- Passed: **5**
- Failed: **0**

The tests cover preprocessing dimensions and one-hot labels, model dimensions and probability output, a synthetic training pass with saving/loading, evaluation metric/report shapes, and persisted preprocessing artifact reuse. The training test uses synthetic data; the actual full-data training was performed earlier, not during this audit.

## Paper comparison

| Component | Paper | Our implementation | Status |
|-----------|-------|--------------------|--------|
| Dataset | NSL-KDD, with training and test datasets | `KDDTrain+.txt` and `KDDTest+.txt` | MATCH |
| Input features | 41 original features; one-hot processing reported as 122 inputs | 41 fields; three categorical features and 38 numeric fields produce 122 inputs; label and difficulty excluded | MATCH |
| Output classes | 24: normal, 22 training attack types, and other attack | 24 indices; other has no positive training example | PARTIAL |
| Architecture | 122 input, 500 hidden, 24 output | 122 → 500 → 24, two linear layers | MATCH |
| Activation functions | Sigmoid hidden, softmax output | Sigmoid hidden, softmax output | MATCH |
| Learning rate | 0.5 | 0.5 | MATCH |
| Batch size | 1,000 records | 1,000, with a final partial batch | MATCH |
| Epochs | 10 | 10 | MATCH |
| Optimization method | Regularized mini-batch gradient ascent | Manual mini-batch ascent on mean log-likelihood; no regularization applied | PARTIAL |
| Regularization | Described as regularized; type/strength not stated | No regularization applied because its method and coefficient are unspecified | PARTIAL |
| Evaluation metrics | Train/test classification accuracy and normal/abnormal accuracy | Both calculated; additional per-class report, confusion matrix, and unknown diagnostic | PARTIAL |
| Test accuracy | Approximately 70% attack classification accuracy | 68.3907% test multiclass accuracy | PARTIAL |

No item is marked MATCH where paper-specific details are missing or implementation behavior differs from the stated procedure.

## Potential reasons results may differ from the paper

1. The paper does not specify the regularizer or its coefficient. This implementation omits regularization, so it does not fully implement the paper's named “regularized” method.
2. Class 23 (“other/unknown”) has no positive training examples. The network therefore has no supervised examples teaching it when to output class 23; all 3,750 test rows mapped to that class were missed in this run.
3. The paper does not provide the exact initialization scheme or random seed. This implementation uses framework-default initialization and a configurable seed whose default is 42.
4. The paper does not define the exact objective expression or class-selection rule. The implementation uses mean softmax log-likelihood and argmax, respectively.
5. The implementation assigns attack class IDs by alphabetically sorting training labels. The paper describes class counts but does not specify their index ordering.
6. The paper's scaling statement does not identify a precise scaler formula. The implementation uses scikit-learn `StandardScaler` on numeric features only.
7. The preprocessing artifact was created in an earlier preprocessing/training run; changing data or preprocessing-library versions would require regenerating and versioning the artifact to reproduce that transformation exactly.
8. The paper reports approximate metrics and notes variation across random initializations; the available information is insufficient to recreate a specific run exactly.

## Viva/presentation points

- Explain that the standard raw files have 43 columns: 41 features, label, and difficulty; only the 41 original features enter X.
- Show the dimensional calculation: 38 numeric features plus 3 protocol values, 70 service values, and 11 flag values equals 122.
- Clarify that class 23 is a reserved unknown label in evaluation and has no positive training examples in the chosen training split; it is not a learned unknown-attack detector in this implementation.
- Distinguish mean log-likelihood (the maximized objective, negative in the saved history) from positive cross-entropy loss.
- Disclose that the paper's regularization is not reproduced because its form and coefficient are absent; do not describe the training as fully identical to the paper.
- Identify seed 42 as this implementation's default choice, not a paper-specified value.
- Explain why 68.3907% being close to approximately 70% is only numerical similarity and not evidence of exact reproduction.
- Note that the binary normal/abnormal accuracy is distinct from multiclass attack-type accuracy.

## Final audit status

**ISSUES FOUND**

### IMPORTANT

- **Regularization deviation:** The paper states regularized mini-batch gradient ascent, but this implementation uses unregularized ascent because the paper does not identify the regularizer or coefficient.
- **Unknown class has no positive training examples:** Class 23 is assigned only to unseen test labels. This run classified 0 of 3,750 such samples as class 23; do not present this as a functioning learned unknown-class detector.

### MINOR

- **Run metadata is incomplete:** Seed default 42 is in code, but the selected seed is not recorded with history/results. The paper provides no seed for comparison.
- **Unspecified mapping/transform details:** Alphabetical class indexing and the exact StandardScaler implementation are implementation choices not identified in the paper.
- **Reported metrics are approximate in the paper:** Direct equivalence cannot be established from the paper's reported values and unspecified details.

The preprocessing-artifact reuse issue listed in the original audit was fixed in Step 11: evaluation now transforms records with the saved training-fitted encoder and scaler, and rerun metrics/reports were byte-for-byte unchanged.
