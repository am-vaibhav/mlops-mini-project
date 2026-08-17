Experiments (Notebooks)
========================

Standalone experiments run outside the DVC pipeline. They connect directly to DagsHub MLflow for tracking.

All experiments live in `notebooks/` and are run manually:

```bash
python notebooks/exp1_bow_vs_tfidf.py
python notebooks/exp3_lor_bow_hp.py
```

---

## DagsHub + MLflow Setup

**File:** `notebooks/dagshub_setup.py`

Every experiment starts with this connection block:

```python
import mlflow
mlflow.set_tracking_uri("https://dagshub.com/vaibhav.vaibhav.rai009/mlops-mini-project.mlflow")
import dagshub
dagshub.init(repo_owner='vaibhav.vaibhav.rai009', repo_name='mlops-mini-project', mlflow=True)
```

What each line does:
- `set_tracking_uri` — tells MLflow where the server is (DagsHub hosts a free MLflow instance per repo)
- `dagshub.init` — authenticates with DagsHub and sets up the MLflow connection

After this, all `mlflow.log_*` calls send data to the DagsHub server.

---

## Experiment 1: BoW vs TF-IDF

**File:** `notebooks/exp1_bow_vs_tfidf.py`
**MLflow Experiment:** `"Bow vs TfIdf"`

### Goal

Compare 5 algorithms × 2 feature extraction methods = 10 combinations to find the best approach.

### Algorithms Tested

| Algorithm | Type |
|-----------|------|
| LogisticRegression | Linear classifier |
| MultinomialNB | Naive Bayes (good for text) |
| XGBoost | Gradient boosted trees |
| RandomForest | Ensemble of decision trees |
| GradientBoosting | Sequential boosted trees |

### Feature Extraction Methods

| Method | How it works |
|--------|-------------|
| **BoW** (Bag of Words) | Counts how many times each word appears. "happy happy sad" → [2, 1] |
| **TF-IDF** | Like BoW but weighs rare words higher. Common words get lower scores |

### MLflow Structure — Parent + Nested Runs

```text
Parent Run: "All Experiments"
├── Child: "LogisticRegression with BoW"
├── Child: "LogisticRegression with TF-IDF"
├── Child: "MultinomialNB with BoW"
├── Child: "MultinomialNB with TF-IDF"
├── Child: "XGBoost with BoW"
├── Child: "XGBoost with TF-IDF"
├── ...
```

```python
with mlflow.start_run(run_name="All Experiments") as parent_run:
    for algo_name, algorithm in algorithms.items():
        for vec_name, vectorizer in vectorizers.items():
            with mlflow.start_run(run_name=f"{algo_name} with {vec_name}", nested=True):
                # train, evaluate, log
```

- `nested=True` creates child runs inside the parent
- Each child logs its own params, metrics, and model
- Parent groups them all together in the MLflow UI

### What Gets Logged Per Run

| Type | Values |
|------|--------|
| **Params** | vectorizer, algorithm, test_size, model-specific params (C, alpha, n_estimators, etc.) |
| **Metrics** | accuracy, precision, recall, f1_score |
| **Model** | sklearn model (or xgboost model for XGBoost) |
| **Artifact** | the experiment script itself |

### XGBoost Model Logging

XGBoost models cannot be logged with `mlflow.sklearn.log_model` — it uses skops internally which doesn't trust XGBoost types. Solution:

```python
if algo_name == 'XGBoost':
    mlflow.xgboost.log_model(model, "model")
else:
    mlflow.sklearn.log_model(model, "model")
```

---

## Experiment 3: Logistic Regression Hyperparameter Tuning

**File:** `notebooks/exp3_lor_bow_hp.py`
**MLflow Experiment:** `"LoR Hyperparameter Tuning"`

### Goal

Find the best LogisticRegression hyperparameters using GridSearchCV.

### Hyperparameter Grid

```python
param_grid = {
    'C': [0.1, 1, 10],          # 3 values
    'penalty': ['l1', 'l2'],     # 2 values
    'solver': ['liblinear']      # 1 value (supports both l1 and l2)
}
# Total combinations: 3 × 2 × 1 = 6
```

### What each hyperparameter means

| Param | What it controls |
|-------|-----------------|
| **C** | Inverse regularization strength. Low C = more regularization (simpler model), High C = less regularization (fits data more closely) |
| **penalty** | L1 = can zero out features (feature selection), L2 = shrinks all features (keeps all) |
| **solver** | `liblinear` supports both L1 and L2 penalties |

### How GridSearchCV Works

```text
For each parameter combination:
    Split training data into 5 folds (cv=5)
    Train on 4 folds, test on 1
    Repeat 5 times (each fold gets to be the test set)
    Average the F1 scores across folds → mean_cv_score
Pick the combination with highest mean_cv_score
```

### MLflow Structure

```text
Parent Run:
├── Child: "LR with params: {'C': 0.1, 'penalty': 'l1', 'solver': 'liblinear'}"
├── Child: "LR with params: {'C': 0.1, 'penalty': 'l2', 'solver': 'liblinear'}"
├── Child: "LR with params: {'C': 1, 'penalty': 'l1', 'solver': 'liblinear'}"
├── ...
└── Parent also logs: best_params + best_f1_score + best model
```

Each child run re-trains the model with that parameter combination and evaluates on the test set (not just CV score), so you can compare CV performance vs actual test performance.