Testing
=======

Tests live in the `tests/` directory and run with Python's built-in `unittest`.

```text
tests/
├── test_model.py      # Model loading, signature, and performance tests
└── test_fast_app.py   # FastAPI endpoint tests (needs update for FastAPI)
```

---

## Running Tests

```bash
# Run model tests
python -m unittest tests/test_model.py

# Run FastAPI app tests
python -m unittest tests/test_fast_app.py

# Run all tests
python -m unittest discover -s tests
```

**Required:** `DAGSHUB_PAT` environment variable must be set (tests connect to MLflow on DagsHub).

---

## test_model.py — Model Validation

**File:** `tests/test_model.py`

This test suite validates a model from the MLflow registry before promoting it to Production.

### Setup (`setUpClass`)

```python
cls.new_model = mlflow.pyfunc.load_model(model_uri)
cls.vectorizer = pickle.load(open('models/vectorizer.pkl', 'rb'))
cls.holdout_data = pd.read_csv('data/processed/test_bow.csv')
```

Loads:
1. The latest model version from MLflow registry (Staging stage)
2. The TF-IDF vectorizer from local file
3. Holdout test data for performance evaluation

### Test 1: `test_model_loaded_properly`

```python
self.assertIsNotNone(self.new_model)
```

Checks that the model was successfully loaded from the MLflow registry. Fails if the model URI is wrong or the registry is unreachable.

### Test 2: `test_model_signature`

```python
input_data = self.vectorizer.transform(["hi how are you"])
input_df = pd.DataFrame(input_data.toarray(), ...)
prediction = self.new_model.predict(input_df)

self.assertEqual(input_df.shape[1], len(self.vectorizer.get_feature_names_out()))
self.assertEqual(len(prediction), input_df.shape[0])
self.assertEqual(len(prediction.shape), 1)
```

Verifies:
- Input shape matches vectorizer output (200 features)
- Output is a 1D array (binary classification)
- Model can actually produce predictions from vectorized text

### Test 3: `test_model_performance`

```python
expected_accuracy = 0.40
expected_precision = 0.40
expected_recall = 0.40
expected_f1 = 0.40
```

Runs the model on holdout test data and checks that all metrics meet minimum thresholds (0.40). This prevents deploying a model that performs worse than random guessing.

| Metric | Threshold | What it measures |
|--------|-----------|-----------------|
| Accuracy | >= 0.40 | Overall correct predictions |
| Precision | >= 0.40 | Of predicted Happy, how many are actually Happy |
| Recall | >= 0.40 | Of actual Happy tweets, how many did we catch |
| F1 | >= 0.40 | Harmonic mean of precision and recall |

### How it fits in CI/CD

In `.github/workflows/ci.yaml`, model tests are currently commented out:

```yaml
#      - name: Run model tests
#        env:
#          DAGSHUB_PAT: ${{ secrets.DAGSHUB_PAT }}
#        run: |
#          python -m unittest tests/test_model.py
```

When enabled, the flow would be:
```text
dvc repro → run tests → if tests pass → build Docker → deploy
```

Tests act as a gate — a model that fails performance thresholds won't be deployed.

---

## test_fast_app.py — API Endpoint Tests

**File:** `tests/test_fast_app.py`

**Note:** This test file still uses Flask-style `test_client()`. It needs to be updated for FastAPI.

### Current (Flask-style — outdated)

```python
cls.client = app.test_client()
response = self.client.get('/')
response = self.client.post('/predict', data=dict(text="I love this!"))
```

### Updated (FastAPI-style — what it should be)

```python
from fastapi.testclient import TestClient
from fast_api.app import app

class FastAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_predict_page(self):
        response = self.client.post('/predict', data={"text": "I love this!"})
        self.assertEqual(response.status_code, 200)
```

FastAPI uses `TestClient` from `fastapi.testclient` (which wraps `httpx`) instead of Flask's `test_client()`.

### What the tests check

| Test | Endpoint | Method | Checks |
|------|----------|--------|--------|
| `test_home_page` | `/` | GET | Returns 200, contains page title |
| `test_predict_page` | `/predict` | POST | Returns 200, response contains "Happy" or "Sad" |

---

## Testing Commands Reference

```bash
# Run specific test file
python -m unittest tests/test_model.py

# Run specific test class
python -m unittest tests.test_model.TestModelLoading

# Run specific test method
python -m unittest tests.test_model.TestModelLoading.test_model_performance

# Run with verbose output
python -m unittest -v tests/test_model.py

# Run all tests in tests/ directory
python -m unittest discover -s tests

# Run tests with pytest (if installed)
pytest tests/ -v
```
