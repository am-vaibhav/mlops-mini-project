Getting Started
===============

## Prerequisites

- Python 3.12+
- AWS CLI (for S3 remote)
- Git

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

# 6. Pull data from DVC remote
dvc pull
```

## Running the Pipeline

```bash
# Run the full pipeline
dvc repro

# Force re-run a specific stage
dvc repro -f model_evaluation

# Check pipeline status
dvc status
```

## Quick Test (without DVC)

```bash
# Run individual stages manually
python -m emotional_tweet.dataset
python -m emotional_tweet.data_preprocessing
python -m emotional_tweet.features
python -m emotional_tweet.modeling.train
python -m emotional_tweet.modeling.predict
python -m emotional_tweet.modeling.register_model
```

**Important:** Always use `python -m` (module mode) — not `python emotional_tweet/file.py` (script mode). Script mode breaks `PROJ_ROOT` path resolution because Python adds the script's directory to `sys.path`, which can import the wrong package if another copy exists nearby.