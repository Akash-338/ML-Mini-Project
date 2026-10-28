# Step 12: Paper Investigation

## Scope

This is an investigation of the two outstanding reproduction issues using the research paper as the source for what the authors specified. No implementation, model weights, or results were changed.

## 1. Regularization evidence

In Section 4.2, the paper states that the model was trained with a “Regularized Mini-Batch gradient ascent algorithm,” learning rate 0.5, batches of 1,000 records, and 10 epochs. The paper adds that these parameters were selected after several tests.

The paper does not provide a mathematical definition of “regularized” in the method description. A search of the complete paper found no specification of:

- an L1 or L2 penalty;
- weight decay;
- a penalty term or regularized objective;
- a regularization coefficient such as λ;
- a gradient equation or update rule;
- an objective/loss function; or
- algorithm steps that determine how regularization is applied.

The word “Regularized” in the optimizer name is the only explicit regularization evidence. The paper does not provide enough information to reproduce regularization mathematically.

**Conclusion:** The optimizer name and listed learning parameters can be reported, but the regularization component cannot be reproduced faithfully from the paper. Selecting a penalty or coefficient would add an unsupported methodological choice.

## 2. Class-23 / unknown-attack evidence

### What the paper says about labels

Section 4.1 describes a 24-column target array:

- one column for normal system behavior;
- 22 columns for known attacks, specifically attacks in the training dataset; and
- a final column for “any other attack.”

It says that this final column is intended to deal with unknown attacks, including the 17 new attacks in the test set that are not mentioned in the training dataset. The dataset discussion says the training set has 22 attack types, whereas the test set has 37 attack types, including 17 new ones.

### What the paper does not explain

The paper does not describe:

- any positive training records or target labels for the “any other attack” output;
- synthesizing or collecting unknown-attack training examples;
- mapping any of the 22 training attacks to the additional output;
- a threshold or rejection rule;
- an open-set recognition procedure;
- clustering or a separate novelty detector; or
- another special training procedure for the unknown output.

The paper describes a 24-output neural network and a softmax output, but it does not explain how an unknown attack can be learned as a supervised class when the described training set contains only normal behavior and the 22 known attack types.

### Consequence for the described supervised setup

In the current project’s label construction, class 23 has zero positive training examples: unseen test labels are mapped to 23, but the training labels consist of normal plus the 22 known attacks. A softmax network can produce a probability for output 23, but, if trained only against those observed training targets, it receives no positive target signal teaching it what an “other/unknown” example looks like. Under the usual supervised likelihood objective, that output is not trained as a positive unknown class.

Therefore, class 23 can be reproduced as a reserved output and as a mapping destination for unseen test labels. A trained unknown-attack detector for that class cannot be reproduced faithfully from the paper’s described data and method: the paper does not say where its positive training examples or any alternative unknown-detection mechanism come from.

This conclusion does not assert that the paper's implementation definitely lacked such a mechanism; it records that the paper does not specify one.

## 3. What the paper explicitly specifies

- Training includes normal behavior and 22 attack types.
- Test data contains 37 attack types, including 17 new attacks not in training.
- The target array has 24 columns: normal, 22 training-known attacks, and one “any other attack” column.
- The additional column is intended to deal with unknown attacks.
- The network has 122 input units, 500 hidden units, and 24 output units.
- The hidden activation is sigmoid; the output activation is softmax.
- The named training method is “Regularized Mini-Batch gradient ascent.”
- The listed learning rate, batch size, and epoch count are 0.5, 1,000 records, and 10 epochs.

## 4. What the paper leaves unspecified

- Regularizer type, formula, coefficient, and application to weights or biases.
- Objective/loss function and gradient/update equations.
- How an “any other attack” target is generated for training, if any.
- How the unknown output is intended to acquire a positive training signal.
- Any thresholding, rejection, novelty-detection, or special unknown-class procedure.

## 5. Faithful reproducibility assessment

- **Regularization:** Not faithfully reproducible from the paper. The paper names regularization but omits the mathematical details required to implement it.
- **Unknown class:** The 24-column label layout and mapping unseen test labels to its final column are reproducible. Training a meaningful classifier for that column is not faithfully reproducible from the described training data and paper details because no positive examples or alternative mechanism are specified.

## 6. Recommended decision for the project

- Reproduce exactly what the paper explicitly specifies.
- Do not invent a regularizer, coefficient, unknown-class training data, threshold, rejection rule, or novelty-detection method.
- Clearly document the unavoidable limitations: regularization is named but mathematically undefined, and the unknown output is described without a specified way to train it.
- Keep the reserved “other/unknown” output and test-label mapping distinguishable from claims that the model has learned to detect unknown attacks.

STEP 12 STATUS: COMPLETE

## Summary

| Issue | Paper provides enough information? | Can reproduce faithfully? | Action recommended |
|---|---|---|---|
| Regularization method | No. The paper names a “Regularized” method but gives no penalty, coefficient, objective, or update equation. | No, not for the regularization component. | Do not invent a regularizer; document that only the named mini-batch gradient-ascent method and stated parameters are known. |
| Class 23 / unknown attacks | Partially. The paper specifies an additional “any other attack” output intended for unknown test attacks, but does not say how it obtains training examples or learns that output. | The reserved output and unseen-label mapping can be reproduced; learning an unknown-attack class cannot be confirmed or faithfully reproduced from the description. | Preserve the distinction; document the absence of a specified unknown-class training/rejection method and do not claim learned unknown detection. |
