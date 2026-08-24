Deployment — Docker + CI/CD + AWS EC2
======================================

The app is containerized with Docker, built and pushed via GitHub Actions, and deployed to an AWS EC2 instance automatically on every push to `main`.

## Full Deployment Flow

```text
git push to main
    │
    ▼
GitHub Actions CI Pipeline
    │
    ├── 1. Install dependencies (pip install -r requirements.txt)
    ├── 2. Run DVC pipeline (dvc repro)
    ├── 3. Build Docker image
    ├── 4. Push image to Docker Hub
    └── 5. SSH into EC2 → pull image → restart container
```

---

## Dockerfile

**File:** `Dockerfile` (project root)

```dockerfile
FROM python:3.12-slim-bookworm

WORKDIR /app

COPY fast_api/ /app/
COPY models/vectorizer.pkl /app/models/vectorizer.pkl

RUN pip install -r requirements.txt

RUN python -m nltk.downloader stopwords wordnet

EXPOSE 8050

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8050", "--log-level", "info"]
```

### What each line does

| Line | Purpose |
|------|---------|
| `FROM python:3.12-slim-bookworm` | Base image — slim Python 3.12 (small size) |
| `WORKDIR /app` | Set working directory inside container |
| `COPY fast_api/ /app/` | Copy app code (app.py, preprocessing_utility.py, templates/, requirements.txt) |
| `COPY models/vectorizer.pkl /app/models/` | Copy the TF-IDF vectorizer (needed for feature extraction) |
| `RUN pip install -r requirements.txt` | Install Python dependencies |
| `RUN python -m nltk.downloader stopwords wordnet` | Download NLTK data (needed for text preprocessing) |
| `EXPOSE 8050` | Document which port the app uses |
| `CMD [...]` | Start uvicorn server on port 8050 |

### What's NOT in the Docker image

- **The ML model** — downloaded from MLflow registry at startup, not baked into the image
- **DAGSHUB_PAT** — passed as environment variable at runtime (`-e DAGSHUB_PAT=...`)
- **Project data** (data/, reports/) — not needed for serving

### Why `uvicorn app:app` not `python -m`

`uvicorn app:app` tells uvicorn to import `app` from `app.py` — it uses Python's import system internally, so there's no `sys.path` issue. This is the standard way to run FastAPI apps.

---

## GitHub Actions CI Pipeline

**File:** `.github/workflows/ci.yaml`

### Pipeline Steps

```text
1. Checkout code
2. Setup Python 3.12
3. Cache pip dependencies (speeds up builds)
4. Install dependencies
5. Run DVC pipeline (dvc repro)
6. Login to Docker Hub
7. Build Docker image
8. Push image to Docker Hub
9. SSH into EC2 and deploy
```

### GitHub Secrets Required

| Secret | What it is |
|--------|-----------|
| `DAGSHUB_PAT` | DagsHub Personal Access Token (for MLflow) |
| `DOCKER_HUB_USERNAME` | Docker Hub username |
| `DOCKER_HUB_ACCESS_TOKEN` | Docker Hub access token |
| `EC2_HOST` | EC2 public IP address |
| `EC2_USER` | SSH username (usually `ubuntu`) |
| `EC2_SSH_KEY` | Private SSH key content (the .pem file content) |

### The Deploy Step

```yaml
- name: Deploy to EC2
  uses: appleboy/ssh-action@v0.1.5
  with:
    host: ${{ secrets.EC2_HOST }}
    username: ${{ secrets.EC2_USER }}
    key: ${{ secrets.EC2_SSH_KEY }}
    script: |
      docker stop my-app || true 
      docker rm my-app || true
      docker system prune -af
      docker pull ${{ secrets.DOCKER_HUB_USERNAME }}/emotions:v1
      docker run -d \
        --restart unless-stopped \
        -p 80:8050 \
        --name my-app \
        -e DAGSHUB_PAT=${{ secrets.DAGSHUB_PAT }} \
        ${{ secrets.DOCKER_HUB_USERNAME }}/emotions:v1
```

What this does:
1. Stops and removes the old container (if running) — `|| true` prevents failure if container doesn't exist
2. `docker system prune -af` — removes all unused images, containers, and build cache to free disk space on the EC2 instance (important for small instances with limited storage)
3. Pulls the latest image from Docker Hub
4. Starts a new container:
   - `-d` — run in background (detached)
   - `--restart unless-stopped` — auto-restart on crash or server reboot
   - `-p 80:8050` — map host port 80 to container port 8050
   - `-e DAGSHUB_PAT=...` — pass the DagsHub token as environment variable
   - `--name my-app` — name the container for easy management

---

## AWS EC2 Setup — Step by Step

### 1. SSH Key Setup

```bash
# Set correct permissions on the key file (required by SSH)
chmod 400 mlops-mini-project-keypair.pem

# Connect to EC2
ssh -i mlops-mini-project-keypair.pem ubuntu@<EC2-PUBLIC-IP>
```

