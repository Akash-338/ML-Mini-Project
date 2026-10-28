# 1. Title

# Using Neural Network for Security Attacks Detection

## 2. Abstract

Network intrusion detection is challenging because attacks can take different forms, including attacks not represented in training data. This project implements an artificial neural network (ANN) experiment based on the provided research paper and the NSL-KDD dataset. The standard `KDDTrain+.txt` and `KDDTest+.txt` splits are used. The 41 original input features are prepared by one-hot encoding `protocol_type`, `service`, and `flag`, and standardizing the numeric features; the resulting input has 122 dimensions. The implemented single-hidden-layer ANN has architecture 122→500→24, with sigmoid hidden activation and softmax output.

The saved experiment achieved 97.1629% training and 68.3907% test multiclass accuracy. Normal-vs-abnormal accuracy was 97.4058% on training and 71.6776% on test. Of 3,750 test examples mapped to the reserved other/unknown class, zero were predicted as that class. The paper leaves important details unspecified, including the regularization formula and how the unknown output is trained. Accordingly, the implementation documents its choices and limitations and is not claimed to be an exact reproduction.

## 3. Introduction

Networked software and its data may be targeted by malicious activity. An intrusion detection system aims to identify unauthorized or abnormal system and data behavior. Signature-based detection looks for known attack patterns, while anomaly-based detection looks for deviations from expected behavior; the latter may encounter previously unseen attacks but can also produce false alarms.

Machine learning offers a way to learn patterns from labeled or unlabeled records. Artificial neural networks (ANNs) can model relationships among multiple input features and produce predictions from observed network records. This project implements the ANN architecture described in the supplied paper using NSL-KDD. It reports both attack-type classification and a binary normal-versus-abnormal view, while making clear that an extra softmax output alone does not establish effective detection of unknown attacks.

## 4. Problem Statement

Given a network-connection record represented by NSL-KDD features, classify it as normal behavior or as one of the known attack types. The paper also proposes an additional output category for “any other attack” to account for attacks not present in training. The paper does not explain how that additional class is supplied with positive training examples or how a softmax model should recognize unseen attacks; this remains a limitation of the described and implemented setup.

## 5. Objectives

- Prepare the standard NSL-KDD training and test splits for ANN input.
- Represent the 41 original input features as 122 processed features.
- Implement the paper's 122→500→24 ANN with sigmoid and softmax activations.
- Train using the stated learning rate, batch size, and epoch count, using manual mini-batch gradient ascent.
- Measure multiclass attack classification and normal-versus-abnormal accuracy.
- Report per-class and unknown/other diagnostics without presenting them as paper-defined metrics.
- Document unspecified paper details and avoid claiming exact reproduction.

## 6. Literature / Base Paper

### Base paper

“Using Neural Network for Security Attacks Detection,” identified in the supplied PDF as a CS 229 Final Project—Final Report. The PDF does not clearly specify author names or a publication year.

### Paper's objective and method

The paper's objective is to use a neural network to predict potential security attacks from system/network data, including evaluation on test data with new attack types. It uses NSL-KDD, describing 41 record features and one-hot preprocessing to 122 input columns. Its target array has 24 columns: normal behavior, 22 known training attacks, and a final column for any other attack.

The paper describes a 122-input, 500-hidden-unit, 24-output ANN. It specifies sigmoid for hidden units and softmax for output units. The stated training approach is “Regularized Mini-Batch gradient ascent,” with learning rate 0.5, batches of 1,000 records, and 10 epochs. The paper does not give the regularization formula or coefficient, objective equation, or update equation.

For evaluation, the paper calculates the number of correctly classified records divided by the total, for training and test data. It also evaluates normal-versus-abnormal behavior. The paper reports almost 100% training attack-class accuracy, approximately 70% test attack-class accuracy, and approximately 80% system accuracy for normal-versus-abnormal detection. It notes that some runs exceeded 85% test accuracy and that results varied with random initialization.

The details above summarize the **base paper**. The implementation choices and measured results below are **our implementation**, not claims about hidden details of the paper.

## 7. Dataset

- Dataset: NSL-KDD, described by the base paper as an improved version of KDD Cup 99.
- Training split: `data/KDDTrain+.txt` — 125,973 records.
- Test split: `data/KDDTest+.txt` — 22,544 records.
- Each raw record has 43 columns: 41 original features, `label`, and `difficulty`.
- The `label` field is the target and is excluded from X. The `difficulty` field is also excluded from X.
- The training split contains normal records and 22 attack labels. Those attack types fall under the four broad categories described in the paper: DoS, Probe, R2L, and U2R.
- The test split contains 37 attack types, including 17 attack types not present in training, as described by the paper.

