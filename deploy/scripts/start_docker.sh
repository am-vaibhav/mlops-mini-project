#!/bin/bash

# Start Docker
sudo systemctl start docker

# Login to ECR
aws ecr get-login-password \
    --region us-west-2 \
    | sudo docker login \
    --username AWS \
    --password-stdin \
    376129864263.dkr.ecr.us-west-2.amazonaws.com

# Pull latest image
sudo docker pull \
    376129864263.dkr.ecr.us-west-2.amazonaws.com/mlops-mini-project-registry

# Remove existing container if present
if [ "$(sudo docker ps -aq -f name=^my-app$)" ]; then
    sudo docker stop my-app || true
    sudo docker rm my-app || true
fi

# Run application
sudo docker run -d \
    --restart unless-stopped \
    -p 80:8050 \
    -e DAGSHUB_PAT="f78fe5bc73f4a44d60ebcd6ad5bd9b7b67c5e460" \
    --name my-app \
    376129864263.dkr.ecr.us-west-2.amazonaws.com/mlops-mini-project-registry