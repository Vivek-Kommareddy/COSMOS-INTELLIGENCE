#!/bin/bash
set -e

export PATH="/usr/local/bin:$PATH"
export AWS_ACCESS_KEY_ID=""
export AWS_SECRET_ACCESS_KEY=""
export AWS_DEFAULT_REGION="us-east-1"

# Get Account ID and build ECR URL
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=${AWS_DEFAULT_REGION}
ECR_URL="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

echo "Logging into ECR at ${ECR_URL}..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_URL

echo "Ensuring repositories exist..."
aws ecr create-repository --repository-name cosmos-server 2>/dev/null || echo "Repository cosmos-server already exists"
aws ecr create-repository --repository-name cosmos-client 2>/dev/null || echo "Repository cosmos-client already exists"

echo "Building Server..."
docker build --platform linux/amd64 -t cosmos-server ./server

echo "Building Client..."
# We bake the Backend URL into the build so the Next.js standalone server
# has the correct rewrite configuration from the start.
BACKEND_URL="https://bpc53g62fh.us-east-1.awsapprunner.com"
docker build --platform linux/amd64 \
    --build-arg API_URL=${BACKEND_URL} \
    -t cosmos-client ./client

echo "Tagging..."
docker tag cosmos-server:latest ${ECR_URL}/cosmos-server:latest
docker tag cosmos-client:latest ${ECR_URL}/cosmos-client:latest

echo "Pushing Server to ECR..."
docker push ${ECR_URL}/cosmos-server:latest

echo "Pushing Client to ECR..."
docker push ${ECR_URL}/cosmos-client:latest

echo "Successfully pushed containers to AWS ECR!"
