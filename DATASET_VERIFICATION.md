# Dataset Verification Report

## A. Dataset source
- Source used: public NSL-KDD dataset mirror on GitHub
- Standard files downloaded:
  - `data/KDDTrain+.txt`
  - `data/KDDTest+.txt`
- Source URL used for download: `https://raw.githubusercontent.com/jmnwong/NSL-KDD-Dataset/master/`

## B. File names
- Training dataset: `data/KDDTrain+.txt`
- Test dataset: `data/KDDTest+.txt`

## C. Dataset dimensions
- `KDDTrain+.txt`: 125,973 rows x 43 columns
- `KDDTest+.txt`: 22,544 rows x 43 columns
- Dataset shows: the standard NSL-KDD files contain 43 columns total.
- Paper says: the dataset has 41 features and the final label is separated from them.
- Status: Match for the 41-feature concept; the dataset file includes an extra `difficulty` column as part of the standard NSL-KDD format.

## D. Original 41 features
- Standard NSL-KDD column list observed in the selected files (excluding the final label and difficulty columns):
  - `duration`
  - `protocol_type`
  - `service`
  - `flag`
  - `src_bytes`
  - `dst_bytes`
  - `land`
  - `wrong_fragment`
  - `urgent`
  - `hot`
  - `num_failed_logins`
  - `logged_in`
  - `num_compromised`
  - `root_shell`
  - `su_attempted`
  - `num_root`
  - `num_file_creations`
  - `num_shells`
  - `num_access_files`
  - `num_outbound_cmds`
  - `is_host_login`
  - `is_guest_login`
  - `count`
  - `srv_count`
  - `serror_rate`
  - `srv_serror_rate`
  - `rerror_rate`
  - `srv_rerror_rate`
  - `same_srv_rate`
  - `diff_srv_rate`
  - `srv_diff_host_rate`
  - `dst_host_count`
  - `dst_host_srv_count`
  - `dst_host_same_srv_rate`
  - `dst_host_diff_srv_rate`
  - `dst_host_same_src_port_rate`
  - `dst_host_srv_diff_host_rate`
  - `dst_host_serror_rate`
  - `dst_host_srv_serror_rate`
  - `dst_host_rerror_rate`
  - `dst_host_srv_rerror_rate`
- Observed dataset structure:
  - 41 original feature columns
  - 1 label column
  - 1 difficulty column
- Paper says: there are 41 features and one label column.
- Dataset shows: 41 features + label + difficulty = 43 columns total.
- Status: Match for the feature count; the paper omits the difficulty column from the feature discussion, which is consistent with it being an auxiliary field rather than an input feature.

## E. Categorical feature analysis
- Categorical columns observed in the standard NSL-KDD text files:
  - `protocol_type`
  - `service`
  - `flag`
  - `label`
- Data type check:
  - numeric fields: integer/float numeric columns
  - categorical fields: protocol_type, service, flag, label are string-like categorical columns
- Unique values observed:
  - `protocol_type`:
    - Training: 3 unique values (`icmp`, `tcp`, `udp`)
    - Test: 3 unique values (`icmp`, `tcp`, `udp`)
  - `service`:
    - Training: 70 unique values
    - Test: 64 unique values
  - `flag`:
    - Training: 11 unique values
    - Test: 11 unique values
  - `label`:
    - Training: 23 unique labels
    - Test: 38 unique labels
- Paper says: the values of three of the original features come from a controlled set of terms, which are handled by one-hot encoding.
- Dataset shows: `protocol_type`, `service`, and `flag` are exactly the categorical features with controlled values.
- Status: Match.

## F. Label analysis
- Label column name: `label`
- Training labels:
  - 23 unique labels
  - includes `normal` and 22 attack classes
- Test labels:
  - 38 unique labels
  - includes many attack classes not present in the training set
