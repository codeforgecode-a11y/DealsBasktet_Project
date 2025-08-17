#!/bin/bash

# Exit on error
set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check for AWS CLI
if ! command -v aws &> /dev/null; then
    echo "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check for required environment variables
required_vars=(
    "AWS_ACCESS_KEY_ID"
    "AWS_SECRET_ACCESS_KEY"
    "AWS_DEFAULT_REGION"
    "DB_PASSWORD"
    "DJANGO_SECRET_KEY"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: $var is not set"
        exit 1
    fi
done

echo "Creating ECR repository..."
aws ecr create-repository \
    --repository-name dealsbasket \
    --image-scanning-configuration scanOnPush=true \
    || true

echo "Creating RDS instance..."
aws rds create-db-instance \
    --db-instance-identifier dealsbasket-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --allocated-storage 20 \
    --master-username dealsbasket_user \
    --master-user-password "$DB_PASSWORD" \
    || true

echo "Creating ElastiCache cluster..."
aws elasticache create-cache-cluster \
    --cache-cluster-id dealsbasket-redis \
    --cache-node-type cache.t3.micro \
    --engine redis \
    --num-cache-nodes 1 \
    || true

echo "Creating S3 bucket..."
aws s3api create-bucket \
    --bucket dealsbasket-static \
    --region $AWS_DEFAULT_REGION \
    --create-bucket-configuration LocationConstraint=$AWS_DEFAULT_REGION \
    || true

echo "Creating ECS cluster..."
aws ecs create-cluster \
    --cluster-name dealsbasket-cluster \
    || true

echo "Creating ECS task definition..."
cat > task-definition.json << EOF
{
    "family": "dealsbasket-task",
    "networkMode": "awsvpc",
    "requiresCompatibilities": ["FARGATE"],
    "cpu": "256",
    "memory": "512",
    "containerDefinitions": [
        {
            "name": "dealsbasket-app",
            "image": "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/dealsbasket:latest",
            "portMappings": [
                {
                    "containerPort": 8000,
                    "protocol": "tcp"
                }
            ],
            "environment": [
                {
                    "name": "DJANGO_SETTINGS_MODULE",
                    "value": "server.settings.production"
                },
                {
                    "name": "DB_NAME",
                    "value": "dealsbasket_db"
                },
                {
                    "name": "DB_USER",
                    "value": "dealsbasket_user"
                },
                {
                    "name": "DB_HOST",
                    "value": "dealsbasket-db.${AWS_DEFAULT_REGION}.rds.amazonaws.com"
                }
            ],
            "secrets": [
                {
                    "name": "DB_PASSWORD",
                    "valueFrom": "${DB_PASSWORD_ARN}"
                },
                {
                    "name": "DJANGO_SECRET_KEY",
                    "valueFrom": "${DJANGO_SECRET_KEY_ARN}"
                }
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/dealsbasket",
                    "awslogs-region": "${AWS_DEFAULT_REGION}",
                    "awslogs-stream-prefix": "ecs"
                }
            }
        }
    ]
}
EOF

echo "Registering task definition..."
aws ecs register-task-definition \
    --cli-input-json file://task-definition.json

echo "Creating ECS service..."
aws ecs create-service \
    --cluster dealsbasket-cluster \
    --service-name dealsbasket-service \
    --task-definition dealsbasket-task \
    --desired-count 2 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[${SUBNET_1},${SUBNET_2}],securityGroups=[${SECURITY_GROUP}],assignPublicIp=ENABLED}" \
    || true

echo "Creating CloudWatch log group..."
aws logs create-log-group \
    --log-group-name /ecs/dealsbasket \
    || true

echo "Setting up parameter store secrets..."
aws ssm put-parameter \
    --name "/dealsbasket/db_password" \
    --value "$DB_PASSWORD" \
    --type SecureString \
    --overwrite

aws ssm put-parameter \
    --name "/dealsbasket/django_secret_key" \
    --value "$DJANGO_SECRET_KEY" \
    --type SecureString \
    --overwrite

echo "Deployment setup complete!"
echo "Next steps:"
echo "1. Configure DNS in Route53"
echo "2. Set up SSL certificate in ACM"
echo "3. Configure GitHub repository secrets"
echo "4. Push code to trigger the CI/CD pipeline"