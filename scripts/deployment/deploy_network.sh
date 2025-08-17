#!/bin/bash

# Deploy network infrastructure for DealsBasket

set -e  # Exit on error

# Configuration
STACK_NAME="dealsbasket-network"
TEMPLATE_FILE="config/aws/network-stack.yml"
REGION="us-east-1"

# Deploy the CloudFormation stack
echo "Deploying network infrastructure..."
aws cloudformation deploy \
    --template-file $TEMPLATE_FILE \
    --stack-name $STACK_NAME \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides \
        EnvironmentName=dealsbasket-prod \
    --region $REGION

# Get the outputs
echo "Getting stack outputs..."
aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query 'Stacks[0].Outputs' \
    --output json > config/aws/network-outputs.json

echo "Network infrastructure deployment completed successfully!"

# Print important information
echo "VPC ID: $(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`VPC`].OutputValue' --output text)"
echo "Public Subnets: $(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`PublicSubnets`].OutputValue' --output text)"
echo "Private Subnets: $(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`PrivateSubnets`].OutputValue' --output text)"
echo "ECS Security Group: $(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`ECSSecurityGroup`].OutputValue' --output text)"
echo "RDS Security Group: $(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`RDSSecurityGroup`].OutputValue' --output text)"