DVC Pipeline — Stage by Stage
==============================

The pipeline is defined in `dvc.yaml`. Each stage has a command (`cmd`), dependencies (`deps`), parameters (`params`), and outputs (`outs`).

- **cmd** — tells DVC what to execute
- **deps** — tells DVC what to watch for changes (if a dep changes, the stage re-runs)
- **params** — values from `params.yaml` that trigger re-runs when changed
- **outs** — output files tracked by DVC (pushed to S3, not Git)

```bash
dvc repro    # runs all stages that need updating
dvc dag      # visualize the pipeline as a graph
```

---

## Stage 1: Data Ingestion

**File:** `emotional_tweet/dataset.py`

```yaml
cmd: python -m emotional_tweet.dataset
deps: emotional_tweet/dataset.py
params: data_ingestion.test_size
outs: data/raw/
```

What it does:
1. Downloads tweet emotions CSV from GitHub
2. Drops `tweet_id` column
3. Filters to only `happiness` and `sadness` tweets
4. Encodes labels: happiness → 1, sadness → 0
5. Splits into train/test using `test_size` from `params.yaml`
6. Saves to `data/raw/train.csv` and `data/raw/test.csv`

### params.yaml

```yaml
data_ingestion:
  test_size: 0.3    # 30% test, 70% train
```

---

## Stage 2: Data Preprocessing

**File:** `emotional_tweet/data_preprocessing.py`

```yaml
cmd: python -m emotional_tweet.data_preprocessing
deps: data/raw, emotional_tweet/data_preprocessing.py
outs: data/processed/
```

What it does — applies these text transformations in order:

| Step | Function | Example |
|------|----------|---------|
| 1 | `lower_case` | "Happy Day!" → "happy day!" |
| 2 | `remove_stop_words` | "i am very happy" → "happy" |
| 3 | `removing_numbers` | "love2code" → "lovecode" |
| 4 | `removing_punctuations` | "hello!!" → "hello" |
| 5 | `removing_urls` | "check https://t.co/abc" → "check" |
| 6 | `lemmatization` | "running cats" → "running cat" |

Saves to `data/processed/train_processed.csv` and `data/processed/test_processed.csv`.

---

## Stage 3: Feature Engineering

**File:** `emotional_tweet/features.py`

```yaml
cmd: python -m emotional_tweet.features
deps: data/processed, emotional_tweet/features.py
params: feature_engineering.max_features
outs: data/features/
```

What it does:
1. Reads processed train/test CSVs
2. Fills NaN values with empty strings
3. Applies TF-IDF vectorization with `max_features` from `params.yaml`
4. Saves feature matrices to `data/features/train_tfidf.csv` and `data/features/test_tfidf.csv`

### TF-IDF (Term Frequency — Inverse Document Frequency)

```text
TF-IDF = how often a word appears in a document × how rare it is across all documents
```

- Common words (the, is, a) get low scores
- Rare but meaningful words (ecstatic, devastated) get high scores
- `max_features=200` keeps only the top 200 most informative words

### params.yaml

```yaml
feature_engineering:
  max_features: 200
```

---

## Stage 4: Model Building

**File:** `emotional_tweet/modeling/train.py`

```yaml
cmd: python -m emotional_tweet.modeling.train
deps: data/features, emotional_tweet/modeling/train.py
params: model_building (C, penalty, solver)
outs: models/model.pkl
```

What it does:
1. Reads TF-IDF training features
2. Trains a `LogisticRegression` with hyperparameters from `params.yaml`
3. Saves the model as `models/model.pkl` using pickle

### params.yaml

```yaml
model_building:
  C: 1              # inverse regularization strength (higher = less regularization)
  penalty: 'l2'     # L2 regularization
  solver: 'liblinear'  # optimization algorithm
```

---

## Stage 5: Model Evaluation

**File:** `emotional_tweet/modeling/predict.py`

```yaml
cmd: python -m emotional_tweet.modeling.predict
deps: data/features, models/model.pkl, emotional_tweet/modeling/predict.py
metrics: reports/metrics_dict.json (cache: false)
```

What it does:
1. Loads the trained model from pickle
2. Predicts on test data
3. Computes metrics: accuracy, precision, recall, AUC
4. Saves metrics to `reports/metrics_dict.json`
5. Connects to DagsHub MLflow server
6. Logs metrics, model parameters, and model artifact to MLflow
7. Infers model signature (input/output schema) and logs it with the model
8. Saves `model_info.json` with `run_id`, `model_id`, and `model_path` for the registration stage

### What gets logged to MLflow

| Type | What |
|------|------|
| **Metrics** | accuracy, precision, recall, auc |
| **Parameters** | All model hyperparameters via `get_params()` |
| **Model** | sklearn model with signature |
| **Artifacts** | metrics_dict.json, model_info.json |

### Model Signature

```python
signature = infer_signature(X_test, y_pred)
```

This records what the model expects as input (200 float features) and what it outputs (0 or 1). Useful for model serving — MLflow will validate inputs against this schema.

### model_info.json (output)

```json
{
    "run_id": "81cbf48c812c436fa74af5af2103a070",
    "model_id": "m-02fc8358ec3c4fc3a295128092625f71",
    "model_path": "models:/m-02fc8358ec3c4fc3a295128092625f71"
}
```

- `run_id` — the MLflow run this model belongs to
- `model_id` — unique identifier for the logged model (MLflow 3.x)
- `model_path` — URI used to register the model (`models:/{model_id}` format)

---

## Stage 6: Model Registration

**File:** `emotional_tweet/modeling/register_model.py`

```yaml
cmd: python -m emotional_tweet.modeling.register_model
deps: reports/model_info.json, emotional_tweet/modeling/register_model.py
```

What it does:
1. Reads `model_info.json` to get the `model_path` URI
2. Registers the model in MLflow Model Registry under name `"my_model"`
3. Transitions the new version to `"Staging"` stage

### MLflow Model Registry Stages

```text
None → Staging → Production → Archived
```

- **Staging** — model is ready for testing/validation
- **Production** — model is serving live traffic
- **Archived** — retired model, kept for reference

---

## Comparing Metrics Across Runs

```bash
# Show current metrics
dvc metrics show

# Compare metrics between commits
dvc metrics diff
```

---

## Changing Parameters and Re-running

```bash
# 1. Edit params.yaml (e.g., change C from 1 to 10)
# 2. Re-run — DVC only re-runs affected stages
dvc repro

# 3. Compare with previous run
dvc metrics diff
```

DVC tracks which stages depend on which params. If you change `model_building.C`, only `model_building`, `model_evaluation`, and `model_registration` re-run — not data ingestion or preprocessing.
