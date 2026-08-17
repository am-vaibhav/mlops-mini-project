import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import os
import yaml
import pickle

from emotional_tweet.config import PROCESSED_DATA_DIR, FEATURES_DATA_DIR, PROJ_ROOT

max_features = yaml.safe_load(open(str(PROJ_ROOT / "params.yaml"), "r"))["feature_engineering"]["max_features"]

train_data = pd.read_csv(str(PROCESSED_DATA_DIR / 'train_processed.csv'))
test_data = pd.read_csv(str(PROCESSED_DATA_DIR / 'test_processed.csv'))
train_data.fillna('', inplace=True)
test_data.fillna('', inplace=True)

X_train = train_data["content"].values
y_train = train_data["sentiment"].values
X_test = test_data["content"].values
y_test = test_data["sentiment"].values
vectorizer = TfidfVectorizer(max_features=max_features)
X_train_tfidf = vectorizer.fit_transform(X_train)
X_test_tfidf = vectorizer.transform(X_test)

train_df = pd.DataFrame(X_train_tfidf.toarray())
train_df['label'] = y_train

test_df = pd.DataFrame(X_test_tfidf.toarray())
test_df['label'] = y_test

pickle.dump(vectorizer, open(str(PROJ_ROOT / "models/vectorizer.pkl"), "wb"))

data_path = str(FEATURES_DATA_DIR)
os.makedirs(data_path, exist_ok=True)
train_df.to_csv(os.path.join(data_path, "train_tfidf.csv"), index=False)
test_df.to_csv(os.path.join(data_path, "test_tfidf.csv"), index=False)