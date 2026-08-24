Project Configuration
=====================

This page covers all configuration files in the project.

---

## config.py — Path Constants

**File:** `emotional_tweet/config.py`

Central file that defines all directory paths used across the project. Every pipeline stage imports from here.

```python
from pathlib import Path

PROJ_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJ_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
FEATURES_DATA_DIR = DATA_DIR / "features"

PARAMS_FILE = PROJ_ROOT / "params.yaml"
MODELS_DIR = PROJ_ROOT / "models"
REPORTS_DIR = PROJ_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
```

### How `PROJ_ROOT` works

```python
PROJ_ROOT = Path(__file__).resolve().parents[1]
```

- `__file__` — path to `config.py` itself (`emotional_tweet/config.py`)
- `.resolve()` — converts to absolute path
- `.parents[1]` — goes up 2 levels: `config.py → emotional_tweet/ → mlops-mini-project/`

This gives the project root regardless of where you run the code from.

### Why module mode matters

```bash
python -m emotional_tweet.dataset       # PROJ_ROOT = /mlops-mini-project (correct)
python emotional_tweet/dataset.py       # PROJ_ROOT might resolve wrong if another copy exists
```

Module mode (`-m`) uses Python's import system, so `__file__` always points to the correct `config.py`. Script mode can add unexpected directories to `sys.path`.

### Which files import config.py

| File | What it imports |
|------|----------------|
| `dataset.py` | `RAW_DATA_DIR`, `PROJ_ROOT` |
| `data_preprocessing.py` | `RAW_DATA_DIR`, `PROCESSED_DATA_DIR` |
| `features.py` | `PROCESSED_DATA_DIR`, `FEATURES_DATA_DIR`, `PROJ_ROOT` |
| `modeling/train.py` | `MODELS_DIR`, `FEATURES_DATA_DIR`, `PROJ_ROOT` |
| `modeling/predict.py` | `MODELS_DIR`, `FEATURES_DATA_DIR`, `REPORTS_DIR` |
| `plots.py` | `FIGURES_DIR`, `PROCESSED_DATA_DIR` |

### Logging

`config.py` also sets up a logger with console + file handlers:

```text
Console: DEBUG level (all messages)
File (errors.log): ERROR level only
Format: "2025-01-15 10:30:45 - data_ingestion - INFO - message"
```

---

## params.yaml — Hyperparameters

**File:** `params.yaml` (project root)

```yaml
data_ingestion:
  test_size: 0.3
feature_engineering:
  max_features: 200
model_building:
  C: 1
  penalty: 'l2'
  solver: 'liblinear'
```

### What each parameter does

| Section | Parameter | Value | Meaning |
|---------|-----------|-------|---------|
| `data_ingestion` | `test_size` | `0.3` | 30% of data used for testing, 70% for training |
| `feature_engineering` | `max_features` | `200` | TF-IDF keeps only top 200 most informative words |
| `model_building` | `C` | `1` | Inverse regularization strength (higher = less regularization) |
| `model_building` | `penalty` | `l2` | L2 regularization (shrinks all feature weights) |
| `model_building` | `solver` | `liblinear` | Optimization algorithm (supports both L1 and L2) |

### How DVC uses params.yaml

In `dvc.yaml`, stages declare which params they depend on:

```yaml
data_ingestion:
  params: [data_ingestion]      # watches data_ingestion.test_size
feature_engineering:
  params: [feature_engineering]  # watches feature_engineering.max_features
model_building:
  params: [model_building]       # watches model_building.C, penalty, solver
```

If you change a parameter value, `dvc repro` re-runs only the affected stages and everything downstream.

### How to tune parameters

```bash
# 1. Edit params.yaml (e.g., change C from 1 to 10)

# 2. Re-run the pipeline
dvc repro

# 3. Compare metrics with previous run
dvc metrics diff
```

---

## requirements.txt — Python Dependencies

**File:** `requirements.txt` (project root)

```text
boto3           # AWS SDK (for S3 DVC remote)
dagshub         # DagsHub integration
docker          # Docker SDK for Python
dvc             # Data Version Control
dvc-s3          # DVC S3 remote support
mlflow          # Experiment tracking
nltk            # Text preprocessing (stopwords, lemmatization)
numpy           # Numerical computing
pandas          # Data manipulation
scikit-learn    # ML algorithms (LogisticRegression, TF-IDF, metrics)
scipy           # Scientific computing (sparse matrices)
SQLAlchemy      # Database toolkit (MLflow dependency)
fastapi         # Web framework for the API
uvicorn         # ASGI server for FastAPI
jinja2          # HTML templating
python-multipart # Form data parsing for FastAPI
joblib          # Model serialization (sklearn dependency)
requests        # HTTP requests
PyYAML          # YAML file parsing (params.yaml)
pydantic        # Data validation (FastAPI dependency)
httpx           # HTTP client (FastAPI TestClient dependency)
```

### Install

```bash
pip install -r requirements.txt
```

**Note:** The `fast_api/` folder has its own `requirements.txt` for the Docker container — it only includes packages needed for serving (not training).

---

## Makefile — Project Commands

**File:** `Makefile` (project root)

```bash
# See available commands
make help

# Install/update dependencies
make requirements

# Delete compiled Python files and __pycache__
make clean

# Run code linting (check style)
make lint

# Auto-format code
make format

# Create virtual environment
make create_environment
```

| Command | What it does |
|---------|-------------|
| `make requirements` | Upgrades pip and installs from `requirements.txt` |
| `make clean` | Removes `*.pyc`, `*.pyo`, and `__pycache__/` directories |
| `make lint` | Runs `ruff format --check` and `ruff check` |
| `make format` | Runs `ruff check --fix` and `ruff format` |
| `make create_environment` | Creates a new virtualenv with `virtualenvwrapper` |
| `make data` | Runs the data ingestion script |

---

## .dvc/config — DVC Remote Configuration

**File:** `.dvc/config`

```ini
[core]
    remote = myremote
[remote "myremote"]
    url = s3://mlopsminiprojectdvc
```

- `remote = myremote` — sets the default remote
- `url = s3://mlopsminiprojectdvc` — S3 bucket where DVC pushes/pulls data

### Managing remotes

```bash
# List configured remotes
dvc remote list

# Add a new remote
dvc remote add -d myremote s3://bucket-name

# Remove a remote
dvc remote remove myremote

# Modify remote URL
dvc remote modify myremote url s3://new-bucket
```

### AWS credentials

DVC uses AWS credentials from `aws configure`:

```bash
aws configure
# AWS Access Key ID: <your-key>
# AWS Secret Access Key: <your-secret>
# Default region name: <your-region>
# Default output format: json
```

---

## .env — Environment Variables

**File:** `.env` (not committed to Git)

```bash
DAGSHUB_PAT=your_dagshub_personal_access_token
```

Used by `python-dotenv` — the `load_dotenv()` call in `predict.py`, `register_model.py`, and `app.py` reads this file automatically.

### How to get a DagsHub PAT

1. Go to DagsHub → Settings → Access Tokens
2. Create a new token
3. Save it in `.env` file

**Never commit `.env` to Git** — add it to `.gitignore`.

For CI/CD, the token is stored as a GitHub Secret (`DAGSHUB_PAT`) and passed as an environment variable.

---

## plots.py — Placeholder

**File:** `emotional_tweet/plots.py`

Template file for generating plots from processed data. Currently contains placeholder code — not wired into the DVC pipeline.
