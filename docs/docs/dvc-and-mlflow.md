DVC & MLflow — How They Work Together
=======================================

## DVC — Data Version Control

DVC manages data and pipeline orchestration. Git tracks code + small pointer files. DVC tracks the actual large files.

```text
Git tracks:    code, dvc.yaml, dvc.lock, params.yaml, .dvc files
DVC tracks:    data/, models/ (stored in .dvc/cache, pushed to remote)
```

### dvc.yaml — Pipeline Definition

```yaml
stages:
  stage_name:
    cmd: python -m module.name       # what to run
    deps:                             # re-run if these change
    - path/to/script.py
    - path/to/input/data
    params:                           # re-run if these values change in params.yaml
    - section_name
    outs:                             # output files (DVC tracks these)
    - path/to/output
    metrics:                          # metrics file (Git tracks, DVC compares)
    - reports/metrics.json:
        cache: false                  # don't cache — Git tracks it directly
```

Why `cmd` and `deps` both reference the same script:
- `cmd` — tells DVC **what to execute**
- `deps` — tells DVC **when to re-execute** (if the script file changes, re-run the stage)

### Module mode vs Script mode

```bash
python -m emotional_tweet.dataset       # module mode — correct
python emotional_tweet/dataset.py       # script mode — can break imports
```

Module mode (`-m`) uses Python's import system. Script mode adds the script's directory to `sys.path`, which can import the wrong package if another copy exists in a parent directory.

### Common DVC Commands

```bash
dvc repro                    # run pipeline (only changed stages)
dvc repro -f stage_name      # force re-run a specific stage
dvc status                   # check what's changed
dvc dag                      # show pipeline graph
dvc metrics show             # display current metrics
dvc metrics diff             # compare metrics with last commit
dvc push                     # upload data to remote (S3)
dvc pull                     # download data from remote
dvc remote list              # show configured remotes
```

---

## DVC Remote Storage

### Setting up S3 Remote

```bash
# 1. Install DVC S3 support
pip install dvc-s3

# 2. Remove old local remote (if exists)
dvc remote remove localremote

# 3. Add S3 remote
dvc remote add -d myremote s3://your-bucket-name/dvcstore

# 4. Configure AWS credentials
aws configure

# 5. Push data
dvc push

# 6. Verify
dvc remote list
```

### What gets pushed to S3

Only the `outs` from `dvc.yaml`:
- `data/raw/` — train.csv, test.csv
- `data/processed/` — train_processed.csv, test_processed.csv
- `data/features/` — train_tfidf.csv, test_tfidf.csv
- `models/model.pkl` — trained model

### Local vs S3 Remote

| | Local (`../dvc_temp`) | S3 (`s3://bucket/path`) |
|---|---|---|
| **Setup** | No config needed | Needs `aws configure` |
| **Sharing** | Only works on your machine | Anyone with S3 access can pull |
| **Cost** | Free | S3 storage costs |
| **Use case** | Learning, testing | Team collaboration, production |

---

## MLflow — Experiment Tracking

MLflow logs everything about your experiments: parameters, metrics, models, and artifacts.

### Connection to DagsHub

```python
import mlflow
mlflow.set_tracking_uri("https://dagshub.com/vaibhav.vaibhav.rai009/mlops-mini-project.mlflow")
import dagshub
dagshub.init(repo_owner='vaibhav.vaibhav.rai009', repo_name='mlops-mini-project', mlflow=True)
```

DagsHub provides a free hosted MLflow server per repository. All experiment data is stored there.

### MLflow Core Concepts

```text
Experiment          → a named group of runs (e.g., "Bow vs TfIdf")
  └── Run           → one training session
        ├── Parameters   → hyperparameters (C=1, penalty='l2')
        ├── Metrics      → evaluation results (accuracy=0.79)
        ├── Model        → saved model artifact
        └── Artifacts    → any files (scripts, plots, configs)
```

### Logging API

```python
with mlflow.start_run() as run:
    # Log hyperparameters
    mlflow.log_param("C", 1)
    mlflow.log_param("penalty", "l2")
    
    # Log metrics
    mlflow.log_metric("accuracy", 0.79)
    mlflow.log_metric("f1_score", 0.78)
    
    # Log model with signature
    signature = infer_signature(X_test, y_pred)
    mlflow.sklearn.log_model(model, artifact_path="model", signature=signature)
    
    # Log any file as artifact
    mlflow.log_artifact("reports/metrics_dict.json")
```

### Model Signature

```python
from mlflow.models import infer_signature
signature = infer_signature(X_test, y_pred)
```

Records what the model expects as input and output. Example:
- Input: 200 float columns (TF-IDF features)
- Output: integer (0 or 1)

This is used for validation when serving the model — MLflow will reject inputs that don't match.

### Nested Runs

```python
with mlflow.start_run(run_name="Parent") as parent:
    with mlflow.start_run(run_name="Child 1", nested=True):
        # logs go to child 1
    with mlflow.start_run(run_name="Child 2", nested=True):
        # logs go to child 2
```

Parent groups related experiments. Each child has its own params/metrics/model.

### Model Logging — sklearn vs xgboost

```python
# For sklearn models (LogisticRegression, NaiveBayes, RandomForest, etc.)
mlflow.sklearn.log_model(model, artifact_path="model")

# For XGBoost models — sklearn logger fails with UntrustedTypesFoundException
mlflow.xgboost.log_model(model, "model")
```

### artifact_path vs name (MLflow 3.x)

```python
# Old way (MLflow 2.x) — positional argument was artifact_path
mlflow.sklearn.log_model(model, "model")

# New way (MLflow 3.x) — positional argument is now name
# Use keyword argument to be explicit
mlflow.sklearn.log_model(model, artifact_path="model")
```

