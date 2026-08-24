FastAPI App — Model Serving
============================

The FastAPI app serves the trained sentiment model via a web interface. Users type tweet text, and the app predicts whether it's **Happy** or **Sad**.

## Project Structure

```text
fast_api/
├── app.py                    # FastAPI application
├── preprocessing_utility.py  # Text preprocessing functions
├── requirements.txt          # App dependencies
├── models/
│   └── vectorizer.pkl        # TF-IDF vectorizer (copied from project root)
└── templates/
    └── index.html            # HTML form + result display
```

---

## How the App Works

```text
User types tweet → normalize_text() → vectorizer.transform() → model.predict() → Happy/Sad
```

### Step-by-step flow

1. **User submits text** via the HTML form (`POST /predict`)
2. **Text preprocessing** — `normalize_text()` from `preprocessing_utility.py` cleans the text (lowercase, remove stopwords, lemmatize, etc.)
3. **Feature extraction** — the TF-IDF vectorizer transforms cleaned text into a feature vector
4. **Prediction** — the MLflow model predicts 0 (Sad) or 1 (Happy)
5. **Response** — result is rendered in the same HTML page

### Where the model comes from

The model is **not** stored locally — it's loaded from **MLflow Model Registry** on DagsHub at startup:

```python
def get_latest_model_version(model_name):
    client = mlflow.MlflowClient()
    latest_version = client.get_latest_versions(model_name, stages=["Production"])
    if not latest_version:
        latest_version = client.get_latest_versions(model_name, stages=["None"])
    return latest_version[0].version if latest_version else None

model_uri = f'models:/{model_name}/{model_version}'
model = mlflow.pyfunc.load_model(model_uri)
```

This means:
- No model file in the Docker image — it downloads fresh from MLflow on startup
- When you register a new model version and set it to Production, the app picks it up on next restart
- The vectorizer (`vectorizer.pkl`) IS stored locally because it's not in the MLflow registry

### Authentication

The app uses `DAGSHUB_PAT` (Personal Access Token) to authenticate with DagsHub's MLflow server:

```python
dagshub_token = os.getenv("DAGSHUB_PAT")
os.environ["MLFLOW_TRACKING_USERNAME"] = dagshub_token
os.environ["MLFLOW_TRACKING_PASSWORD"] = dagshub_token
```

This token is passed as an environment variable — never hardcoded.

---

## app.py — Key Parts Explained

### FastAPI vs Flask

This app was converted from Flask to FastAPI. Key differences:

| Flask | FastAPI |
|-------|---------|
| `Flask(__name__)` | `FastAPI()` |
| `render_template("index.html", result=None)` | `templates.TemplateResponse(request, "index.html", {"result": None})` |
| `@app.route('/predict', methods=['POST'])` | `@app.post('/predict')` |
| `request.form['text']` | `text: str = Form(...)` |
| `app.run(debug=True)` | `uvicorn.run(app, port=8050)` |

### Why `Form(...)` is needed

FastAPI expects JSON by default. HTML forms send data as `application/x-www-form-urlencoded`. `Form(...)` tells FastAPI to read from form data instead of JSON.

### Template path resolution

```python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
```

Uses `__file__` to find the templates folder relative to `app.py` — works regardless of which directory you launch the app from.

### TemplateResponse — new Starlette syntax

```python
# Old (Starlette < 0.30)
templates.TemplateResponse("index.html", {"request": request, "result": None})

# New (Starlette >= 0.30)
templates.TemplateResponse(request, "index.html", {"result": None})
```

The `request` moved from the context dict to the first argument. Using the old syntax causes `TypeError: unhashable type: 'dict'`.

---

## Running Locally

```bash
cd fast_api
python app.py
# Server starts at http://localhost:8050
```

Or with uvicorn directly:

```bash
cd fast_api
uvicorn app:app --port 8050 --reload
```

**Required:** Set `DAGSHUB_PAT` environment variable before running.

---

## preprocessing_utility.py

Contains the same text preprocessing pipeline used during training:

| Step | Function | What it does |
|------|----------|-------------|
| 1 | `lower_case` | Convert to lowercase |
| 2 | `remove_stop_words` | Remove common English words |
| 3 | `removing_numbers` | Strip all digits |
| 4 | `removing_punctuations` | Remove punctuation marks |
| 5 | `removing_urls` | Remove URLs |
| 6 | `lemmatization` | Reduce words to base form |

**Important:** This must match the preprocessing done during training — if you change preprocessing in the pipeline, update this file too, or predictions will be wrong.