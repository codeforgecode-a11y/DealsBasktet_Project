#!/bin/bash

# AWS Deployment Script for DealsBasket

set -e  # Exit on error

# Check if required tools are installed
command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed. Aborting." >&2; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "Docker Compose is required but not installed. Aborting." >&2; exit 1; }
command -v aws >/dev/null 2>&1 || { echo "AWS CLI is required but not installed. Aborting." >&2; exit 1; }

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "Error: AWS CLI is not configured. Please run 'aws configure' first."
    exit 1
fi

# Set default region if not set
AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-ap-south-1}
export AWS_DEFAULT_REGION

echo "Using AWS Region: $AWS_DEFAULT_REGION"

# Load environment variables (optional for deployment)
if [ -f config/aws/.env.aws ]; then
    echo "Loading environment configuration..."
    # Note: This file contains placeholders, actual values come from Parameter Store
else
    echo "Warning: config/aws/.env.aws file not found, using defaults"
fi

# Get AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
if [ $? -ne 0 ]; then
    echo "Error: Failed to get AWS Account ID. Please check your AWS credentials."
    exit 1
fi

# ECR repository name and tag
ECR_REPO="dealsbasket"
IMAGE_TAG="latest"

echo "Starting AWS deployment..."
echo "AWS Account ID: $AWS_ACCOUNT_ID"

# Login to Amazon ECR
echo "Logging in to Amazon ECR..."
if ! aws ecr get-login-password --region $AWS_DEFAULT_REGION | sudo docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com; then
    echo "Error: Failed to log in to ECR"
    exit 1
fi

# Build the Docker image
echo "Building Docker image..."
if ! sudo docker build -t dealsbasket:latest .; then
    echo "Error: Docker build failed"
    exit 1
fi

# Tag the image for ECR
echo "Tagging image for ECR..."
if ! sudo docker tag dealsbasket:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG; then
    echo "Error: Failed to tag Docker image"
    exit 1
fi

# Push the image to ECR
echo "Pushing image to ECR..."
if ! docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG; then
    echo "Error: Failed to push image to ECR"
    exit 1
fi

# Update ECS service
echo "Updating ECS service..."
if ! aws ecs update-service --cluster dealsbasket-cluster --service dealsbasket-service --force-new-deployment --region $AWS_DEFAULT_REGION; then
    echo "Error: Failed to update ECS service"
    exit 1
fi

# Wait for service to stabilize
echo "Waiting for ECS service to stabilize..."
if ! aws ecs wait services-stable --cluster dealsbasket-cluster --services dealsbasket-service --region $AWS_DEFAULT_REGION; then
    echo "Warning: Service may not have stabilized properly"
fi

# Create S3 buckets if they don't exist
echo "Setting up S3 buckets..."
if [ "$AWS_DEFAULT_REGION" = "us-east-1" ]; then
    aws s3api create-bucket --bucket dealsbasket-static --region $AWS_DEFAULT_REGION || true
    aws s3api create-bucket --bucket dealsbasket-media --region $AWS_DEFAULT_REGION || true
else
    aws s3api create-bucket --bucket dealsbasket-static --region $AWS_DEFAULT_REGION --create-bucket-configuration LocationConstraint=$AWS_DEFAULT_REGION || true
    aws s3api create-bucket --bucket dealsbasket-media --region $AWS_DEFAULT_REGION --create-bucket-configuration LocationConstraint=$AWS_DEFAULT_REGION || true
fi

# Sync static files to S3 (if they exist)
if [ -d "staticfiles" ]; then
    echo "Syncing static files to S3..."
    aws s3 sync staticfiles/ s3://dealsbasket-static/ --region $AWS_DEFAULT_REGION
fi

if [ -d "media" ]; then
    echo "Syncing media files to S3..."
    aws s3 sync media/ s3://dealsbasket-media/ --region $AWS_DEFAULT_REGION
fi

# Invalidate CloudFront cache (if distribution exists)
echo "Checking for CloudFront distribution..."
DISTRIBUTION_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[?contains(Aliases.Items, 'dealsbasket')].Id" --output text 2>/dev/null || echo "")
if [ ! -z "$DISTRIBUTION_ID" ] && [ "$DISTRIBUTION_ID" != "None" ]; then
    echo "Invalidating CloudFront cache..."
    aws cloudfront create-invalidation --distribution-id $DISTRIBUTION_ID --paths "/*"
else
    echo "No CloudFront distribution found, skipping cache invalidation"
fi

echo "Deployment completed successfully!"