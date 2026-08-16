import numpy as np
import pandas as pd
import pickle
import json
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
import os

from emotional_tweet.config import MODELS_DIR, FEATURES_DATA_DIR, PROJ_ROOT

test_data = pd.read_csv(str(FEATURES_DATA_DIR / 'test_tfidf.csv'))
X_test = test_data.iloc[:, :-1].values
y_test = test_data.iloc[:, -1].values

model = pickle.load(open(str(MODELS_DIR / 'model.pkl'), 'rb'))

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
json.dump(metrics_dict, open(str(PROJ_ROOT / 'metrics_dict.json'), 'w'))