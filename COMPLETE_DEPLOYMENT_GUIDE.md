# 🚀 Complete AWS Deployment Guide for DealsBasket

## 📋 Overview

This guide provides step-by-step instructions for deploying the DealsBasket Django application to AWS with enterprise-grade security, performance, and monitoring.

## 🔧 Prerequisites

### Required Tools
- AWS CLI v2.x
- Docker
- Python 3.12+
- Git

### AWS Account Setup
- AWS Account with appropriate permissions
- Domain name registered (optional but recommended)
- Route53 hosted zone (if using custom domain)

## 🛡️ Security First - Critical Steps

### 1. Set Up Secrets Management
```bash
# Run the secrets setup script
chmod +x scripts/deployment/setup_secrets.sh
./scripts/deployment/setup_secrets.sh
```

**What this does:**
- Creates secure parameters in AWS Systems Manager
- Generates strong passwords and secret keys
- Sets up IAM policies for parameter access

### 2. Security Audit
```bash
# Run security audit before deployment
chmod +x scripts/deployment/security_audit.sh
./scripts/deployment/security_audit.sh
```

**Fix any CRITICAL issues before proceeding!**

## 🏗️ Infrastructure Deployment

### Step 1: Deploy Network Infrastructure
```bash
aws cloudformation deploy \
  --template-file config/aws/network-stack.yml \
  --stack-name dealsbasket-network \
  --region ap-south-1
```

### Step 2: Deploy Security Stack
```bash
# Get VPC ID from network stack
VPC_ID=$(aws cloudformation describe-stacks \
  --stack-name dealsbasket-network \
  --query "Stacks[0].Outputs[?OutputKey=='VpcId'].OutputValue" \
  --output text)

# Get subnet IDs
PRIVATE_SUBNETS=$(aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=*Private*" \
  --query "Subnets[].SubnetId" --output text | tr '\t' ',')

PUBLIC_SUBNETS=$(aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=*Public*" \
  --query "Subnets[].SubnetId" --output text | tr '\t' ',')

# Deploy security stack
aws cloudformation deploy \
  --template-file config/aws/security-stack.yml \
  --stack-name dealsbasket-security \
  --parameter-overrides \
    VpcId=$VPC_ID \
    PrivateSubnetIds=$PRIVATE_SUBNETS \
    PublicSubnetIds=$PUBLIC_SUBNETS \
  --capabilities CAPABILITY_IAM \
  --region ap-south-1
```

### Step 3: Deploy Database Stack
```bash
# Get security group ID
DB_SG_ID=$(aws cloudformation describe-stacks \
  --stack-name dealsbasket-security \
  --query "Stacks[0].Outputs[?OutputKey=='DatabaseSecurityGroupId'].OutputValue" \
  --output text)

# Deploy RDS stack
aws cloudformation deploy \
  --template-file config/aws/rds-stack.yml \
  --stack-name dealsbasket-rds \
  --parameter-overrides \
    VpcId=$VPC_ID \
    SubnetIds=$PRIVATE_SUBNETS \
    SecurityGroupId=$DB_SG_ID \
  --capabilities CAPABILITY_IAM \
  --region ap-south-1
```

### Step 4: Set Up Database
```bash
# Run database setup script
chmod +x scripts/deployment/setup_database.sh
./scripts/deployment/setup_database.sh
```

### Step 5: Deploy Monitoring Stack
```bash
# Run monitoring setup script
chmod +x scripts/deployment/setup_monitoring_enhanced.sh
./scripts/deployment/setup_monitoring_enhanced.sh
```

### Step 6: Deploy Performance Optimizations
```bash
# Run performance setup script
chmod +x scripts/deployment/setup_performance.sh
./scripts/deployment/setup_performance.sh
```

### Step 7: Set Up SSL/HTTPS (Optional)
```bash
# Run SSL setup script (requires domain)
chmod +x scripts/deployment/setup_ssl.sh
./scripts/deployment/setup_ssl.sh
```

## 🐳 Application Deployment

### Step 1: Build and Push Docker Image
```bash
# Run AWS deployment script
chmod +x scripts/deployment/deploy_aws.sh
./scripts/deployment/deploy_aws.sh
```

### Step 2: Set Up CI/CD Pipeline

1. **GitHub Secrets Setup:**
   ```
   AWS_ACCESS_KEY_ID: Your AWS access key
   AWS_SECRET_ACCESS_KEY: Your AWS secret key
   DOMAIN_NAME: Your domain name (if using SSL)
   ```