- Dataset shows there are more unique labels in the test set than the train set, consistent with the paper's statement that the test set contains new/unknown attacks.
- Paper says: the training set contains 22 attack types and the test set contains 37 attack types, with 17 of them new.
- Dataset shows: the raw files contain 23 unique training labels and 38 unique test labels, which is consistent with the paper's discussion of known and unknown attacks.
- Status: Match.

## G. Class distribution

### Training set (`KDDTrain+.txt`)
- Total rows: 125,973
- Top labels:
  - `normal`: 67,343
  - `neptune`: 41,214
  - `satan`: 3,633
  - `ipsweep`: 3,599
  - `portsweep`: 2,931
  - `smurf`: 2,646
  - `nmap`: 1,493
  - `back`: 956
  - `teardrop`: 892
  - `warezclient`: 890
- Total distinct labels: 23

### Test set (`KDDTest+.txt`)
- Total rows: 22,544
- Top labels:
  - `normal`: 9,711
  - `neptune`: 4,657
  - `guess_passwd`: 1,231
  - `mscan`: 996
  - `warezmaster`: 944
  - `apache2`: 737
  - `satan`: 735
  - `processtable`: 685
  - `smurf`: 665
  - `back`: 359
- Total distinct labels: 38

## H. Comparison with the paper
- Paper says: there are 41 original input features before preprocessing.
- Dataset shows: 41 feature columns are present, followed by `label` and `difficulty`.
- Status: Match.

- Paper says: the model uses one-hot encoding on categorical features and ends up with 122 inputs.
- Dataset shows:
  - numeric feature count = 38
  - categorical feature counts = `protocol_type` (3) + `service` (70) + `flag` (11)
  - one-hot encoded total = 38 + 3 + 70 + 11 = 122
- Status: Match.

- Paper says: the labels are represented as 24 output classes.
- Dataset shows:
  - training labels include normal + 22 known attack classes = 23 unique labels
  - the paper describes a 24th output class for any other attack / unknown attack
- Status: Match to the paper's conceptual explanation, with the raw dataset itself not containing a literal 24th label column in the input files.

- Paper says: the dataset contains a difficulty-related field.
- Dataset shows: `difficulty` is present in the standard NSL-KDD files.
- Status: Match.

- Paper says: 17 test-set attacks are new and do not appear in the training data.
- Dataset shows: the test set has 38 unique labels while the training set has 23, which is consistent with unseen attack classes being present in the test set.
- Status: Match.

## I. Any discrepancies or unresolved issues
- Paper says: the model output has 24 classes.
- Dataset shows: raw label files do not contain a literal 24-class label encoding; instead, the dataset stores attack names as string labels, and the paper’s 24-class encoding is a modeling decision made after preprocessing.
- Status: Unclear from the raw files alone; matches the paper’s methodology only after the authors explicitly construct the label matrix.

- Paper says: the model excludes the label column from X.
- Dataset shows: the raw data includes a `label` column at the end, and a `difficulty` column is also present.
- Status: Match for the intended modeling setup, but the raw files themselves contain both of these columns.

- Paper says: the data is standardized to zero mean and unit variance.
- Dataset shows: no explicit normalization is applied yet at the raw-file stage; this is a preprocessing step to be performed later.
- Status: Not yet applied in the raw dataset; consistent with the paper’s preprocessing plan.

- Paper says: 41 original input features are used before one-hot encoding.
- Dataset shows: the raw files include 41 features plus 2 extra metadata columns (`label`, `difficulty`), so the exact separation between feature set and metadata must be enforced during preprocessing.
- Status: Match, but must be handled carefully in implementation.

## Final assessment
- The selected NSL-KDD files are the standard train/test split and are structurally consistent with the paper.
- The paper’s 122 input feature count is reproducible from the selected files by one-hot encoding the categorical columns `protocol_type`, `service`, and `flag`.
- The `label` column and the `difficulty` column should not both be included in X.
- The `difficulty` column should be treated as metadata, not as part of the 41 model features.

DATASET STATUS:
- Ready for preprocessing