`chmod 400` makes the key file read-only for the owner. SSH refuses to use keys with open permissions (security requirement).

### 2. Install Docker on EC2

```bash
# Update package list
sudo apt-get update

# Install Docker
sudo apt-get install -y docker.io

# Start Docker and enable on boot
sudo systemctl start docker
sudo systemctl enable docker

# Add ubuntu user to docker group (avoids needing sudo for docker commands)
sudo usermod -aG docker ubuntu
```

After `usermod`, log out and back in for the group change to take effect.

### 3. Run the App Manually (for testing)

```bash
# Pull the image
docker pull <dockerhub-username>/emotions:v1

# Run interactively (see logs in terminal)
docker run -it -p 8050:8050 \
  -e DAGSHUB_PAT="<your-token>" \
  <dockerhub-username>/emotions:v1

# Run in background (detached)
docker run -d \
  --restart unless-stopped \
  -p 80:8050 \
  --name my-app \
  -e DAGSHUB_PAT="<your-token>" \
  <dockerhub-username>/emotions:v1
```

### 4. Useful Docker Commands on EC2

```bash
# Check running containers
docker ps

# Check all containers (including stopped)
docker ps -a

# View container logs
docker logs my-app

# Stop the container
docker stop my-app

# Remove the container
docker rm my-app

# Remove the image
docker rmi <image-name>

# Check what's using a port
sudo lsof -i :80
```

---

## Port Mapping Explained

```text
-p 80:8050
    │   │
    │   └── Container port (where uvicorn listens inside Docker)
    │
    └── Host port (where users access from the internet)
```

- Users visit `http://<EC2-IP>:80` (or just `http://<EC2-IP>` since 80 is default HTTP)
- Docker forwards that to port 8050 inside the container
- If port 80 is already in use (nginx, apache), use a different host port: `-p 8050:8050`

### EC2 Security Group

Make sure your EC2 security group allows inbound traffic on the host port:

| Type | Port | Source |
|------|------|--------|
| HTTP | 80 | 0.0.0.0/0 |
| Custom TCP | 8050 | 0.0.0.0/0 (if using port 8050) |
| SSH | 22 | Your IP |

---

## Common Issues

### `port is already allocated`

```
Bind for 0.0.0.0:80 failed: port is already allocated
```

Something else is using port 80. Fix:
```bash
sudo lsof -i :80                    # find what's using it
# Either stop that service, or use a different port (-p 8050:8050)
```

### `permission denied` for docker commands

```
permission denied while trying to connect to the docker API
```

Either use `sudo` or add your user to the docker group:
```bash
sudo usermod -aG docker ubuntu
# Log out and back in
```

### `No such container: my-app`

```
Error response from daemon: No such container: my-app
```

This is expected on first deploy — `docker stop my-app || true` handles it with `|| true` so it doesn't fail the pipeline.

### EC2 IP changes after stop/start

EC2 instances get a new public IP when stopped and started. Solutions:
- Use an **Elastic IP** (static IP that persists)
- Update `EC2_HOST` secret in GitHub after each IP change

### SSH `broken pipe` or connection drops

The EC2 instance may have limited memory. Check with:
```bash
free -m
docker stats
```

If memory is tight, the SSH session may be killed when Docker downloads the model at startup (MLflow model download uses RAM).

---

## Deployment Architecture

```text
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Developer  │      │   GitHub     │      │   AWS EC2    │
│              │      │   Actions    │      │              │
│  git push ──────────▶ CI Pipeline ─────────▶ Docker      │
│              │      │              │      │ Container    │
└──────────────┘      │  ┌────────┐  │      │              │
                      │  │Docker  │  │      │  ┌────────┐  │
                      │  │ Hub    │◀─┘      │  │FastAPI │  │
                      │  └────┬───┘         │  │  App   │  │
                      │       │             │  └───┬────┘  │
                      └───────┼─────────────┘      │       │
                              │    docker pull     │       │
                              └────────────────────┘       │
                                                           │
                      ┌──────────────┐                     │
                      │   DagsHub    │   mlflow.load_model │
                      │   MLflow     │◀────────────────────┘
                      │   Registry   │
                      └──────────────┘
```

---

## Alternative: AWS ECR Deployment

Instead of Docker Hub, you can push images to AWS Elastic Container Registry (ECR). This is useful when your infrastructure is fully on AWS.

### EC2 Full Setup (from scratch)

```bash
# 1. Update EC2
sudo apt-get update

# 2. Install Docker
sudo apt-get install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker

# 3. Install required packages
sudo apt-get install -y unzip curl

# 4. Download and install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# 5. Allow ubuntu user to use Docker without sudo
sudo usermod -aG docker ubuntu

# 6. Exit and reconnect (for group change to take effect)
exit
```

After reconnecting:

