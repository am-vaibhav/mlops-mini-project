from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import pickle
import pandas as pd
from preprocessing_utility import normalize_text


import mlflow
mlflow.set_tracking_uri("https://dagshub.com/vaibhav.vaibhav.rai009/mlops-mini-project.mlflow")
import dagshub
dagshub.init(repo_owner='vaibhav.vaibhav.rai009', repo_name='mlops-mini-project', mlflow=True)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

def get_latest_model_version(model_name):
    client = mlflow.MlflowClient()
    latest_version = client.get_latest_versions(model_name, stages=["Production"])
    if not latest_version:
        latest_version = client.get_latest_versions(model_name, stages=["None"])
    return latest_version[0].version if latest_version else None

model_name = "my_model"
model_version = get_latest_model_version(model_name)

model_uri = f'models:/{model_name}/{model_version}'
model = mlflow.pyfunc.load_model(model_uri)

vectorizer = pickle.load(open('models/vectorizer.pkl', 'rb'))

@app.get('/', response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "result": None})

@app.post('/predict', response_class=HTMLResponse)
async def predict(request: Request, text: str = Form(...)):
    text = normalize_text(text)

    features = vectorizer.transform([text])

    features_df = pd.DataFrame(features.toarray(), columns=[str(i) for i in range(features.shape[1])])

    result = model.predict(features_df)

    return templates.TemplateResponse("index.html", {"request": request, "result": result[0]})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8040)