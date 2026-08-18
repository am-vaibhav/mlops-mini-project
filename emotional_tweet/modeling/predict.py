import pandas as pd
import pickle
import json
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
import os
import logging
import mlflow
from mlflow.models import infer_signature
from dotenv import load_dotenv
load_dotenv()

# logging configuration
logger = logging.getLogger('model_evaluation')
logger.setLevel('DEBUG')

console_handler = logging.StreamHandler()
console_handler.setLevel('DEBUG')

file_handler = logging.FileHandler('model_evaluation_errors.log')
file_handler.setLevel('ERROR')

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

from emotional_tweet.config import MODELS_DIR, FEATURES_DATA_DIR, REPORTS_DIR

test_data = pd.read_csv(str(FEATURES_DATA_DIR / 'test_tfidf.csv'))
X_test = test_data.iloc[:, :-1].values
y_test = test_data.iloc[:, -1].values

with open(str(MODELS_DIR / 'model.pkl'), 'rb') as f:
    model = pickle.load(f)

y_pred = model.predict(X_test)
y_pred_proba = model.predict_proba(X_test)[:, 1]

accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
auc = roc_auc_score(y_test, y_pred_proba)

metrics_dict = {
    'accuracy': accuracy,
    'precision': precision,
    'recall': recall,
    'auc': auc
}

with open(str(REPORTS_DIR / 'metrics_dict.json'), 'w') as f:
    json.dump(metrics_dict, f)


# Set up DagsHub credentials for MLflow tracking
dagshub_token = os.getenv("DAGSHUB_PAT")
os.environ["MLFLOW_TRACKING_USERNAME"] = dagshub_token
os.environ["MLFLOW_TRACKING_PASSWORD"] = dagshub_token

dagshub_url = "https://dagshub.com"
repo_owner = "vaibhav.vaibhav.rai009"
repo_name = "mlops-mini-project"

# Set up MLflow tracking URI
mlflow.set_tracking_uri(f'{dagshub_url}/{repo_owner}/{repo_name}.mlflow')
mlflow.set_experiment("dvc-pipeline")

with mlflow.start_run() as run:  # Start an MLflow run
    # Log metrics to MLflow
    for metric_name, metric_value in metrics_dict.items():
        mlflow.log_metric(metric_name, metric_value)

    # Log model parameters to MLflow
    if hasattr(model, 'get_params'):
        params = model.get_params()
        for param_name, param_value in params.items():
            mlflow.log_param(param_name, param_value)

    # Log model to MLflow
    signature = infer_signature(X_test, y_pred)
    model_result = mlflow.sklearn.log_model(model, artifact_path="model", signature=signature)

    # Save model info
    run_id = run.info.run_id
    model_id = model_result.model_id
    model_info = {'run_id': run_id, 'model_id': model_id, 'model_path': f"models:/{model_id}"}
    with open(str(REPORTS_DIR / 'model_info.json'), 'w') as file:
        json.dump(model_info, file, indent=4)

    # Log the model info file to MLflow
    mlflow.log_artifact(str(REPORTS_DIR / 'model_info.json'))

    # Log the metrics file to MLflow
    mlflow.log_artifact(str(REPORTS_DIR / 'metrics_dict.json'))


    # Log the evaluation errors log file to MLflow
    if os.path.exists('model_evaluation_errors.log'):
        mlflow.log_artifact('model_evaluation_errors.log')