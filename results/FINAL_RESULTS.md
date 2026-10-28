# Final Experiment Results

## 1. Dataset

- Dataset: NSL-KDD
- Training file: `data/KDDTrain+.txt` — 125,973 samples
- Test file: `data/KDDTest+.txt` — 22,544 samples
- Files use 41 original features, a label column, and a difficulty column.
- The difficulty column was excluded from model inputs.

## 2. Preprocessing

- Excluded `label` and `difficulty` from the feature matrix.
- One-hot encoded `protocol_type`, `service`, and `flag`.
- Fit the encoder on training data only and applied it to test data.
- Standardized the 38 numerical features using a scaler fit on training data only.
- Feature matrices contain 122 columns: 38 numeric + 3 protocol type + 70 service + 11 flag.
- Labels use 24 output classes: normal (0), 22 training attack labels (1–22), and other/unknown (23).
- Test labels absent from training were mapped to class 23.
- Evaluation loads the persisted training-fitted encoder and scaler and applies them to both train and test data; it does not refit preprocessing.

## 3. Model architecture

- Feedforward ANN: **122 → 500 → 24**
- Hidden activation: sigmoid
- Output activation: softmax

## 4. Training configuration

- Learning rate: 0.5
- Mini-batch size: 1,000 (final partial batch: 973)
- Epochs: 10
- Training objective: mean softmax log-likelihood, optimized with manual gradient ascent.
- Seed 42 is this implementation's configurable default and was used for the saved run; the paper does not specify a random seed.
- The paper describes regularized mini-batch gradient ascent but does not specify a regularization method or coefficient. No regularizer was added because those details are unavailable.
- Class 23 ("other/unknown") has no positive training examples in the selected training split. Mapping unseen test labels to this class does not make it a learned unknown-attack detector.

## 5. Training results

- Final training objective (mean log-likelihood): **-0.085459**
- Training multiclass accuracy: **97.1629%** (122,399 / 125,973)
- Training normal-vs-abnormal accuracy: **97.4058%** (122,705 / 125,973)

Training objective and training accuracy by epoch are plotted in `training_loss.png` and `training_accuracy.png`.

## 6. Test results

- Test multiclass accuracy: **68.3907%** (15,418 / 22,544)
- `Our test multiclass accuracy of 68.3907% is close to the paper's reported approximately 70% test accuracy.`
- This closeness is not proof of exact reproduction.

## 7. Normal-vs-abnormal results

- Training: **97.4058%** (122,705 / 125,973)
- Test: **71.6776%** (16,159 / 22,544)

## 8. Unknown/other attack diagnostic

This diagnostic is additional; the paper does not define this per-class metric.

- Test samples mapped to class 23 (other/unknown): **3,750**
- Correctly predicted as class 23: **0**
- Class-23 diagnostic accuracy: **0.0000%**

## 9. Comparison with the research paper

### PAPER:

- Training attack-class accuracy: almost 100%.
- Test attack-class accuracy: approximately 70%.
- Normal-vs-abnormal system accuracy: approximately 80%.
- Some runs reportedly exceeded 85% test accuracy; the paper describes variation across runs.

### OUR IMPLEMENTATION:

- Training multiclass accuracy: **97.1629%**
- Test multiclass accuracy: **68.3907%**
- Training normal-vs-abnormal accuracy: **97.4058%**
- Test normal-vs-abnormal accuracy: **71.6776%**

The test multiclass result is numerically close to the paper's approximate value, but this does not establish exact reproduction. The paper reports approximate values and does not provide enough implementation detail to establish that training and preprocessing are identical.

## 10. Important reproduction limitations

- The paper does not specify the random seed; this implementation exposes a configurable seed.
- The paper does not specify the exact regularization method or coefficient; regularization was therefore left unspecified and not applied.
- The paper does not specify weight/bias initialization; the ANN uses the framework's standard/default initialization.
- The paper does not state the exact objective formula; this implementation uses mean softmax log-likelihood and manual gradient ascent as a mathematically appropriate classification objective.
- The paper does not explicitly give the prediction-to-class rule; this evaluation uses the highest-probability softmax class.
- The paper's approximate reported results and unspecified details mean our measurements should not be described as an exact reproduction.
- Per-class precision, recall, F1-score, support, and the confusion matrix are additional diagnostics beyond the two accuracy measures emphasized by the paper.
