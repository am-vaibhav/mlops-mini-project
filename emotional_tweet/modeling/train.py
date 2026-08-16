import numpy as np
import pandas as pd
import pickle
from sklearn.linear_model import LogisticRegression
import logging
import yaml

from emotional_tweet.config import MODELS_DIR, FEATURES_DATA_DIR, PROJ_ROOT

C = yaml.safe_load(open(str(PROJ_ROOT / "params.yaml"), "r"))["model_building"]["C"]
solver = yaml.safe_load(open(str(PROJ_ROOT / "params.yaml"), "r"))["model_building"]["solver"]
penalty = yaml.safe_load(open(str(PROJ_ROOT / "params.yaml"), "r"))["model_building"]["penalty"]


train_data = pd.read_csv(str(FEATURES_DATA_DIR / 'train_tfidf.csv'))
X_train = train_data.iloc[:, :-1].values
y_train = train_data.iloc[:, -1].values

lr = LogisticRegression(C=C, solver=solver, penalty=penalty)
lr.fit(X_train, y_train)
pickle.dump(lr, open(str(MODELS_DIR / 'model.pkl'), 'wb'))