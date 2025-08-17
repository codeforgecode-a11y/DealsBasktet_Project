#!/bin/bash

# Deploy RDS infrastructure for DealsBasket

set -e  # Exit on error

# Configuration
STACK_NAME="dealsbasket-rds"
TEMPLATE_FILE="config/aws/rds-stack.yml"
REGION="us-east-1"
NETWORK_STACK_NAME="dealsbasket-network"

# Get network stack outputs
VPC_ID=$(aws cloudformation describe-stacks --stack-name $NETWORK_STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`VPC`].OutputValue' --output text)
PRIVATE_SUBNETS=$(aws cloudformation describe-stacks --stack-name $NETWORK_STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`PrivateSubnets`].OutputValue' --output text)
RDS_SECURITY_GROUP=$(aws cloudformation describe-stacks --stack-name $NETWORK_STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`RDSSecurityGroup`].OutputValue' --output text)

# Deploy the CloudFormation stack
echo "Deploying RDS infrastructure..."
aws cloudformation deploy \
    --template-file $TEMPLATE_FILE \
    --stack-name $STACK_NAME \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides \
        EnvironmentName=dealsbasket-prod \
        VpcId=$VPC_ID \
        SubnetIds=$PRIVATE_SUBNETS \
        SecurityGroupId=$RDS_SECURITY_GROUP \
    --region $REGION

# Get the outputs
echo "Getting stack outputs..."
aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query 'Stacks[0].Outputs' \
    --output json > config/aws/rds-outputs.json

echo "RDS infrastructure deployment completed successfully!"

# Print important information
echo "DB Endpoint: $(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`DBEndpoint`].OutputValue' --output text)"
echo "DB Port: $(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`DBPort`].OutputValue' --output text)"