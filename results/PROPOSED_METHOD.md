# Proposed Method: Class-Weighted ANN

## Research hypothesis

Class-imbalance-aware training may improve minority-class detection compared with the frozen baseline ANN. This is a hypothesis to evaluate; this document does not claim an improvement.

## Baseline method

The baseline is the existing 122 → 500 → 24 ANN with a Sigmoid hidden activation and Softmax output. It uses the existing 122-feature NSL-KDD preprocessing, a 24-class label mapping, manual mini-batch gradient ascent, learning rate 0.5, batch size 1,000, 10 epochs, and seed 42. Its saved model and result files are not overwritten by this experiment.

## Proposed method

The proposed experiment uses the same ANN architecture, saved preprocessing artifact, dataset split, label mapping, input ordering, training order, seed, learning rate, batch size, epochs, and manual gradient-ascent update as the baseline. The intended change is the weighted log-likelihood objective only:

```text
weight_c = N / (K_positive * count_c)
weighted_objective = mean(weight_y * log(p_y))
```

Here `N` is the number of training samples, `K_positive` is the number of classes with at least one training example, and `count_c` is the training count for class `c`. Classes with positive counts receive the inverse-frequency weight above. The weights sum to an average per-sample weight of 1 over training labels.

Class 23 (`other/unknown`) has zero training examples. It is assigned a weight of exactly 0 and is never included in the inverse-frequency division. No arbitrary weight is assigned, and no test labels are used to calculate weights.

## What is unchanged

- Baseline ANN architecture and saved weights
- Saved preprocessing encoder/scaler and feature ordering
- Dataset train/test split and label mapping
- Learning rate 0.5, batch size 1,000, 10 epochs, seed 42
- Manual mini-batch gradient-ascent update
- Baseline evaluation JSON, report, and confusion matrix

## What changes

Only the sample contribution to the training objective is multiplied by the weight associated with its ground-truth training class. The weighted model is saved separately.

## Output files

- `models/proposed_ann_model.pth` — proposed model weights
- `results/proposed_training_history.csv` — epoch, weighted objective, loss, accuracy
- `results/class_weights.csv` — class ID/name, training count, computed weight
- `results/proposed_evaluation_results.json` — training/test metrics
- `results/proposed_classification_report.csv` — per-class report for both splits
- `results/proposed_confusion_matrix.csv` — proposed test confusion matrix

Run the experiment from the project root:

```powershell
python -m src.train_proposed
python -m src.evaluate_proposed
```

The scripts load the persisted preprocessing objects and transform the dataset without fitting or saving any preprocessing object.