```bash
# 7. Configure AWS CLI
aws configure
# AWS Access Key ID: <your-key>
# AWS Secret Access Key: <your-secret>
# Default region name: us-west-2
# Default output format: json

# 8. Login to AWS ECR
aws ecr get-login-password --region us-west-2 \
  | docker login --username AWS --password-stdin \
  376129864263.dkr.ecr.us-west-2.amazonaws.com

# 9. Pull the image
docker pull 376129864263.dkr.ecr.us-west-2.amazonaws.com/mlops-mini-project-registry:latest

# 10. Run the container
docker run -d \
  --restart unless-stopped \
  -p 80:8050 \
  -e DAGSHUB_PAT="<YOUR_DAGSHUB_PAT>" \
  --name my-app \
  376129864263.dkr.ecr.us-west-2.amazonaws.com/mlops-mini-project-registry:latest
```

### Complete flow

```text
EC2
 │
 ├── apt update
 ├── install Docker
 ├── start Docker
 ├── enable Docker
 │
 ├── install AWS CLI
 │
 ├── add ubuntu → docker group
 │
 ├── reconnect SSH
 │
 ├── aws configure
 │
 ├── ECR login
 │
 ├── docker pull
 │
 └── docker run -d
        │
        └── Application :8050
                 │
                 └── EC2 port 80
```

---

## AMI + User Data Deployment

For production, you can create an AMI (Amazon Machine Image) with Docker and AWS CLI pre-installed, then use EC2 **User Data** to deploy automatically on instance launch.

### What goes in the AMI

```text
AMI
│
├── Ubuntu
├── Docker installed
├── AWS CLI installed
├── Docker configured
└── Required application setup
```

You create this AMI once from a manually set up EC2 instance, then launch new instances from it.

### User Data script (runs on instance launch)

```bash
#!/bin/bash

# Start Docker
sudo systemctl start docker

# Login to ECR
aws ecr get-login-password --region us-west-2 \
    | sudo docker login --username AWS --password-stdin \
    376129864263.dkr.ecr.us-west-2.amazonaws.com

# Pull latest image
sudo docker pull \
    376129864263.dkr.ecr.us-west-2.amazonaws.com/mlops-mini-project-registry:latest

# Remove existing container if present
if [ "$(sudo docker ps -aq -f name=^my-app$)" ]; then
    sudo docker stop my-app || true
    sudo docker rm my-app || true
fi

# Run application
sudo docker run -d \
    --restart unless-stopped \
    -p 80:8050 \
    -e DAGSHUB_PAT="<YOUR_DAGSHUB_PAT>" \
    --name my-app \
    376129864263.dkr.ecr.us-west-2.amazonaws.com/mlops-mini-project-registry:latest
```

### What happens when EC2 launches from AMI

```text
Launch EC2 from AMI
        │
        ▼
  EC2 starts
        │
        ▼
  User Data runs
        │
        ▼
  Start Docker
        │
        ▼
  Login to ECR
        │
        ▼
  Pull image
        │
        ▼
  docker run -d
        │
        ▼
  FastAPI :8050
        │
        ▼
  EC2 :80
```

### Why ECR login is needed in User Data

When you launch a **new** EC2 instance from the AMI, the Docker image is not present locally — it was never pulled on this instance. So the User Data script must:

1. Login to ECR (authenticate)
2. Pull the image (download)
3. Run the container (start)

Without the login + pull steps, `docker run` fails with "image not found".

### Production secrets: don't hardcode

Don't put secrets directly in User Data:

```bash
# Bad — credential visible in EC2 metadata
-e DAGSHUB_PAT="actual-secret-value"
```

Better approaches:

| Method | How |
|--------|-----|
| **AWS Secrets Manager** | Store `DAGSHUB_PAT` as a secret, fetch at runtime |
| **SSM Parameter Store** | Store as a parameter, read with `aws ssm get-parameter` |
| **IAM Role** | Attach to EC2 for ECR permissions (no access keys needed) |

Example with SSM Parameter Store:

```bash
# In User Data script
DAGSHUB_PAT=$(aws ssm get-parameter \
    --name "/myapp/dagshub_pat" \
    --with-decryption \
    --query "Parameter.Value" \
    --output text)

sudo docker run -d \
    -p 80:8050 \
    -e DAGSHUB_PAT="$DAGSHUB_PAT" \
    --name my-app \
    376129864263.dkr.ecr.us-west-2.amazonaws.com/mlops-mini-project-registry:latest
```

For ECR authentication, attaching an **IAM Role** to the EC2 instance eliminates the need for `aws configure` with long-lived access keys entirely.

### Docker Hub vs ECR comparison

| | Docker Hub | AWS ECR |
|---|---|---|
| **Setup** | `docker login` with username/token | `aws ecr get-login-password` |
| **CI/CD** | `docker push username/image:tag` | `docker push account.dkr.ecr.region.amazonaws.com/repo:tag` |
| **Cost** | Free tier: 1 private repo | Pay per storage + transfer |
| **Integration** | Works anywhere | Best with AWS (IAM roles, CodeDeploy) |
| **This project** | Used in current CI/CD | Alternative approach |
