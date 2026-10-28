# Slide 1 — Title

## Using Neural Network for Security Attacks Detection

- Student: Dhanraj Rathod
- SRN: PES1UG24AM359
- Branch: AIML

# Slide 2 — Problem Statement

- Network intrusion detection from connection records
- Classify normal behavior and known attack types
- Test data also contains attack types not seen during training
- Goal: automated classification to support security monitoring

# Slide 3 — Motivation & Objectives

- **Motivation**
  - Network activity can represent many kinds of attacks
  - Machine learning can learn patterns from labeled records
  - ANNs provide a learned mapping from input features to classes
- **Objectives**
  - Prepare NSL-KDD records for classification
  - Implement and train the specified ANN
  - Measure multiclass and normal-vs-abnormal accuracy
  - Report limitations without claiming exact reproduction

# Slide 4 — Base Paper

### BASE PAPER

- Title: “Using Neural Network for Security Attacks Detection”
- Dataset: NSL-KDD
- ANN: 122 inputs → 500 hidden units → 24 outputs
- Hidden activation: sigmoid; output activation: softmax
- Training: regularized mini-batch gradient ascent
- Paper reports: almost 100% training accuracy; approximately 70% test attack-class accuracy; approximately 80% normal-vs-abnormal accuracy
- Paper also reports run-to-run variation; some runs exceeded 85% test accuracy

# Slide 5 — Dataset

- Dataset: NSL-KDD
- Training: `KDDTrain+.txt` — **125,973** samples
- Test: `KDDTest+.txt` — **22,544** samples
- Raw record fields: 41 original features + label + difficulty
- Training contains 22 attack types across DoS, Probe, R2L, and U2R categories
- Test contains 37 attack types, including 17 not present in training

# Slide 6 — Data Preprocessing

```text
41 original features
        ↓
categorical + numerical separation
        ↓
one-hot encode:
protocol_type = 3
service       = 70
flag          = 11
        +
38 numerical features
        ↓
122 processed features
```

- Encoder and scaler fit on training data only
- Persisted preprocessing artifact used during evaluation
- `label` and `difficulty` excluded from X
- 24 target classes: normal (0), 22 known attacks (1–22), other/unknown (23)
- Class 23 has no positive training examples in this selected setup

# Slide 7 — Proposed / Implemented Architecture

### OUR IMPLEMENTATION

```text
Input: 122
    ↓
Hidden layer: 500
    ↓
Sigmoid
    ↓
Output: 24
    ↓
Softmax
```

- Single hidden layer
- No additional architectural components
- Matches the paper's stated layer sizes and activations

# Slide 8 — Training Methodology

### OUR IMPLEMENTATION

- Manual mini-batch gradient ascent
- Learning rate: **0.5**
- Batch size: **1,000** (final partial batch: 973)
- Epochs: **10**
- Seed **42**: our implementation choice; not specified by the paper
- Paper mentions regularization but gives no form/coefficient
- No regularizer was invented or implemented

# Slide 9 — Evaluation Methodology

1. **Multiclass attack classification**
   - Predicted class = highest-probability softmax output (argmax)
2. **Normal vs abnormal**
   - Class 0 = normal; classes 1–23 = abnormal
3. **Confusion matrix**
   - 24 × 24 test-set class counts
4. **Classification report**
   - Per-class precision, recall, F1-score, support
5. **Unknown/other diagnostic**
   - Count test examples mapped to class 23 and predicted as class 23
   - Additional diagnostic, not a paper-defined metric

# Slide 10 — Results

### OUR IMPLEMENTATION — SAVED RESULTS

- Training multiclass: **97.1629%**
- Test multiclass: **68.3907%**
- Training normal-vs-abnormal: **97.4058%**
- Test normal-vs-abnormal: **71.6776%**
- Unknown/other test samples mapped to class 23: **3,750**
- Correctly predicted as class 23: **0**

# Slide 11 — Results Analysis

- Test multiclass accuracy (**68.3907%**) is close to the paper's approximate **70%**
- Numerical similarity does **not** prove exact reproduction
- Paper reports variation across random initialization
- Regularization is named but its method and coefficient are unspecified
- Class 23 has no positive training examples in this dataset setup
- Multiclass and normal-vs-abnormal accuracy measure different tasks
- Class 23 result is a diagnostic; it is not evidence of a functioning unknown-attack detector

# Slide 12 — Limitations

- Paper does not specify regularization method or coefficient
- Class 23 has no positive training examples
- Paper does not specify a concrete initialization method
- Exact scaling details are not fully specified by the paper
- Alphabetical ordering for known attack class IDs is our implementation choice
- Paper reports approximate results and variation between runs
- These are documented reproduction limitations, not claims of exact reproduction

# Slide 13 — Future Work

### FUTURE WORK — NOT PART OF CURRENT IMPLEMENTATION

- Investigate proper unknown-attack detection
- Evaluate on additional intrusion-detection datasets
- Run explicit, separately reported regularization experiments
- Investigate class-imbalance handling
- Compare with other machine-learning and deep-learning models

# Slide 14 — Conclusion

- ANN implemented with the paper's **122→500→24** architecture
- Preprocessing and evaluation completed on NSL-KDD
- Test multiclass accuracy: **68.3907%**
- Test normal-vs-abnormal accuracy: **71.6776%**
- Regularization and unknown-class limitations documented honestly
- A documented reproduction attempt is complete; exact reproduction is not claimed
