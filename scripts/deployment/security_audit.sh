#!/bin/bash

# Security Audit Script for DealsBasket AWS Deployment
# This script performs security checks and recommendations

set -e

echo "🔒 Starting security audit for DealsBasket deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

# Function to print results
print_result() {
    local status=$1
    local message=$2
    
    case $status in
        "PASS")
            echo -e "${GREEN}✅ PASS${NC}: $message"
            ((PASS_COUNT++))
            ;;
        "WARN")
            echo -e "${YELLOW}⚠️  WARN${NC}: $message"
            ((WARN_COUNT++))
            ;;
        "FAIL")
            echo -e "${RED}❌ FAIL${NC}: $message"
            ((FAIL_COUNT++))
            ;;
    esac
}

# Check AWS CLI configuration
echo "🔍 Checking AWS CLI configuration..."
if aws sts get-caller-identity &> /dev/null; then
    print_result "PASS" "AWS CLI is configured"
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    AWS_REGION=$(aws configure get region || echo "ap-south-1")
    echo "   Account ID: $AWS_ACCOUNT_ID"
    echo "   Region: $AWS_REGION"
else
    print_result "FAIL" "AWS CLI not configured"
    exit 1
fi

# Check for hardcoded credentials
echo ""
echo "🔍 Checking for hardcoded credentials..."
if grep -r "AKIA" config/ 2>/dev/null | grep -v template; then
    print_result "FAIL" "Hardcoded AWS access keys found in config files"
else
    print_result "PASS" "No hardcoded AWS access keys found"
fi

if grep -r "password.*=" config/ 2>/dev/null | grep -v template | grep -v "use_aws_parameter_store"; then
    print_result "FAIL" "Hardcoded passwords found in config files"
else
    print_result "PASS" "No hardcoded passwords found"
fi

# Check Parameter Store secrets
echo ""
echo "🔍 Checking AWS Parameter Store secrets..."
required_params=(
    "/dealsbasket/django_secret_key"
    "/dealsbasket/db_password"
    "/dealsbasket/jwt_secret_key"
)

for param in "${required_params[@]}"; do
    if aws ssm get-parameter --name "$param" --region "$AWS_REGION" &> /dev/null; then
        print_result "PASS" "Parameter $param exists"
    else
        print_result "FAIL" "Parameter $param not found"
    fi
done

# Check IAM policies
echo ""
echo "🔍 Checking IAM policies..."
POLICY_ARN="arn:aws:iam::$AWS_ACCOUNT_ID:policy/DealsBasketParameterAccess"
if aws iam get-policy --policy-arn "$POLICY_ARN" &> /dev/null; then
    print_result "PASS" "DealsBasketParameterAccess policy exists"
    
    # Check if policy is too permissive
    POLICY_VERSION=$(aws iam get-policy --policy-arn "$POLICY_ARN" --query 'Policy.DefaultVersionId' --output text)
    POLICY_DOC=$(aws iam get-policy-version --policy-arn "$POLICY_ARN" --version-id "$POLICY_VERSION" --query 'PolicyVersion.Document' --output json)
    
    if echo "$POLICY_DOC" | grep -q '"Resource": "\*"'; then
        print_result "WARN" "IAM policy uses wildcard resources - consider restricting"
    else
        print_result "PASS" "IAM policy follows principle of least privilege"
    fi
else
    print_result "FAIL" "DealsBasketParameterAccess policy not found"
fi

# Check ECS task definition
echo ""
echo "🔍 Checking ECS task definition..."
if [ -f "task-definition-v6.json" ]; then
    if [ -s "task-definition-v6.json" ]; then
        print_result "PASS" "Task definition file exists and is not empty"
        
        # Check for secrets usage
        if grep -q "secrets" task-definition-v6.json; then
            print_result "PASS" "Task definition uses AWS secrets"
        else
            print_result "WARN" "Task definition doesn't use AWS secrets"
        fi
        
        # Check for health checks
        if grep -q "healthCheck" task-definition-v6.json; then
            print_result "PASS" "Task definition includes health checks"
        else
            print_result "WARN" "Task definition missing health checks"
        fi
    else
        print_result "FAIL" "Task definition file is empty"
    fi
