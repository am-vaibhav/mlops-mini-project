#!/bin/bash
# Login to AWS ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 376129864263.dkr.ecr.us-west-2.amazonaws.com

# Pull the latest image
docker pull 376129864263.dkr.ecr.us-west-2.amazonaws.com/mlops-mini-project-registry

# Check if the container 'campusx-app' is running
if [ "$(docker ps -q -f name=my-app)" ]; then
    # Stop the running container
    docker stop my-app
fi

# Check if the container 'campusx-app' exists (stopped or running)
if [ "$(docker ps -aq -f name=my-app)" ]; then
    # Remove the container if it exists
    docker rm my-app
fi

docker run -d \
    --restart unless-stopped \
    -p 80:8050 \
    -e DAGSHUB_PAT="f78fe5bc73f4a44d60ebcd6ad5bd9b7b67c5e460" \
    --name my-app \
    376129864263.dkr.ecr.us-west-2.amazonaws.com/mlops-mini-project-registry