CLI Commands Reference
======================

All terminal commands needed to work with this project, organized by tool.

---

## Git

```bash
# Clone the repository
git clone <repo-url>
cd mlops-mini-project

# Check status
git status

# Stage and commit
git add dvc.yaml params.yaml dvc.lock reports/metrics_dict.json
git commit -m "update pipeline parameters"

# Push to remote (triggers CI/CD)
git push origin main

# Pull latest changes
git pull origin main

# View commit history
git log --oneline -10
```

### What goes in Git vs DVC

```text
Git:  code, dvc.yaml, dvc.lock, params.yaml, .dvc files, reports/metrics_dict.json
DVC:  data/, models/ (large files → pushed to S3)
```

---

## DVC (Data Version Control)

### Pipeline

```bash
# Run the full pipeline (only changed stages)
dvc repro

# Force re-run a specific stage
dvc repro -f model_evaluation

# Check what has changed since last run
dvc status

# Visualize the pipeline as a DAG (directed acyclic graph)
dvc dag
```

### Metrics

```bash
# Show current metrics
dvc metrics show

# Compare metrics between current and last commit
dvc metrics diff

# Compare metrics between two specific commits
dvc metrics diff HEAD~2 HEAD
```

### Data Management

```bash
# Push data to S3 remote
dvc push

# Pull data from S3 remote
dvc pull

# Check what would be pushed/pulled
dvc status -c    # -c = cloud (checks remote)
```

### Remote Configuration

```bash
# List configured remotes
dvc remote list

# Add S3 remote as default
dvc remote add -d myremote s3://mlopsminiprojectdvc

# Remove a remote
dvc remote remove localremote

# Modify remote URL
dvc remote modify myremote url s3://new-bucket-name
```

### Workflow: Change Parameters and Re-run

```bash
# 1. Edit params.yaml
# 2. Re-run pipeline
dvc repro
# 3. Check new metrics
dvc metrics show
# 4. Compare with previous
dvc metrics diff
# 5. Push data to S3
dvc push
# 6. Commit changes to Git
git add dvc.lock params.yaml reports/metrics_dict.json
git commit -m "tune C parameter to 10"
git push origin main
```

---

## Python — Running Pipeline Stages

Always use module mode (`python -m`) — not script mode (`python file.py`).

```bash
# Run individual stages
python -m emotional_tweet.dataset
python -m emotional_tweet.data_preprocessing
python -m emotional_tweet.features
python -m emotional_tweet.modeling.train
python -m emotional_tweet.modeling.predict
python -m emotional_tweet.modeling.register_model
```

### Why `-m` (module mode)

```bash
python -m emotional_tweet.dataset       # uses Python import system — correct
python emotional_tweet/dataset.py       # adds script directory to sys.path — can break
```

Module mode ensures `config.py`'s `PROJ_ROOT` resolves correctly. Script mode can import the wrong package if another copy exists nearby.

---

## NLTK

```bash
# Download required NLTK data (needed once)
python -c "import nltk; nltk.download('stopwords'); nltk.download('wordnet')"

# Or using module mode
python -m nltk.downloader stopwords wordnet
```

---

## FastAPI — Running the App

```bash
# From fast_api/ directory
cd fast_api
python app.py

# Or with uvicorn directly (with auto-reload for development)
uvicorn app:app --port 8050 --reload

# Test the endpoints
curl http://localhost:8050/
curl -X POST http://localhost:8050/predict -d "text=I am happy today"
```

**Required:** Set `DAGSHUB_PAT` environment variable before running.

```bash
export DAGSHUB_PAT="your_token_here"
```

---

## Docker

### Build and Run Locally

```bash
# Build the image
docker build -t emotions:v1 .

# Run the container
docker run -d \
  -p 8050:8050 \
  --name my-app \
  -e DAGSHUB_PAT="your_token_here" \
  emotions:v1

# Run interactively (see logs in terminal)
docker run -it \
  -p 8050:8050 \
  -e DAGSHUB_PAT="your_token_here" \
  emotions:v1
```

### Container Management

```bash
# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# View container logs
docker logs my-app

# Follow logs in real-time
docker logs -f my-app

# Stop a container
docker stop my-app

# Remove a container
docker rm my-app

# Remove an image
docker rmi emotions:v1

# Clean up unused images, containers, and cache
docker system prune -af
```

### Docker Hub

```bash
# Login
docker login

# Tag and push
docker tag emotions:v1 <username>/emotions:v1
docker push <username>/emotions:v1

# Pull from Docker Hub
docker pull <username>/emotions:v1
```

---

## AWS CLI

### Configure Credentials

```bash
aws configure
# AWS Access Key ID: <your-key>
# AWS Secret Access Key: <your-secret>
# Default region name: <your-region>
# Default output format: json
```

### S3 Commands (for DVC data)

