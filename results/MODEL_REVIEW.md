# Model review and grouped-validation experiment

The baseline ANN and class-weighted ANN are preserved as historical experiments. Both have an output for unknown attacks but no positive training examples for it, so neither is a trained unknown-class detector. The weighted ANN's strong inverse-frequency weights and fluctuating training objective make its learning unstable; its test false-positive rate is 15.19%. Neither ANN has validation-based model selection. Avoid calling them production-ready or exact paper reproductions.

The existing gradient-boosted binary model used a random validation split that placed six identical feature vectors in both partitions. `src.improved_detector` now groups identical 41-feature hashes when splitting. It fits encoding only on the training partition and selects the binary threshold on validation; the new model and metrics are stored separately as `models/grouped_binary_detector.joblib` and `results/grouped_binary_results.json`. Prior `improved_binary_*` artifacts remain for comparison. The five-fold stratified-group split warns about rare classes; all attack labels remain represented in the training partition for this run, but rare-label estimates remain unstable.

| Test metric | Previous boosted run | Grouped-validation run |
|---|---:|---:|
| Binary accuracy | 90.84% | 87.56% |
| Attack recall | 88.26% | 85.16% |
| False-positive rate | 5.75% | 9.27% |
| Unseen-label attacks detected as attacks | 3,084 / 3,750 | 2,996 / 3,750 |

These are different models and training partitions; this is not a controlled estimate of the effect of duplicates alone. The 5% false-positive target applies to validation only, not test data. Test data was previously inspected and contains 664 rows with feature vectors also in the original training file; results are exploratory, not a pristine generalization estimate. The grouped model cannot identify unseen attack types. It detects 18.1% of guess_passwd test examples, 0% of snmpgetattack and 2.1% of snmpguess; this remains a serious limitation. No claim is made that the grouped run improved test performance.

Further work: independent data, repeated grouped splits and seeds, validation-only hyperparameter and threshold selection, uncertainty estimates, rare attack data, model calibration and modern traffic validation. The demo continues to use the baseline ANN. Do not deploy based on these results.
