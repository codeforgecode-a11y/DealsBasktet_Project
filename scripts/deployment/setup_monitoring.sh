#!/bin/bash

# Exit on error
set -e

# Load environment variables
source .env.production

echo "📊 Setting up monitoring..."
echo "=========================="

# Create CloudWatch dashboard
echo "📌 Creating CloudWatch dashboard..."
aws cloudwatch put-dashboard --dashboard-name DealsBasket --dashboard-body '{
    "widgets": [
        {
            "type": "metric",
            "properties": {
                "metrics": [
                    ["AWS/ECS", "CPUUtilization", "ServiceName", "dealsbasket-service", "ClusterName", "dealsbasket-cluster"]
                ],
                "period": 300,
                "stat": "Average",
                "region": "'$AWS_DEFAULT_REGION'",
                "title": "ECS CPU Utilization"
            }
        },
        {
            "type": "metric",
            "properties": {
                "metrics": [
                    ["AWS/ECS", "MemoryUtilization", "ServiceName", "dealsbasket-service", "ClusterName", "dealsbasket-cluster"]
                ],
                "period": 300,
                "stat": "Average",
                "region": "'$AWS_DEFAULT_REGION'",
                "title": "ECS Memory Utilization"
            }
        },
        {
            "type": "metric",
            "properties": {
                "metrics": [
                    ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", "dealsbasket-db"]
                ],
                "period": 300,
                "stat": "Average",
                "region": "'$AWS_DEFAULT_REGION'",
                "title": "RDS CPU Utilization"
            }
        }
    ]
}'

# Create CloudWatch alarms
echo "📌 Creating CloudWatch alarms..."

# CPU Alarm
aws cloudwatch put-metric-alarm \
    --alarm-name dealsbasket-high-cpu \
    --alarm-description "CPU usage exceeds 80%" \
    --metric-name CPUUtilization \
    --namespace AWS/ECS \
    --dimensions Name=ClusterName,Value=dealsbasket-cluster Name=ServiceName,Value=dealsbasket-service \
    --period 300 \
    --evaluation-periods 2 \
    --threshold 80 \
    --comparison-operator GreaterThanThreshold \
    --statistic Average

# Memory Alarm
aws cloudwatch put-metric-alarm \
    --alarm-name dealsbasket-high-memory \
    --alarm-description "Memory usage exceeds 80%" \
    --metric-name MemoryUtilization \
    --namespace AWS/ECS \
    --dimensions Name=ClusterName,Value=dealsbasket-cluster Name=ServiceName,Value=dealsbasket-service \
    --period 300 \
    --evaluation-periods 2 \
    --threshold 80 \
    --comparison-operator GreaterThanThreshold \
    --statistic Average

# Set up auto-scaling
echo "📌 Setting up auto-scaling..."
aws application-autoscaling register-scalable-target \
    --service-namespace ecs \
    --scalable-dimension ecs:service:DesiredCount \
    --resource-id service/dealsbasket-cluster/dealsbasket-service \
    --min-capacity 1 \
    --max-capacity 4

aws application-autoscaling put-scaling-policy \
    --service-namespace ecs \
    --scalable-dimension ecs:service:DesiredCount \
    --resource-id service/dealsbasket-cluster/dealsbasket-service \
    --policy-name cpu-tracking-scaling-policy \
    --policy-type TargetTrackingScaling \
    --target-tracking-scaling-policy-configuration '{
        "TargetValue": 75.0,
        "PredefinedMetricSpecification": {
            "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
        },
        "ScaleOutCooldown": 300,
        "ScaleInCooldown": 300
    }'

echo "=========================="
echo "✅ Monitoring setup completed!"
echo "
Access your monitoring:
----------------------
• CloudWatch Dashboard: https://$AWS_DEFAULT_REGION.console.aws.amazon.com/cloudwatch/home?region=$AWS_DEFAULT_REGION#dashboards:name=DealsBasket
• Alarms: https://$AWS_DEFAULT_REGION.console.aws.amazon.com/cloudwatch/home?region=$AWS_DEFAULT_REGION#alarmsV2:
• Logs: https://$AWS_DEFAULT_REGION.console.aws.amazon.com/cloudwatch/home?region=$AWS_DEFAULT_REGION#logsV2:log-groups
"