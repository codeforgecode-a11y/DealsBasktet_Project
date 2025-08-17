# AWS Deployment Guide for DealsBasket

This guide outlines the steps to deploy DealsBasket on AWS using ECS (Elastic Container Service) with CI/CD pipeline.

## Prerequisites

1. AWS Account with appropriate permissions
2. AWS CLI installed and configured
3. GitHub repository for the project
4. Docker installed locally

## AWS Services Used

- ECR (Elastic Container Registry) - For storing Docker images
- ECS (Elastic Container Service) - For running containers
- RDS (Relational Database Service) - For PostgreSQL database
- ElastiCache - For Redis caching
- S3 - For static and media files
- CloudFront - For CDN
- Route53 - For DNS management
- ACM - For SSL certificates

## Initial Setup

### 1. Create ECR Repository

```bash
aws ecr create-repository \
    --repository-name dealsbasket \
    --image-scanning-configuration scanOnPush=true \
    --region ap-south-1
```

### 2. Create RDS Instance

```bash
aws rds create-db-instance \
    --db-instance-identifier dealsbasket-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --allocated-storage 20 \
    --master-username admin \
    --master-user-password <your-password> \
    --vpc-security-group-ids <security-group-id> \
    --availability-zone ap-south-1a
```

### 3. Create ElastiCache Cluster

```bash
aws elasticache create-cache-cluster \
    --cache-cluster-id dealsbasket-redis \
    --cache-node-type cache.t3.micro \
    --engine redis \
    --num-cache-nodes 1
```

### 4. Create S3 Bucket

```bash
aws s3api create-bucket \
    --bucket dealsbasket-static \
    --region ap-south-1 \
    --create-bucket-configuration LocationConstraint=ap-south-1
```

## GitHub Secrets Setup

Add the following secrets to your GitHub repository:

- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- DB_PASSWORD
- DJANGO_SECRET_KEY
- REDIS_URL

## ECS Configuration

### 1. Create ECS Cluster

```bash
aws ecs create-cluster --cluster-name dealsbasket-cluster
```

### 2. Create Task Definition

Create a task definition JSON file (`task-definition.json`):

```json
{
    "family": "dealsbasket-task",
    "networkMode": "awsvpc",
    "requiresCompatibilities": ["FARGATE"],
    "cpu": "256",
    "memory": "512",
    "containerDefinitions": [
        {
            "name": "dealsbasket-app",
            "image": "<ecr-repo-url>/dealsbasket:latest",
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
                }
            ],
            "secrets": [
                {
                    "name": "DB_PASSWORD",
                    "valueFrom": "<ssm-parameter-arn>"
                }
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/dealsbasket",
                    "awslogs-region": "ap-south-1",
                    "awslogs-stream-prefix": "ecs"
                }
            }
        }
    ]
}
```

Register the task definition:

```bash
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

### 3. Create ECS Service

```bash
aws ecs create-service \
    --cluster dealsbasket-cluster \
    --service-name dealsbasket-service \
    --task-definition dealsbasket-task \
    --desired-count 2 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[<subnet-id-1>,<subnet-id-2>],securityGroups=[<security-group-id>],assignPublicIp=ENABLED}"
```

## CI/CD Pipeline

The GitHub Actions workflow (.github/workflows/deploy.yml) will:

1. Run tests
2. Build Docker image
3. Push to ECR
4. Deploy to ECS

### Workflow Steps:

1. Code is pushed to main branch
2. GitHub Actions workflow is triggered
3. Tests are run
4. Docker image is built
5. Image is pushed to ECR
6. New task definition is created
7. ECS service is updated

## DNS and SSL Setup

1. Create Route53 hosted zone
2. Request SSL certificate in ACM
3. Create CloudFront distribution
4. Update DNS records

## Monitoring

1. Set up CloudWatch alarms for:
   - CPU and Memory usage
   - Request latency
   - Error rates
   - Database connections

2. Configure logging:
   - Application logs to CloudWatch
   - Access logs to S3
   - Error tracking with Sentry

## Cost Optimization

1. Use Spot instances where possible
2. Set up auto-scaling
3. Use CloudFront caching effectively
4. Monitor and optimize RDS and ElastiCache usage

## Security Considerations

1. Use security groups effectively
2. Enable WAF for CloudFront
3. Regular security updates
4. Implement proper backup strategy
5. Use AWS Secrets Manager for sensitive data

## Maintenance

1. Regular database backups
2. Log rotation
3. Security patches
4. Performance monitoring
5. Cost monitoring

## Rollback Procedure

1. Identify the last known good deployment
2. Update ECS service with previous task definition
3. Monitor the rollback
4. Investigate the failure

## Additional Notes

- Keep sensitive information in AWS Secrets Manager
- Use parameter store for configuration
- Implement proper error handling
- Set up alerts for critical issues
- Regular security audits
- Performance optimization
- Regular backups