2. **Enable GitHub Actions:**
   - Use `.github/workflows/deploy-enhanced.yml`
   - Push to `main` branch triggers deployment

## 🔍 Verification and Testing

### 1. Health Check
```bash
# Check application health
curl https://your-domain.com/health/

# Or using ALB DNS
ALB_DNS=$(aws cloudformation describe-stacks \
  --stack-name dealsbasket-ssl \
  --query "Stacks[0].Outputs[?OutputKey=='LoadBalancerDNS'].OutputValue" \
  --output text)

curl http://$ALB_DNS/health/
```

### 2. Database Connection Test
```bash
# Run database connection test
chmod +x scripts/deployment/test_db_connection.sh
./scripts/deployment/test_db_connection.sh
```

### 3. Performance Test
```bash
# Basic load test
for i in {1..10}; do
  curl -w "%{time_total}\n" -o /dev/null -s https://your-domain.com/api/products/
done
```

## 📊 Monitoring and Maintenance

### CloudWatch Dashboards
- **Application Dashboard:** `dealsbasket-prod-monitoring`
- **Performance Metrics:** Custom namespace `DealsBasket/Application`
- **Security Metrics:** Custom namespace `DealsBasket/Security`

### Key Metrics to Monitor
- **Application:** Response time, error rate, throughput
- **Infrastructure:** CPU, memory, disk usage
- **Database:** Connection count, query performance
- **Cache:** Hit ratio, memory usage

### Alerts Setup
- High CPU/Memory usage
- Database connection issues
- Application errors
- Security events

## 🔧 Troubleshooting

### Common Issues

1. **ECS Service Won't Start**
   ```bash
   # Check service events
   aws ecs describe-services \
     --cluster dealsbasket-cluster \
     --services dealsbasket-service
   ```

2. **Database Connection Issues**
   ```bash
   # Check security groups
   aws ec2 describe-security-groups \
     --group-ids $DB_SG_ID
   ```

3. **SSL Certificate Issues**
   ```bash
   # Check certificate status
   aws acm list-certificates \
     --certificate-statuses ISSUED
   ```

### Log Locations
- **Application Logs:** `/ecs/dealsbasket-prod`
- **Database Logs:** RDS console
- **Load Balancer Logs:** S3 bucket (if enabled)

## 🔄 Updates and Maintenance

### Application Updates
1. Push code to GitHub
2. GitHub Actions automatically deploys
3. Monitor deployment in AWS Console

### Infrastructure Updates
1. Update CloudFormation templates
2. Run `aws cloudformation deploy` commands
3. Test changes in staging first

### Security Updates
1. Regularly rotate secrets
2. Update dependencies
3. Review security audit results

## 📞 Support and Resources

### AWS Resources
- **CloudWatch:** Monitoring and logs
- **ECS Console:** Container management
- **RDS Console:** Database management
- **CloudFormation:** Infrastructure as code

### Documentation
- `AWS_DEPLOYMENT_CHECKLIST.md` - Pre-deployment checklist
- `AUTHENTICATION_SYSTEM.md` - Authentication details
- `API_DOCUMENTATION.md` - API reference

### Emergency Contacts
- AWS Support (if you have a support plan)
- Application team contacts
- Database administrator

## 🎯 Success Criteria

✅ **Deployment Complete When:**
- All health checks pass
- Application accessible via HTTPS
- Database migrations successful
- Monitoring dashboards active
- Security audit passes
- Performance metrics within targets

## 🚨 Rollback Procedure

If deployment fails:

1. **Immediate Rollback:**
   ```bash
   # Rollback ECS service to previous task definition
   aws ecs update-service \
     --cluster dealsbasket-cluster \
     --service dealsbasket-service \
     --task-definition previous-task-definition-arn
   ```

2. **Database Rollback:**
   ```bash
   # Restore from RDS snapshot if needed
   aws rds restore-db-instance-from-db-snapshot \
     --db-instance-identifier dealsbasket-db-rollback \
     --db-snapshot-identifier snapshot-name
   ```

3. **Infrastructure Rollback:**
   ```bash
   # Rollback CloudFormation stacks
   aws cloudformation cancel-update-stack \
     --stack-name stack-name
   ```

---

**🎉 Congratulations!** Your DealsBasket application is now deployed on AWS with enterprise-grade security, performance, and monitoring!
