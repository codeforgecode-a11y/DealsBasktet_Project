# AWS Deployment Checklist for DealsBasket

## 🚨 CRITICAL SECURITY FIXES REQUIRED

### 1. Remove Hardcoded Credentials
- [ ] **IMMEDIATE**: Remove AWS credentials from `config/aws/.env.aws`
- [ ] **IMMEDIATE**: Remove database passwords from configuration files
- [ ] **IMMEDIATE**: Remove Django secret key from configuration files
- [ ] Set up AWS Secrets Manager or Parameter Store for sensitive data

### 2. Fix IAM Permissions
- [ ] Replace overly permissive IAM policy with principle of least privilege
- [ ] Create separate roles for ECS tasks and execution
- [ ] Review and update security groups

### 3. Environment Configuration
- [ ] Add missing Cloudinary configuration to AWS environment
- [ ] Add JWT configuration to production environment
- [ ] Configure email settings for production
- [ ] Set up CORS allowed origins

## 📋 PRE-DEPLOYMENT CHECKLIST

### Infrastructure Setup
- [ ] Create VPC and networking (use CloudFormation template)
- [ ] Set up RDS PostgreSQL instance
- [ ] Create ECR repository
- [ ] Set up S3 buckets for static/media files
- [ ] Configure CloudFront distribution
- [ ] Create ECS cluster

### Security Configuration
- [ ] Set up AWS Secrets Manager parameters:
  - `/dealsbasket/django_secret_key`
  - `/dealsbasket/db_password`
  - `/dealsbasket/cloudinary_api_secret`
  - `/dealsbasket/jwt_secret_key`
- [ ] Configure SSL certificate in ACM
- [ ] Set up proper security groups
- [ ] Enable CloudTrail for auditing

### Application Configuration
- [ ] Update task definition with correct region (ap-south-1)
- [ ] Configure health checks
- [ ] Set up CloudWatch logging
- [ ] Configure auto-scaling policies

## 🛠️ DEPLOYMENT STEPS

### 1. Infrastructure Deployment
```bash
# Deploy networking stack
aws cloudformation create-stack \
  --stack-name dealsbasket-network \
  --template-body file://config/aws/network-stack.yml

# Deploy RDS stack
aws cloudformation create-stack \
  --stack-name dealsbasket-rds \
  --template-body file://config/aws/rds-stack.yml \
  --parameters ParameterKey=VpcId,ParameterValue=<VPC_ID>
```

### 2. Secrets Management
```bash
# Store secrets in Parameter Store
aws ssm put-parameter \
  --name "/dealsbasket/django_secret_key" \
  --value "$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')" \
  --type SecureString

aws ssm put-parameter \
  --name "/dealsbasket/db_password" \
  --value "YOUR_SECURE_DB_PASSWORD" \
  --type SecureString
```

### 3. Container Deployment
```bash
# Build and push Docker image
./scripts/deployment/deploy_aws.sh
```

## ⚠️ IDENTIFIED ISSUES

### Critical Issues
1. **Exposed AWS Credentials**: Hardcoded in environment file
2. **Weak Database Password**: Simple password exposed in plain text
3. **Overly Permissive IAM**: Grants * permissions to all resources
4. **Missing SSL Configuration**: HTTPS not properly configured
5. **Empty Task Definition**: Main task definition file is empty

### Configuration Issues
1. **Region Mismatch**: Scripts use us-east-1 but config uses ap-south-1
2. **Missing Environment Variables**: Cloudinary and JWT configs missing
3. **No Connection Pooling**: Database connections not optimized
4. **Missing Monitoring**: No application monitoring setup

### Security Concerns
1. **No WAF Protection**: Web Application Firewall not configured
2. **Public S3 Buckets**: Static bucket configured as public-read
3. **No VPC Endpoints**: Direct internet access for AWS services
4. **Missing Backup Strategy**: No automated backups configured

## 🔧 RECOMMENDED IMPROVEMENTS

### Security Enhancements
- [ ] Implement AWS WAF for API protection
- [ ] Use VPC endpoints for AWS services
- [ ] Enable GuardDuty for threat detection
- [ ] Set up AWS Config for compliance monitoring

### Performance Optimizations
- [ ] Implement database connection pooling
- [ ] Set up Redis for caching
- [ ] Configure CloudFront caching policies
- [ ] Implement auto-scaling for ECS

### Monitoring & Logging
- [ ] Set up CloudWatch dashboards
- [ ] Configure application metrics
- [ ] Implement log aggregation
- [ ] Set up alerting for critical events

### Backup & Recovery
- [ ] Enable RDS automated backups
- [ ] Set up cross-region replication
- [ ] Implement disaster recovery plan
- [ ] Test backup restoration procedures

## 📝 NEXT STEPS

1. **Immediate (Before Deployment)**:
   - Fix all security issues
   - Set up AWS Secrets Manager
   - Update IAM policies
   - Test deployment in staging environment

2. **Short Term (Within 1 Week)**:
   - Implement monitoring and alerting
   - Set up backup strategies
   - Configure auto-scaling
   - Performance testing

3. **Long Term (Within 1 Month)**:
   - Implement CI/CD pipeline
   - Set up disaster recovery
   - Security audit and penetration testing
   - Documentation and runbooks

## 🚀 DEPLOYMENT COMMAND

After fixing all issues, deploy using:
```bash
# 1. Set up infrastructure
./scripts/deployment/setup_aws.sh

# 2. Deploy application
./scripts/deployment/deploy_aws.sh

# 3. Verify deployment
curl https://your-domain.com/health/
```

## 📞 SUPPORT

For deployment issues, check:
- CloudWatch logs: `/ecs/dealsbasket`
- ECS service events
- Application health endpoint: `/health/`
