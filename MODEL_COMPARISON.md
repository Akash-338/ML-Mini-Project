# Model comparison and why we used each model

This document compares the paper-based baseline ANN with two alternative experiments on the supplied NSL-KDD data. The current application uses the **group-aware gradient-boosted binary detector**. The two ANN models and their code were removed during project cleanup, but their earlier outputs remain available in Git history.

## Results comparison

The ANN values below are from the saved experiments at Git commit `394c8f4`; the boosted values are from [grouped_binary_results.json](results/grouped_binary_results.json). The table uses the supplied KDDTest+ set (22,544 records).

| Test measure | Baseline ANN | Class-weighted ANN | Group-aware boosted detector |
|---|---:|---:|---:|
| Binary accuracy: normal versus attack | 71.68% | 83.68% | **87.56%** |
| Attack recall: attacks detected as attacks | 55.58% | 82.82% | **85.16%** |
| False-positive rate: normal records flagged as attacks; lower is better | **7.04%** | 15.19% | 9.27% |
| Exact normal/attack-name accuracy | 68.39% | 68.76% | Not applicable |
| Unseen-label records flagged as attacks | 653 / 3,750 | 2,313 / 3,750 | **2,996 / 3,750** |
| Unseen attacks labelled as unknown | 0 / 3,750 | 0 / 3,750 | Not applicable |

The boosted model detected the most attacks in this comparison; the baseline ANN had the fewest false alarms on normal traffic. The weighted ANN improved binary attack recall over the baseline while increasing false alarms. These metrics measure different aspects of performance, so no model is best for every objective.

**Comparison limits:** the ANN experiments trained on all 125,973 KDDTrain+ records without a separate validation split. The retained boosted experiment trained on 100,778 records and used 25,195 for validation. The test set has already been examined during development, and 664 test rows have feature values also present in the full training file. Thus this is an exploratory comparison, not proof of performance on independent live traffic. Flagging a record with an unseen attack label as an attack does not mean identifying the attack as unknown.

The [presentation](presentation/PES_ML_Intrusion_Detection.pptx) uses a later weighted ANN rerun, whose figures differ slightly from the archived commit above. See [MODEL_WORKFLOW.md](MODEL_WORKFLOW.md) for those figures and the full procedure.

## 1. Paper baseline ANN

**Why we used it:** to establish a reference based on the supplied research paper and understand how well its neural-network approach works on the project dataset.

**How it works:** the implementation transforms the 41 original fields into 122 inputs, then uses one hidden layer with 500 sigmoid units and 24 softmax outputs. It uses learning rate 0.5, batch size 1,000 and 10 epochs. The paper names a regularized optimizer but does not specify the regularizer, so the implementation omitted it and is a partial reproduction.

| Advantages | Drawbacks |
|---|---|
| Provides a reference for comparisons with the paper's approach. | Detected only 55.58% of test attacks as attacks in the archived run. |
| Attempts to name known attack types as well as predict normal traffic. | The reserved unknown output had no positive training examples and correctly labelled zero unseen test records as unknown. |
| Had the lowest false-positive rate among these three runs. | The classes are highly imbalanced and some attacks were frequently classified as normal. |

## 2. Class-weighted ANN

**Why we used it:** some attack types have very few training examples. Inverse-frequency weights increase the contribution of rare classes to the training objective, giving the ANN more incentive to learn them.

**How it works:** it uses the baseline network architecture and training configuration, but weights each training example according to its attack-class frequency. The absent unknown class has no positive examples and receives no positive training signal.

| Advantages | Drawbacks |
|---|---|
| Increased binary attack recall from 55.58% to 82.82% in the archived runs. | False positives rose from 7.04% to 15.19% of normal test records. |
| Retains predictions for individual known attack types. | Very large weights for classes with only a few examples can make training unstable. |
| Provides a direct experiment on the effects of class imbalance. | It did not learn to label unseen attacks as unknown. |

## 3. Group-aware gradient-boosted detector

**Why we used it:** gradient-boosted trees can learn nonlinear patterns in tabular data. The project's immediate goal was to distinguish normal traffic from attacks while examining the trade-off between missed attacks and false alarms.

**How it works:** the model fits a categorical encoder and histogram gradient-boosted classifier on a training partition. Identical feature hashes are grouped during the development split. A threshold is chosen on validation data to maximize attack recall under an empirical 5% false-positive constraint. The saved threshold is then applied to test records.

| Advantages | Drawbacks |
|---|---|
| Achieved the highest binary attack recall and accuracy in the recorded comparison. | It predicts normal or attack only; it does not name the attack or identify it as unknown. |
| Its validation threshold explicitly considers false alarms. | The 5% validation target did not hold on test: the observed test false-positive rate was 9.27%. |
| Saved preprocessing, model and threshold are bundled together. | Some attacks remain poorly detected: `guess_passwd` 223/1,231, `snmpgetattack` 0/178 and `snmpguess` 7/331. |

## Data split for the retained detector

| Dataset partition | Records | Purpose |
|---|---:|---|
| Model training, from KDDTrain+ | 100,778 | Fit the encoder and classifier |
| Validation, from KDDTrain+ | 25,195 | Choose the attack-score threshold |
| KDDTest+ | 22,544 | Report exploratory test results after threshold selection |

The score has not been calibrated as a probability. The same validation partition selects and assesses the threshold, and the test set is not a pristine final holdout. Further work requires an independent, representative dataset, repeated group-aware evaluations, and improved detection for rare attack types before deployment is considered.

## Sources in this project

- [Current model evaluation](results/grouped_binary_results.json) and [data audit](results/data_audit.json).
- Historical ANN results and confusion matrices in Git commit `394c8f4` under `results/`.
- Supplied paper: [Using Neural Network for Security Attacks Detection](reference/81970400.pdf).
- [Complete model workflow](MODEL_WORKFLOW.md) and [dataset verification](DATASET_VERIFICATION.md).