The exact file dimensions and feature inventory are documented in [DATASET_VERIFICATION.md](DATASET_VERIFICATION.md).

## 8. Data Preprocessing

The project uses 41 original input features, excluding `label` and `difficulty` from X.

- Categorical input features: `protocol_type`, `service`, and `flag`.
- One-hot encoding is used for those three input columns.
- The observed training categories expand to 3 protocol values, 70 service values, and 11 flag values.
- The remaining 38 numerical features are standardized with `StandardScaler`.
- Both the one-hot encoder and scaler are fit on training data only. Evaluation loads the persisted training-fitted preprocessing artifact and transforms the training and test splits without refitting.
- The processed input dimension is 38 + 3 + 70 + 11 = **122**.

Target labels are represented with 24 one-hot columns:

- Class 0: `normal`.
- Classes 1–22: the 22 attack labels present in the training split, assigned in alphabetical order by the implementation.
- Class 23: reserved `other/unknown`; test labels absent from training are mapped here.

The selected training split contains no positive examples for class 23. The class is therefore a reserved output/mapping destination, not a successfully learned unknown-attack detector.

## 9. Proposed / Implemented ANN Architecture

The implemented network has one hidden layer and no added architectural components.

```text
Input layer           Hidden layer          Output layer
122 features   →      500 neurons    →      24 classes
                      sigmoid                softmax
```

The framework's default linear-layer initialization is used because the base paper does not specify an initialization method.

## 10. Training Methodology

**Base paper:** “Regularized Mini-Batch gradient ascent,” learning rate 0.5, batch size 1,000, and 10 epochs.

**Our implementation:**

- Performs manual mini-batch gradient ascent on the mean softmax log-likelihood. This is the objective used by our implementation; the paper does not provide an exact objective equation.
- Learning rate: **0.5**.
- Batch size: **1,000** records; the final batch contains 973 records.
- Epochs: **10**.
- Seed: **42** was used as the implementation's configurable default for the saved run. The paper does not specify a seed.
- Training records are consumed in their existing order; the paper does not state a shuffling procedure.

The paper mentions regularization but does not specify its form or coefficient. No regularizer was invented or implemented; therefore, the implementation does not reproduce the regularization component of the paper's named method.

## 11. Evaluation Methodology

### Multiclass attack classification accuracy

The model produces 24 softmax probabilities per record. The predicted class is the highest-probability class. Accuracy is the number of exact class matches divided by the number of records, measured for both training and test splits.

### Normal-vs-abnormal accuracy

Class 0 is treated as normal; classes 1 through 23 are treated as abnormal. Binary accuracy is computed separately on training and test data. This is distinct from exact attack-type classification accuracy.

### Additional diagnostics

- **Confusion matrix:** 24 × 24 test-set matrix of actual versus predicted class counts.
- **Classification report:** per-class precision, recall, F1-score, and support.
- **Unknown/other diagnostic:** the number of test records mapped to class 23 and the number predicted as class 23. This is an additional diagnostic, not a metric explicitly defined by the paper.

## 12. Results

The following are the **actual saved results** from our implementation:

| Measure | Correct / total | Accuracy |
|---|---:|---:|
| Training multiclass attack classification | 122,399 / 125,973 | 97.1629% |
| Test multiclass attack classification | 15,418 / 22,544 | 68.3907% |
| Training normal-vs-abnormal | 122,705 / 125,973 | 97.4058% |
| Test normal-vs-abnormal | 16,159 / 22,544 | 71.6776% |

**Unknown/other additional diagnostic:**

- Test samples mapped to class 23: **3,750**.
- Correctly predicted as class 23: **0**.
- This diagnostic does not establish a functioning learned unknown-attack detector.

Saved outputs include [training history](results/training_history.csv), [evaluation metrics](results/evaluation_results.json), [classification report](results/classification_report.csv), and [confusion matrix](results/confusion_matrix.csv).

## 13. Results Analysis

The **base paper** reports approximately 70% test attack-class accuracy. **Our implementation** obtained 68.3907%, which is numerically close to that approximate value. This similarity does not prove exact reproduction: the paper's reported value is approximate, the paper notes variation across random initializations, and several details needed to reproduce a specific run are not stated.

The base paper reports normal-versus-abnormal accuracy of approximately 80%; our test result is 71.6776%. The metrics are computed for the same broad task, but cannot be assumed to be directly equivalent beyond the described grouping and calculation because details and exact results in the paper are limited.

