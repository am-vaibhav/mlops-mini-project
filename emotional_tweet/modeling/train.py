import numpy as np
import pandas as pd
import pickle
from sklearn.ensemble import GradientBoostingClassifier
import logging
import yaml

from emotional_tweet.config import MODELS_DIR, FEATURES_DATA_DIR, PROJ_ROOT

n_estimators = yaml.safe_load(open(str(PROJ_ROOT / "params.yaml"), "r"))["model_building"]["n_estimators"]
learning_rate = yaml.safe_load(open(str(PROJ_ROOT / "params.yaml"), "r"))["model_building"]["learning_rate"]


train_data = pd.read_csv(str(FEATURES_DATA_DIR / 'train_tfidf.csv'))
X_train = train_data.iloc[:, :-1].values
y_train = train_data.iloc[:, -1].values

lr = GradientBoostingClassifier(n_estimators=n_estimators, learning_rate=learning_rate)
lr.fit(X_train, y_train)
pickle.dump(lr, open(str(MODELS_DIR / 'model.pkl'), 'wb'))