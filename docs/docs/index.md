MLOps Mini Project — Tweet Sentiment Classification
=====================================================

This project builds an end-to-end MLOps pipeline for classifying tweet emotions (happiness vs sadness) using DVC for pipeline orchestration, MLflow for experiment tracking, and DagsHub as the remote MLflow server.

## Dataset

**Source:** [CampusX Tweet Emotions Dataset](https://raw.githubusercontent.com/campusx-official/jupyter-masterclass/main/tweet_emotions.csv)

| Column | Description |
|--------|-------------|
| `tweet_id` | Unique tweet identifier (dropped during ingestion) |
| `sentiment` | Emotion label — filtered to `happiness` (1) and `sadness` (0) |
| `content` | Raw tweet text |

---

## Project Structure

```text
mlops-mini-project/
├── .dvc/
│   └── config                 # DVC remote configuration (S3 bucket)
├── .github/
│   └── workflows/
│       └── ci.yaml            # GitHub Actions CI/CD pipeline
├── data/
│   ├── raw/                   # Train/test split (DVC tracked)
│   ├── processed/             # Cleaned text data (DVC tracked)
│   └── features/              # TF-IDF features (DVC tracked)
├── models/
│   ├── model.pkl              # Trained model (DVC tracked)
│   └── vectorizer.pkl         # TF-IDF vectorizer (DVC tracked)
├── reports/
│   ├── metrics_dict.json      # Evaluation metrics (DVC metric, Git tracked)
│   └── model_info.json        # MLflow run_id and model_id
├── emotional_tweet/           # Source code package
│   ├── __init__.py
│   ├── config.py              # All path constants (PROJ_ROOT, DATA_DIR, etc.)
│   ├── dataset.py             # Stage 1: Data ingestion
│   ├── data_preprocessing.py  # Stage 2: Text preprocessing
│   ├── features.py            # Stage 3: TF-IDF feature engineering
│   ├── plots.py               # Plotting (placeholder)
│   └── modeling/
│       ├── __init__.py
│       ├── train.py           # Stage 4: Model training
│       ├── predict.py         # Stage 5: Evaluation + MLflow logging
│       └── register_model.py  # Stage 6: Model registry
├── fast_api/                  # FastAPI serving app
│   ├── app.py                 # FastAPI application
│   ├── preprocessing_utility.py # Text preprocessing for serving
│   ├── requirements.txt       # App-only dependencies (for Docker)
│   ├── models/
│   │   └── vectorizer.pkl     # Vectorizer copy (for serving)
│   └── templates/
│       └── index.html         # Web UI
├── tests/
│   ├── test_model.py          # Model loading, signature, performance tests
│   └── test_fast_app.py       # API endpoint tests
├── notebooks/                 # Standalone experiments
│   ├── dagshub_setup.py       # DagsHub + MLflow connection test
│   ├── exp1_bow_vs_tfidf.py   # BoW vs TF-IDF comparison
│   └── exp3_lor_bow_hp.py     # LogisticRegression hyperparameter tuning
├── docs/                      # MkDocs documentation
│   ├── mkdocs.yml
│   └── docs/
├── Dockerfile                 # Container definition for deployment
├── Makefile                   # Project automation commands
├── dvc.yaml                   # DVC pipeline definition
├── dvc.lock                   # DVC pipeline state (auto-generated)
├── params.yaml                # Hyperparameters
├── requirements.txt           # Full project dependencies
└── .env                       # Environment variables (not in Git)
```

---

## How It All Connects

```text
params.yaml ──→ dataset.py ──→ data_preprocessing.py ──→ features.py ──→ train.py ──→ predict.py ──→ register_model.py
                    │                   │                     │              │            │                │
                  data/raw         data/processed        data/features   models/    reports/         MLflow
                                                                        model.pkl  metrics_dict.json  Registry
```

- **Git tracks:** code, dvc.yaml, dvc.lock, params.yaml, reports/metrics_dict.json
- **DVC tracks:** data/, models/ (large files pushed to S3 remote)
- **MLflow tracks:** metrics, parameters, model artifacts, model registry (on DagsHub)

---

## Tools Used

| Tool | Purpose |
|------|---------|
| **DVC** | Data versioning, pipeline orchestration, remote storage (S3) |
| **MLflow** | Experiment tracking, model logging, model registry |
| **DagsHub** | Remote MLflow tracking server |
| **scikit-learn** | LogisticRegression, TF-IDF, metrics |
| **NLTK** | Text preprocessing (stopwords, lemmatization) |