If you don't use the keyword, the model may be stored differently and `register_model` won't find it.

---

## MLflow Model Registry

### Registering a Model (MLflow 3.x)

```python
# model_info.json contains model_id from log_model result
model_uri = f"models:/{model_id}"           # MLflow 3.x URI format
result = mlflow.register_model(model_uri, "my_model")
```

In MLflow 3.x, `log_model` returns a `model_id`. Use `models:/{model_id}` URI to register, not the old `runs:/{run_id}/artifact_path` format.

### Model Stages

```python
client = mlflow.tracking.MlflowClient()
client.transition_model_version_stage(
    name="my_model",
    version=result.version,
    stage="Staging"
)
```

```text
None → Staging → Production → Archived
```

---

## DVC + MLflow — What Goes Where

| What | DVC | MLflow | Git |
|------|-----|--------|-----|
| Raw data | Yes (S3) | No | No |
| Processed data | Yes (S3) | No | No |
| Feature data | Yes (S3) | No | No |
| Model (.pkl) | Yes (S3) | Yes (artifact) | No |
| Vectorizer (.pkl) | Yes (S3) | No | No |
| Metrics (JSON) | Yes (metric) | Yes (log_metric) | Yes |
| Hyperparameters | No | Yes (log_param) | Yes (params.yaml) |
| Code | No | No | Yes |
| Pipeline definition | No | No | Yes (dvc.yaml) |
| Model registry | No | Yes | No |

DVC and MLflow complement each other:
- **DVC** handles the pipeline and data versioning
- **MLflow** handles experiment tracking and model management
- **Git** handles code versioning

---

## How to Decide — DVC or MLflow?

### The Two Rules

```text
┌────────────────┬──────────────────────────────────┬──────────────────────────────────────────┐
│                │               DVC                │                  MLflow                  │
├────────────────┼──────────────────────────────────┼──────────────────────────────────────────┤
│ Purpose        │ Version & reproduce              │ Track & compare                          │
├────────────────┼──────────────────────────────────┼──────────────────────────────────────────┤
│ Think of it as │ A hard drive with history        │ A lab notebook                           │
├────────────────┼──────────────────────────────────┼──────────────────────────────────────────┤
│ Saves          │ Files your pipeline needs to run │ Records about what happened during a run │
└────────────────┴──────────────────────────────────┴──────────────────────────────────────────┘
```

### DVC — "Can the next stage use this?"

If a file is **consumed by another stage** or **needed to serve the model**, it goes in DVC:

```text
data/raw/              → preprocessing needs it
data/processed/        → feature engineering needs it
data/features/         → training needs it
models/model.pkl       → evaluation needs it, app serves it
models/vectorizer.pkl  → app needs it to transform user input
```

**Rule: If deleting this file breaks `dvc repro` or the app, it belongs in DVC.**

### MLflow — "Do I want to compare this across runs?"

If you want to **look back and compare**, it goes in MLflow:

```text
metrics (accuracy, f1)     → "which run was best?"
params (C=1, penalty=l2)   → "what settings produced that?"
model artifact             → "I want to deploy run #47's model"
signature                  → "what does this model expect?"
```

**Rule: If you'd put this in a spreadsheet to compare experiments, it belongs in MLflow.**

---

## WHEN to Save — Stage by Stage

```text
┌─────────────────────┬─────────────────────────────────────┬────────────────────────────────────────────────────────────┐
│        Stage        │          DVC (save files)           │                    MLflow (log records)                    │
├─────────────────────┼─────────────────────────────────────┼────────────────────────────────────────────────────────────┤
│ Data ingestion      │ Save train/test splits              │ Nothing — no experiment yet                                │
├─────────────────────┼─────────────────────────────────────┼────────────────────────────────────────────────────────────┤
│ Preprocessing       │ Save cleaned data                   │ Nothing — no metrics yet                                   │
├─────────────────────┼─────────────────────────────────────┼────────────────────────────────────────────────────────────┤
│ Feature engineering │ Save feature matrices + vectorizer  │ Nothing — no model yet                                     │
├─────────────────────┼─────────────────────────────────────┼────────────────────────────────────────────────────────────┤
│ Training            │ Save model.pkl                      │ Nothing yet — wait for evaluation                          │
├─────────────────────┼─────────────────────────────────────┼────────────────────────────────────────────────────────────┤
│ Evaluation          │ Metrics file (for dvc metrics diff) │ Log metrics, params, model, signature — this is the moment │
├─────────────────────┼─────────────────────────────────────┼────────────────────────────────────────────────────────────┤
│ Registration        │ Nothing                             │ Register model to registry, set stage                      │
├─────────────────────┼─────────────────────────────────────┼────────────────────────────────────────────────────────────┤
│ Serving (app)       │ Nothing — consumes DVC files        │ Nothing — consumes registered model                        │
└─────────────────────┴─────────────────────────────────────┴────────────────────────────────────────────────────────────┘
```

### The Key Insight

**DVC saves happen during the pipeline** — they're the outputs that flow between stages.

**MLflow logging happens at evaluation time** — that's when you have results worth recording. You don't log to MLflow during training because you don't have metrics yet. You log everything together in evaluation: the model, its params, its metrics, its signature.

### Overlap is OK

`model.pkl` exists in **both** DVC and MLflow — that's intentional:
- **DVC copy**: pipeline artifact, lets the next stage run
- **MLflow copy**: experiment artifact, tied to a run_id, deployable from the registry

They serve different purposes even though it's the same file.