The paper reports that repeated runs can differ and relates that variation to random parameter initialization. Our implementation uses seed 42 as its own configurable choice; this seed is not specified by the paper. The paper also names regularization without defining it, so our unregularized ascent is a documented limitation rather than a claim of exact optimizer reproduction.

Finally, no training records have class 23 as their target. While the model has a 24th softmax output and unseen test labels are mapped to it, the network has no positive class-23 examples from which to learn that category. In this run, none of the 3,750 class-23 test records was predicted as class 23.

## 14. Limitations

- **Regularization:** its form, coefficient, and application are unspecified in the paper and are not implemented.
- **Unknown class:** class 23 has no positive training examples in this selected dataset setup; it must not be described as a functioning learned unknown-attack detector.
- **Initialization:** the paper says initialization is random in discussing run variation but does not specify a concrete distribution or initialization method. The implementation uses framework defaults.
- **Scaling:** the paper says to make the mean zero and scale to unit variance but does not specify the exact scaler formula or which transformed columns receive scaling. This implementation standardizes the 38 numeric features.
- **Class ordering:** the paper specifies the class meanings but not integer indices for individual attacks. Our implementation sorts training attack labels alphabetically to assign classes 1–22.
- **Objective and prediction rule:** the exact objective equation and class-conversion rule are not stated in the paper. Our implementation uses mean softmax log-likelihood and argmax.
- **Approximate paper results:** the paper's approximate metrics and run-to-run variability make direct exact comparison impossible.
- These limitations mean this project is a documented reproduction attempt, not an exact reproduction.

## 15. Conclusion

This project implements the paper's reported NSL-KDD-based ANN dimensions and activations, and evaluates the saved model using multiclass and normal-versus-abnormal accuracy. The implemented run achieved 68.3907% test multiclass accuracy and 71.6776% test normal-versus-abnormal accuracy. The former is close to the paper's approximate 70% figure, but that does not establish exact reproduction.

The results must be interpreted alongside two substantial paper ambiguities: the undefined regularization method and the lack of a described source of positive examples or other mechanism for the “any other attack” output. We have not invented those missing methods.

## 16. Future Work

Subject to being clearly distinguished from the paper reproduction, realistic future work could:

- investigate and evaluate explicit unknown-attack detection approaches;
- evaluate on additional intrusion-detection datasets;
- conduct clearly labeled regularization experiments;
- investigate class-imbalance handling;
- compare with other machine-learning and deep-learning models.

These are possible extensions and are not part of the current implementation or reported results.

## 17. Reproducibility / How to Run

Run commands from the project root in this order:

1. Preprocessing: `python -m src.preprocessing`
2. Training: `python -m src.train`
3. Evaluation: `python -m src.evaluate`
4. Visualization: `python -m src.visualization`
5. Tests: `pytest -q`

Training calls the preprocessing pipeline and saves the fitted preprocessing artifact and model weights. Evaluation loads the saved encoder/scaler artifact and saved model; it does not retrain or refit preprocessing. Visualization reads saved result files and does not train.

**Caution:** Running training again overwrites the saved model weights and training history. The current report's numbers describe the existing saved experiment, not a newly run experiment.

## 18. References

References below are those listed in the supplied base paper; no additional sources are introduced.

**Base paper:** “Using Neural Network for Security Attacks Detection.” CS 229 Final Project—Final Report, supplied PDF. Author names and year are not clearly specified in the PDF.

[1] Anna L. Buczak and Erhan Guven. “A survey of data mining and machine learning methods for cyber security intrusion detection.” *IEEE Communications Surveys & Tutorials*, 18(2), 2015, pp. 1153–1176.

[2] KDD Cup 1999 Data. http://kdd.ics.uci.edu/databases/kddcup99/kddcup99.html

[3] Jian-hua Li. “Cyber security meets artificial intelligence: a survey.” *Frontiers of Information Technology & Electronic Engineering*, 19(12), 2018, pp. 1462–1474.

[4] Yann LeCun, Yoshua Bengio, and Geoffrey Hinton. “Deep learning.” *Nature*, 521(7553), 2015, pp. 436–444.

[5] M. Tavallaee, E. Bagheri, W. Lu, and A. A. Ghorbani. “A detailed analysis of the KDD CUP 99 data set.” *2009 IEEE Symposium on Computational Intelligence for Security and Defense Applications*, 2009, pp. 1–6. doi:10.1109/CISDA.2009.5356528.

[6] Hany M. Harb et al. “Selecting optimal subset of features for intrusion detection systems.” 2011.
