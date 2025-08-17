#!/bin/bash

# Enhanced Monitoring Setup Script for DealsBasket
# This script sets up comprehensive monitoring and alerting

set -e

echo "📊 Setting up enhanced monitoring and alerting for DealsBasket..."

# Load environment variables
if [ -f config/aws/.env.aws ]; then
    source config/aws/.env.aws
else
    echo "❌ Environment file not found. Please create config/aws/.env.aws"
    exit 1
fi

# Get AWS region
AWS_REGION=${AWS_DEFAULT_REGION:-ap-south-1}
echo "📍 Using AWS Region: $AWS_REGION"

# Get notification email
read -p "📧 Enter email address for alerts: " NOTIFICATION_EMAIL
if [ -z "$NOTIFICATION_EMAIL" ]; then
    echo "❌ Email address is required for alerts"
    exit 1
fi

# Deploy monitoring stack
echo "🚀 Deploying monitoring CloudFormation stack..."
aws cloudformation deploy \
    --template-file config/aws/monitoring-stack.yml \
    --stack-name dealsbasket-monitoring \
    --parameter-overrides \
        EnvironmentName=dealsbasket-prod \
        NotificationEmail="$NOTIFICATION_EMAIL" \
        ECSClusterName=dealsbasket-cluster \
        ECSServiceName=dealsbasket-service \
    --capabilities CAPABILITY_IAM \
    --region "$AWS_REGION"

if [ $? -eq 0 ]; then
    echo "✅ Monitoring stack deployed successfully"
else
    echo "❌ Failed to deploy monitoring stack"
    exit 1
fi

# Create custom log insights queries
echo "📝 Creating CloudWatch Insights queries..."

# Error analysis query
aws logs put-query-definition \
    --name "DealsBasket-Errors" \
    --query-string 'fields @timestamp, @message, @logStream
| filter @message like /ERROR/
| sort @timestamp desc
| limit 100' \
    --log-group-names "/ecs/dealsbasket-prod" \
    --region "$AWS_REGION"

# Performance analysis query
aws logs put-query-definition \
    --name "DealsBasket-Performance" \
    --query-string 'fields @timestamp, @message
| filter @message like /response_time/
| stats avg(@message) by bin(5m)' \
    --log-group-names "/ecs/dealsbasket-prod" \
    --region "$AWS_REGION"

# Authentication analysis query
aws logs put-query-definition \
    --name "DealsBasket-Auth" \
    --query-string 'fields @timestamp, @message
| filter @message like /authentication/ or @message like /login/
| sort @timestamp desc
| limit 50' \
    --log-group-names "/ecs/dealsbasket-prod" \
    --region "$AWS_REGION"

# Set up log metric filters
echo "📈 Creating log metric filters..."

# Error rate metric filter
aws logs put-metric-filter \
    --log-group-name "/ecs/dealsbasket-prod" \
    --filter-name "ErrorRate" \
    --filter-pattern "[timestamp, request_id, level=\"ERROR\", ...]" \
    --metric-transformations \
        metricName=ErrorRate,metricNamespace=DealsBasket/Application,metricValue=1,defaultValue=0 \
    --region "$AWS_REGION"

# Response time metric filter
aws logs put-metric-filter \
    --log-group-name "/ecs/dealsbasket-prod" \
    --filter-name "ResponseTime" \
    --filter-pattern "[timestamp, request_id, level, message=\"response_time:\", response_time]" \
    --metric-transformations \
        metricName=ResponseTime,metricNamespace=DealsBasket/Application,metricValue='$response_time',defaultValue=0 \
    --region "$AWS_REGION"

# Authentication failures metric filter
aws logs put-metric-filter \
    --log-group-name "/ecs/dealsbasket-prod" \
    --filter-name "AuthFailures" \
    --filter-pattern "[timestamp, request_id, level, message=\"authentication failed\", ...]" \
    --metric-transformations \
        metricName=AuthFailures,metricNamespace=DealsBasket/Security,metricValue=1,defaultValue=0 \
    --region "$AWS_REGION"

# Create additional alarms for custom metrics
echo "🚨 Creating custom metric alarms..."

# High error rate alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "dealsbasket-high-error-rate" \
    --alarm-description "High application error rate" \
    --metric-name ErrorRate \
    --namespace DealsBasket/Application \
    --statistic Sum \
    --period 300 \
    --evaluation-periods 2 \
    --threshold 10 \
    --comparison-operator GreaterThanThreshold \
    --alarm-actions "arn:aws:sns:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):dealsbasket-prod-alerts" \
    --region "$AWS_REGION"

# High response time alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "dealsbasket-high-response-time" \
    --alarm-description "High application response time" \
    --metric-name ResponseTime \
    --namespace DealsBasket/Application \
    --statistic Average \
    --period 300 \
    --evaluation-periods 2 \
    --threshold 2000 \
    --comparison-operator GreaterThanThreshold \
    --alarm-actions "arn:aws:sns:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):dealsbasket-prod-alerts" \
    --region "$AWS_REGION"

# Authentication failures alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "dealsbasket-auth-failures" \
    --alarm-description "High authentication failure rate" \
    --metric-name AuthFailures \
    --namespace DealsBasket/Security \
    --statistic Sum \
    --period 300 \
    --evaluation-periods 1 \
    --threshold 5 \
    --comparison-operator GreaterThanThreshold \
    --alarm-actions "arn:aws:sns:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):dealsbasket-prod-alerts" \
    --region "$AWS_REGION"

# Get dashboard URL
DASHBOARD_URL="https://console.aws.amazon.com/cloudwatch/home?region=$AWS_REGION#dashboards:name=dealsbasket-prod-monitoring"

echo ""
echo "✅ Enhanced monitoring setup completed successfully!"
echo ""
echo "📊 Monitoring Resources Created:"
echo "  - CloudWatch Dashboard: dealsbasket-prod-monitoring"
echo "  - SNS Alert Topic: dealsbasket-prod-alerts"
echo "  - Log Groups: /ecs/dealsbasket-prod"
echo "  - Custom Metric Filters: ErrorRate, ResponseTime, AuthFailures"
echo "  - CloudWatch Alarms: CPU, Memory, Database, Response Time, Errors"
echo "  - Log Insights Queries: Errors, Performance, Authentication"
echo ""
echo "🔗 Quick Links:"
echo "  Dashboard: $DASHBOARD_URL"
echo "  Logs: https://console.aws.amazon.com/cloudwatch/home?region=$AWS_REGION#logsV2:log-groups"
echo "  Alarms: https://console.aws.amazon.com/cloudwatch/home?region=$AWS_REGION#alarmsV2:"
echo ""
echo "📧 Alert Notifications:"
echo "  Email: $NOTIFICATION_EMAIL"
echo "  (Check your email and confirm the SNS subscription)"
echo ""
echo "💡 Next Steps:"
echo "  1. Confirm SNS email subscription"
echo "  2. Review and customize alarm thresholds"
echo "  3. Set up additional custom metrics in your application"
echo "  4. Configure log retention policies"
echo "  5. Set up automated responses to critical alerts"
