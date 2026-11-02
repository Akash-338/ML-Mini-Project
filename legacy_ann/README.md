# Historical ANN experiments

This folder restores the paper-based baseline ANN and class-weighted ANN code from Git commit `394c8f4`. Only package import paths and the dataset directory were adjusted so these experiments run independently of the current boosted detector. The model architecture and historical training procedures were not changed.

The baseline uses 122 inputs, 500 sigmoid hidden units and 24 softmax outputs. The weighted ANN uses the same architecture with inverse-frequency class weights. The reserved unknown class has no positive training examples; neither ANN learns a reliable unknown-attack detector. The paper does not specify enough details for an exact reproduction. These historical experiments use the full training file without a separate validation split, and their previously inspected test results are exploratory.

## Install and run

Install the current project requirements and PyTorch in the same virtual environment. The historical experiments were verified with `torch==2.14.1+cpu`; install a compatible PyTorch build for your system.

```powershell
.\.venv-new\Scripts\python.exe -m pip install -r requirements.txt torch
.\.venv-new\Scripts\python.exe -m legacy_ann.src.train
.\.venv-new\Scripts\python.exe -m legacy_ann.src.evaluate
.\.venv-new\Scripts\python.exe -m legacy_ann.src.train_proposed
.\.venv-new\Scripts\python.exe -m legacy_ann.src.evaluate_proposed
```

Run the baseline training first, because it fits and saves the preprocessing objects used by both ANNs. The scripts read `../data/` and write generated models and evaluation files into `legacy_ann/models/` and `legacy_ann/results/`, which are ignored by Git. Re-running commands overwrites files in those folders. These scripts do not overwrite the current boosted detector. Historical saved results and limitations are documented in [MODEL_COMPARISON.md](../MODEL_COMPARISON.md).