else
    print_result "FAIL" "Task definition file not found"
fi

# Check CloudFormation templates
echo ""
echo "🔍 Checking CloudFormation templates..."
templates=(
    "config/aws/cloudformation.yml"
    "config/aws/rds-stack.yml"
    "config/aws/security-stack.yml"
)

for template in "${templates[@]}"; do
    if [ -f "$template" ]; then
        print_result "PASS" "Template $template exists"
        
        # Validate template syntax
        if aws cloudformation validate-template --template-body "file://$template" &> /dev/null; then
            print_result "PASS" "Template $template is valid"
        else
            print_result "FAIL" "Template $template has syntax errors"
        fi
    else
        print_result "WARN" "Template $template not found"
    fi
done

# Check for SSL/TLS configuration
echo ""
echo "🔍 Checking SSL/TLS configuration..."
if grep -q "ssl" nginx.conf; then
    print_result "PASS" "Nginx SSL configuration found"
else
    print_result "WARN" "Nginx SSL configuration not found"
fi

if grep -q "SECURE_SSL_REDIRECT.*True" server/settings/production.py; then
    print_result "PASS" "Django SSL redirect enabled"
else
    print_result "WARN" "Django SSL redirect not enabled"
fi

# Check database security
echo ""
echo "🔍 Checking database security..."
if grep -q "sslmode.*require" server/settings/production.py; then
    print_result "PASS" "Database SSL connection required"
else
    print_result "WARN" "Database SSL connection not required"
fi

if grep -q "StorageEncrypted.*true" config/aws/rds-stack.yml; then
    print_result "PASS" "RDS encryption enabled"
else
    print_result "WARN" "RDS encryption not enabled"
fi

# Check for monitoring and logging
echo ""
echo "🔍 Checking monitoring and logging..."
if grep -q "logConfiguration" task-definition-v6.json; then
    print_result "PASS" "ECS logging configured"
else
    print_result "WARN" "ECS logging not configured"
fi

if grep -q "EnablePerformanceInsights.*true" config/aws/rds-stack.yml; then
    print_result "PASS" "RDS Performance Insights enabled"
else
    print_result "WARN" "RDS Performance Insights not enabled"
fi

# Check for backup configuration
echo ""
echo "🔍 Checking backup configuration..."
if grep -q "BackupRetentionPeriod" config/aws/rds-stack.yml; then
    print_result "PASS" "RDS backup retention configured"
else
    print_result "WARN" "RDS backup retention not configured"
fi

# Check for WAF configuration
echo ""
echo "🔍 Checking WAF configuration..."
if [ -f "config/aws/security-stack.yml" ] && grep -q "WebACL" config/aws/security-stack.yml; then
    print_result "PASS" "WAF configuration found"
else
    print_result "WARN" "WAF configuration not found"
fi

# Security recommendations
echo ""
echo "🔒 Security Recommendations:"
echo "1. Enable AWS GuardDuty for threat detection"
echo "2. Set up AWS Config for compliance monitoring"
echo "3. Enable CloudTrail for API auditing"
echo "4. Implement VPC Flow Logs"
echo "5. Set up AWS Security Hub for centralized security findings"
echo "6. Enable AWS Inspector for vulnerability assessments"
echo "7. Implement least privilege access for all IAM roles"
echo "8. Regular security audits and penetration testing"

# Summary
echo ""
echo "📊 Security Audit Summary:"
echo -e "${GREEN}✅ Passed: $PASS_COUNT${NC}"
echo -e "${YELLOW}⚠️  Warnings: $WARN_COUNT${NC}"
echo -e "${RED}❌ Failed: $FAIL_COUNT${NC}"

if [ $FAIL_COUNT -gt 0 ]; then
    echo ""
    echo -e "${RED}🚨 CRITICAL: $FAIL_COUNT security issues found. Please fix before deployment.${NC}"
    exit 1
elif [ $WARN_COUNT -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}⚠️  WARNING: $WARN_COUNT security warnings found. Consider addressing before deployment.${NC}"
    exit 0
else
    echo ""
    echo -e "${GREEN}🎉 All security checks passed!${NC}"
    exit 0
fi
