# Dataset verification

This document describes the files used by the current project. The earlier project record identifies a public NSL-KDD mirror at `https://raw.githubusercontent.com/jmnwong/NSL-KDD-Dataset/master/`. That record is not independent proof of the files' origin, license or suitability for a new use; verify those before redistribution or deployment.

## Files and fields

| File | Records | Fields |
|---|---:|---:|
| `data/KDDTrain+.txt` | 125,973 | 43 |
| `data/KDDTest+.txt` | 22,544 | 43 |

Each record contains **41 features**, a text attack `label`, and a `difficulty` field. The current detector excludes the last two fields from its feature matrix. It turns the label into a binary target: `normal` is normal, every other label is attack. `src/preprocessing.py` is the authoritative ordered schema.

The three categorical input features are `protocol_type`, `service` and `flag`; the remaining 38 are numeric. The encoder fits categorical values on the training partition. It ignores unknown categories in the model pipeline, while the demo currently requires categorical choices from the fitted encoder.

For the full original training file, the category counts are 3 protocols, 70 services and 11 flags. These produce 122 columns when combined with the 38 numeric inputs for the historical ANN. The current boosted pipeline fits its encoder on the development training partition, so its transformed width follows the categories present in that partition.

## Data quality and class distribution

The saved [data audit](results/data_audit.json) reports no missing values or non-finite numeric values in these two files. It reports 16 repeated feature rows in the training file and 57 in the test file. There are 664 test rows whose 41-feature vector occurs in the full training file; this is feature overlap and does not by itself establish event identity or label agreement. Hashes of the files are saved in the audit and model result reports.

The full training file has 67,343 normal records and 58,630 attacks. It contains 22 attack names. The test file has 9,711 normal records and 12,833 attacks, including 17 attack names absent from the full training file, covering 3,750 test rows. Counts by label and observed categorical values are in `results/data_audit.json`.

Some attack types have very few examples. The group-split training script warns that the least-populated label has only two records. A large overall accuracy therefore cannot establish reliable detection of every attack type.

## Split used for the retained model

The saved run splits `KDDTrain+` into **100,778 model-training rows** and **25,195 validation rows** with a group-aware split. Grouping uses a hash of all 41 feature values, so records with the same hash stay together within the development split. The splitter attempts to preserve attack-label distributions but rare labels can be unevenly represented. The 22,544 KDDTest+ records are evaluated separately after selecting the threshold.

The test set has already been examined during development and has feature overlap with the training file. It is therefore not a pristine final holdout. `src/overlap_diagnostics.py` provides a descriptive comparison for test rows with and without overlapping features, not an independent evaluation.

## Relationship to the paper

The supplied paper describes 41 features, three categorical inputs and a 122-input ANN. The raw file also has a difficulty field in addition to the label. The paper describes 22 known training attack types and 17 attack types present only in test; the observed set difference supports those counts. Its table lists 9,710 normal test records, whereas this file contains 9,711, so its table total is one record lower than the supplied file. The cause is not established.

The paper describes a 24th output for other attacks but does not explain how that output obtains positive training examples. The current retained model is binary and does not reproduce that output. The paper also does not specify enough regularization detail for an exact ANN reproduction.

## Reproduce the audit

From the project root, using the configured environment:

```powershell
.\.venv\Scripts\python.exe -m src.data_audit
```

This overwrites `results/data_audit.json`. The script reads the local files; it does not download or independently verify their provenance. For the model training and evaluation procedure, see [MODEL_WORKFLOW.md](MODEL_WORKFLOW.md).