```bash
# List S3 buckets
aws s3 ls

# List files in DVC bucket
aws s3 ls s3://mlopsminiprojectdvc/

# Copy file to S3
aws s3 cp local-file.csv s3://mlopsminiprojectdvc/

# Download from S3
aws s3 cp s3://mlopsminiprojectdvc/file.csv ./local-file.csv
```

### ECR (Elastic Container Registry)

```bash
# Login to ECR
aws ecr get-login-password --region us-west-2 \
  | docker login --username AWS --password-stdin \
  376129864263.dkr.ecr.us-west-2.amazonaws.com

# Tag image for ECR
docker tag emotions:v1 376129864263.dkr.ecr.us-west-2.amazonaws.com/mlops-mini-project-registry:latest

# Push to ECR
docker push 376129864263.dkr.ecr.us-west-2.amazonaws.com/mlops-mini-project-registry:latest

# Pull from ECR
docker pull 376129864263.dkr.ecr.us-west-2.amazonaws.com/mlops-mini-project-registry:latest
```

---

## AWS EC2 — Server Setup

### SSH into EC2

```bash
# Set key permissions (required by SSH)
chmod 400 mlops-mini-project-keypair.pem

# Connect
ssh -i mlops-mini-project-keypair.pem ubuntu@<EC2-PUBLIC-IP>
```

### Install Docker + AWS CLI on EC2

```bash
# Update packages
sudo apt-get update

# Install Docker
sudo apt-get install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker

# Install required packages
sudo apt-get install -y unzip curl

# Download and install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Add user to docker group (avoids sudo for docker commands)
sudo usermod -aG docker ubuntu

# Log out and back in for group change to take effect
exit
ssh -i mlops-mini-project-keypair.pem ubuntu@<EC2-PUBLIC-IP>

# Configure AWS CLI (after reconnecting)
aws configure
```

### Run the App on EC2 (Docker Hub)

```bash
# Pull the image
docker pull kccsrknnv/emotions:v1

# Run in background
docker run -d \
  --restart unless-stopped \
  -p 80:8050 \
  --name my-app \
  -e DAGSHUB_PAT="f78fe5bc73f4a44d60ebcd6ad5bd9b7b67c5e460" \
  kccsrknnv/emotions:v1
```

### Run the App on EC2 (ECR)

```bash
# Login to ECR
aws ecr get-login-password --region us-west-2 \
  | docker login --username AWS --password-stdin \
  376129864263.dkr.ecr.us-west-2.amazonaws.com

# Pull
docker pull 376129864263.dkr.ecr.us-west-2.amazonaws.com/mlops-mini-project-registry:latest

# Run
docker run -d \
  --restart unless-stopped \
  -p 80:8050 \
  -e DAGSHUB_PAT="f78fe5bc73f4a44d60ebcd6ad5bd9b7b67c5e460" \
  --name my-app \
  376129864263.dkr.ecr.us-west-2.amazonaws.com/mlops-mini-project-registry:latest
```

### Troubleshooting on EC2

```bash
# Check running containers
docker ps

# View container logs
docker logs my-app

# Check what's using a port
sudo lsof -i :80

# Check memory
free -m

# Check disk space
df -h

# Check Docker resource usage
docker stats
```

---

## Testing

```bash
# Run model tests
python -m unittest tests/test_model.py

# Run API tests
python -m unittest tests/test_fast_app.py

# Run all tests
python -m unittest discover -s tests

# Run with verbose output
python -m unittest -v tests/test_model.py

# Run a specific test
python -m unittest tests.test_model.TestModelLoading.test_model_performance
```

---

## Make Commands

```bash
# Show available commands
make help

# Install dependencies
make requirements

# Clean compiled files
make clean

# Lint code
make lint

# Format code
make format
```

---

## Environment Setup (One-time)

```bash
# 1. Create virtual environment
python -m venv .venv
source .venv/bin/activate       # Linux/Mac
# .venv\Scripts\activate        # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download NLTK data
python -c "import nltk; nltk.download('stopwords'); nltk.download('wordnet')"

# 4. Configure AWS (for S3 remote)
aws configure

# 5. Set DagsHub token
echo 'DAGSHUB_PAT=your_token' > .env

# 6. Pull data from DVC
dvc pull

# 7. Verify setup
dvc status
python -m emotional_tweet.dataset
```

---

## GitHub Secrets (for CI/CD)

Set these in GitHub repo → Settings → Secrets and variables → Actions:

| Secret | Value |
|--------|-------|
| `DAGSHUB_PAT` | DagsHub Personal Access Token |
| `DOCKER_HUB_USERNAME` | Docker Hub username |
| `DOCKER_HUB_ACCESS_TOKEN` | Docker Hub access token |
| `EC2_HOST` | EC2 public IP address |
| `EC2_USER` | `ubuntu` (default EC2 username) |
| `EC2_SSH_KEY` | Content of the `.pem` private key file |
