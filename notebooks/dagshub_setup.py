import mlflow
mlflow.set_tracking_uri("https://dagshub.com/vaibhav.vaibhav.rai009/mlops-mini-project.mlflow")
import dagshub
dagshub.init(repo_owner='vaibhav.vaibhav.rai009', repo_name='mlops-mini-project', mlflow=True)

with mlflow.start_run():
  mlflow.log_param('parameter name', 'value')
  mlflow.log_metric('metric name', 1)