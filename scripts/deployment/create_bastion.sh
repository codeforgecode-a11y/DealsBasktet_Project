#!/bin/bash

# Set VPC ID
VPC_ID=vpc-06386d67e19c29e01

# Create bastion host security group
echo "Creating security group..."
BASTION_SG_ID=$(aws ec2 create-security-group \
    --group-name dealsbasket-bastion-sg-$(date +%s) \
    --description "Security group for bastion host" \
    --vpc-id $VPC_ID \
    --output text \
    --query 'GroupId')

echo "Created security group: $BASTION_SG_ID"

# Add SSH access from our IP
echo "Adding SSH access rule..."
aws ec2 authorize-security-group-ingress \
    --group-id $BASTION_SG_ID \
    --protocol tcp \
    --port 22 \
    --cidr 152.58.96.171/32

# Set public subnet ID
PUBLIC_SUBNET="subnet-067a20b384a89d09c"
echo "Using public subnet: $PUBLIC_SUBNET"

# Launch bastion host
echo "Launching bastion host..."
aws ec2 run-instances \
    --image-id ami-0e2c86481225d3c51 \
    --instance-type t2.micro \
    --key-name dealsbasket-key \
    --security-group-ids $BASTION_SG_ID \
    --subnet-id $PUBLIC_SUBNET \
    --associate-public-ip-address \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=dealsbasket-bastion}]'