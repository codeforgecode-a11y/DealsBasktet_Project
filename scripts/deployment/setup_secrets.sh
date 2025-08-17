#!/bin/bash

# AWS Secrets Management Setup for DealsBasket
# This script sets up secure parameter storage in AWS Systems Manager

set -e

echo "🔐 Setting up AWS Secrets Management for DealsBasket..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Get AWS region from config or use default
AWS_REGION=$(aws configure get region || echo "ap-south-1")
echo "📍 Using AWS Region: $AWS_REGION"

# Check if secrets already exist in a different region
echo "🔍 Checking for existing secrets..."
EXISTING_REGION=""
for region in us-east-1 ap-south-1 us-west-2 eu-west-1; do
    if aws ssm get-parameter --name "/dealsbasket/django_secret_key" --region "$region" &> /dev/null; then
        EXISTING_REGION="$region"
        echo "⚠️  Found existing secrets in region: $EXISTING_REGION"
        break
    fi
done

if [ ! -z "$EXISTING_REGION" ] && [ "$EXISTING_REGION" != "$AWS_REGION" ]; then
    echo "⚠️  Secrets exist in $EXISTING_REGION but current region is $AWS_REGION"
    read -p "Do you want to use existing secrets in $EXISTING_REGION? (y/n): " USE_EXISTING
    if [ "$USE_EXISTING" = "y" ] || [ "$USE_EXISTING" = "Y" ]; then
        AWS_REGION="$EXISTING_REGION"
        echo "✅ Using existing secrets in region: $AWS_REGION"
    fi
fi

# Function to generate secure random password
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Function to create or update parameter
create_parameter() {
    local name=$1
    local value=$2
    local description=$3
    
    echo "📝 Creating parameter: $name"
    
    if aws ssm get-parameter --name "$name" --region "$AWS_REGION" &> /dev/null; then
        echo "⚠️  Parameter $name already exists. Updating..."
        aws ssm put-parameter \
            --name "$name" \
            --value "$value" \
            --type "SecureString" \
            --description "$description" \
            --overwrite \
            --region "$AWS_REGION"
    else
        aws ssm put-parameter \
            --name "$name" \
            --value "$value" \
            --type "SecureString" \
            --description "$description" \
            --region "$AWS_REGION"
    fi
    
    echo "✅ Parameter $name created/updated successfully"
}

