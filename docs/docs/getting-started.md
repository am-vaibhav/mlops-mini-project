Getting Started
===============

## Prerequisites

- Python 3.12+
- AWS CLI (for S3 remote)
- Git
- Docker (for containerized deployment)

## Setup

```bash
# 1. Clone the repo
git clone <repo-url>
cd mlops-mini-project

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download NLTK data (needed for text preprocessing)
python -c "import nltk; nltk.download('stopwords'); nltk.download('wordnet')"

# 5. Configure AWS (for DVC S3 remote)
aws configure
# Enter: Access Key, Secret Key, Region, Output format

# 6. Set up DagsHub token
echo 'DAGSHUB_PAT=your_dagshub_token_here' > .env

# 7. Pull data from DVC remote
dvc pull
```

### Getting a DagsHub PAT

1. Go to [DagsHub](https://dagshub.com) → Settings → Access Tokens
2. Create a new token
3. Save it in the `.env` file as shown above

---

## Running the Pipeline

```bash
# Run the full pipeline (only changed stages)
dvc repro

# Force re-run a specific stage
dvc repro -f model_evaluation

# Check pipeline status
dvc status

# View pipeline DAG
dvc dag
```

## Running Stages Individually

```bash
python -m emotional_tweet.dataset
python -m emotional_tweet.data_preprocessing
python -m emotional_tweet.features
python -m emotional_tweet.modeling.train
python -m emotional_tweet.modeling.predict
python -m emotional_tweet.modeling.register_model
```

**Important:** Always use `python -m` (module mode) — not `python emotional_tweet/file.py` (script mode). Script mode breaks `PROJ_ROOT` path resolution because Python adds the script's directory to `sys.path`, which can import the wrong package if another copy exists nearby.

---

## Running the FastAPI App Locally

```bash
cd fast_api
export DAGSHUB_PAT="your_token_here"
python app.py
# Server starts at http://localhost:8050
```

Or with uvicorn (auto-reload for development):

```bash
cd fast_api
uvicorn app:app --port 8050 --reload
```

---

## Running with Docker Locally

```bash
# Build
docker build -t emotions:v1 .

# Run
docker run -d -p 8050:8050 --name my-app \
  -e DAGSHUB_PAT="your_token_here" \
  emotions:v1

# Check
docker logs my-app

# Visit http://localhost:8050
```

---

## Running Tests

```bash
# Model tests (needs DAGSHUB_PAT)
python -m unittest tests/test_model.py

# All tests
python -m unittest discover -s tests
```

---

## Comparing Metrics After Changes

```bash
# 1. Edit params.yaml
# 2. Re-run
dvc repro
# 3. See current metrics
dvc metrics show
# 4. Compare with last commit
dvc metrics diff
# 5. Push data and commit
dvc push
git add dvc.lock params.yaml reports/metrics_dict.json
git commit -m "tune parameters"
git push origin main    # triggers CI/CD
```