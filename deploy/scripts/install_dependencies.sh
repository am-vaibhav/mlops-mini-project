#!/bin/bash

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