# Generate Django secret key
echo "🔑 Generating Django secret key..."
DJANGO_SECRET_KEY=$(python3 -c "
import secrets
import string
alphabet = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
secret_key = ''.join(secrets.choice(alphabet) for i in range(50))
print(secret_key)
")

# Generate database password
echo "🔑 Generating database password..."
DB_PASSWORD=$(generate_password)

# Generate JWT secret key
echo "🔑 Generating JWT secret key..."
JWT_SECRET_KEY=$(python3 -c "
import secrets
import string
alphabet = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
jwt_secret = ''.join(secrets.choice(alphabet) for i in range(64))
print(jwt_secret)
")

# Create parameters in AWS Systems Manager
echo "📦 Creating parameters in AWS Systems Manager..."

create_parameter "/dealsbasket/django_secret_key" "$DJANGO_SECRET_KEY" "Django secret key for DealsBasket application"
create_parameter "/dealsbasket/db_password" "$DB_PASSWORD" "Database password for DealsBasket RDS instance"
create_parameter "/dealsbasket/jwt_secret_key" "$JWT_SECRET_KEY" "JWT secret key for DealsBasket authentication"

# Prompt for Cloudinary credentials
echo ""
echo "🌤️  Cloudinary Configuration"
echo "Please enter your Cloudinary credentials:"
read -p "Cloudinary Cloud Name: " CLOUDINARY_CLOUD_NAME
read -p "Cloudinary API Key: " CLOUDINARY_API_KEY
read -s -p "Cloudinary API Secret: " CLOUDINARY_API_SECRET
echo ""

if [ ! -z "$CLOUDINARY_CLOUD_NAME" ] && [ ! -z "$CLOUDINARY_API_KEY" ] && [ ! -z "$CLOUDINARY_API_SECRET" ]; then
    create_parameter "/dealsbasket/cloudinary_cloud_name" "$CLOUDINARY_CLOUD_NAME" "Cloudinary cloud name for DealsBasket"
    create_parameter "/dealsbasket/cloudinary_api_key" "$CLOUDINARY_API_KEY" "Cloudinary API key for DealsBasket"
    create_parameter "/dealsbasket/cloudinary_api_secret" "$CLOUDINARY_API_SECRET" "Cloudinary API secret for DealsBasket"
else
    echo "⚠️  Skipping Cloudinary configuration (empty values provided)"
fi

# Prompt for email configuration
echo ""
echo "📧 Email Configuration"
echo "Please enter your email service credentials:"
read -p "Email Host (e.g., smtp.gmail.com): " EMAIL_HOST
read -p "Email Port (e.g., 587): " EMAIL_PORT
read -p "Email Username: " EMAIL_HOST_USER
read -s -p "Email Password: " EMAIL_HOST_PASSWORD
echo ""
read -p "Default From Email: " DEFAULT_FROM_EMAIL

if [ ! -z "$EMAIL_HOST" ] && [ ! -z "$EMAIL_HOST_USER" ] && [ ! -z "$EMAIL_HOST_PASSWORD" ]; then
    create_parameter "/dealsbasket/email_host" "$EMAIL_HOST" "Email host for DealsBasket notifications"
    create_parameter "/dealsbasket/email_port" "${EMAIL_PORT:-587}" "Email port for DealsBasket notifications"
    create_parameter "/dealsbasket/email_host_user" "$EMAIL_HOST_USER" "Email username for DealsBasket notifications"
    create_parameter "/dealsbasket/email_host_password" "$EMAIL_HOST_PASSWORD" "Email password for DealsBasket notifications"
    create_parameter "/dealsbasket/default_from_email" "$DEFAULT_FROM_EMAIL" "Default from email for DealsBasket notifications"
else
    echo "⚠️  Skipping email configuration (empty values provided)"
fi

# Create IAM policy for ECS to access parameters
echo ""
echo "🔐 Creating IAM policy for parameter access..."

cat > /tmp/dealsbasket-parameter-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameter",
                "ssm:GetParameters",
                "ssm:GetParametersByPath"
            ],
            "Resource": [
                "arn:aws:ssm:${AWS_REGION}:*:parameter/dealsbasket/*"
            ]
        }
    ]
}
EOF

# Create or update the policy
POLICY_ARN="arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/DealsBasketParameterAccess"

if aws iam get-policy --policy-arn "$POLICY_ARN" &> /dev/null; then
    echo "⚠️  Policy already exists. Creating new version..."
    aws iam create-policy-version \
        --policy-arn "$POLICY_ARN" \
        --policy-document file:///tmp/dealsbasket-parameter-policy.json \
        --set-as-default
else
    echo "📝 Creating new IAM policy..."
    aws iam create-policy \
        --policy-name "DealsBasketParameterAccess" \
        --policy-document file:///tmp/dealsbasket-parameter-policy.json \
        --description "Policy for DealsBasket ECS tasks to access SSM parameters"
fi

# Clean up temporary file
rm /tmp/dealsbasket-parameter-policy.json

echo ""
echo "✅ Secrets management setup completed successfully!"
echo ""
echo "📋 Summary of created parameters:"
echo "  - /dealsbasket/django_secret_key"
echo "  - /dealsbasket/db_password"
echo "  - /dealsbasket/jwt_secret_key"
echo "  - /dealsbasket/cloudinary_* (if provided)"
echo "  - /dealsbasket/email_* (if provided)"
echo ""
echo "🔗 Next steps:"
echo "  1. Update your ECS task role to include the DealsBasketParameterAccess policy"
echo "  2. Update your task definition to use these parameters as secrets"
echo "  3. Remove hardcoded credentials from your configuration files"
echo ""
echo "💡 To retrieve a parameter value:"
echo "  aws ssm get-parameter --name '/dealsbasket/django_secret_key' --with-decryption --region $AWS_REGION"
