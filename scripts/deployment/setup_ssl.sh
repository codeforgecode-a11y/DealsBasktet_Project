#!/bin/bash

# SSL/HTTPS Setup Script for DealsBasket
# This script sets up SSL certificates and HTTPS configuration

set -e

echo "🔒 Setting up SSL/HTTPS configuration for DealsBasket..."

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

# Get domain information
read -p "🌐 Enter your domain name (e.g., dealsbasket.com): " DOMAIN_NAME
if [ -z "$DOMAIN_NAME" ]; then
    echo "❌ Domain name is required"
    exit 1
fi

read -p "🌐 Enter your subdomain (e.g., api.dealsbasket.com): " SUBDOMAIN_NAME
if [ -z "$SUBDOMAIN_NAME" ]; then
    SUBDOMAIN_NAME="api.$DOMAIN_NAME"
fi

# Check if Route53 hosted zone exists
echo "🔍 Checking Route53 hosted zone..."
HOSTED_ZONE_ID=$(aws route53 list-hosted-zones-by-name --dns-name "$DOMAIN_NAME" --query "HostedZones[0].Id" --output text 2>/dev/null || echo "None")

if [ "$HOSTED_ZONE_ID" = "None" ] || [ -z "$HOSTED_ZONE_ID" ]; then
    echo "⚠️  Route53 hosted zone not found for $DOMAIN_NAME"
    read -p "Do you want to create a hosted zone? (y/n): " CREATE_ZONE
    
    if [ "$CREATE_ZONE" = "y" ] || [ "$CREATE_ZONE" = "Y" ]; then
        echo "📝 Creating Route53 hosted zone..."
        HOSTED_ZONE_ID=$(aws route53 create-hosted-zone \
            --name "$DOMAIN_NAME" \
            --caller-reference "$(date +%s)" \
            --query "HostedZone.Id" \
            --output text)
        
        # Remove the /hostedzone/ prefix
        HOSTED_ZONE_ID=${HOSTED_ZONE_ID#/hostedzone/}
        
        echo "✅ Created hosted zone: $HOSTED_ZONE_ID"
        echo "⚠️  Please update your domain's nameservers with your registrar:"
        aws route53 get-hosted-zone --id "$HOSTED_ZONE_ID" --query "DelegationSet.NameServers" --output table
    else
        echo "❌ Hosted zone is required for SSL certificate validation"
        exit 1
    fi
else
    # Remove the /hostedzone/ prefix if present
    HOSTED_ZONE_ID=${HOSTED_ZONE_ID#/hostedzone/}
    echo "✅ Found hosted zone: $HOSTED_ZONE_ID"
fi

# Get VPC and subnet information
echo "🔍 Getting VPC and subnet information..."
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=tag:Name,Values=DealsBasket-VPC" --query "Vpcs[0].VpcId" --output text 2>/dev/null || echo "None")

if [ "$VPC_ID" = "None" ] || [ -z "$VPC_ID" ]; then
    echo "❌ VPC not found. Please deploy the network stack first."
    exit 1
fi

PUBLIC_SUBNET_IDS=$(aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=*Public*" \
    --query "Subnets[].SubnetId" \
    --output text | tr '\t' ',')

if [ -z "$PUBLIC_SUBNET_IDS" ]; then
    echo "❌ Public subnets not found. Please deploy the network stack first."
    exit 1
fi

# Get ALB security group
ALB_SG_ID=$(aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=dealsbasket-prod-alb-sg" \
    --query "SecurityGroups[0].GroupId" \
    --output text 2>/dev/null || echo "None")

if [ "$ALB_SG_ID" = "None" ] || [ -z "$ALB_SG_ID" ]; then
    echo "❌ ALB security group not found. Please deploy the security stack first."
    exit 1
fi

# Deploy SSL stack
echo "🚀 Deploying SSL CloudFormation stack..."
aws cloudformation deploy \
    --template-file config/aws/ssl-stack.yml \
    --stack-name dealsbasket-ssl \
    --parameter-overrides \
        EnvironmentName=dealsbasket-prod \
        DomainName="$DOMAIN_NAME" \
        SubdomainName="$SUBDOMAIN_NAME" \
        HostedZoneId="$HOSTED_ZONE_ID" \
        VpcId="$VPC_ID" \
        PublicSubnetIds="$PUBLIC_SUBNET_IDS" \
        ALBSecurityGroupId="$ALB_SG_ID" \
    --capabilities CAPABILITY_IAM \
    --region "$AWS_REGION"

if [ $? -eq 0 ]; then
    echo "✅ SSL stack deployed successfully"
else
    echo "❌ Failed to deploy SSL stack"
    exit 1
fi

# Wait for certificate validation
echo "⏳ Waiting for SSL certificate validation..."
CERTIFICATE_ARN=$(aws cloudformation describe-stacks \
    --stack-name dealsbasket-ssl \
    --query "Stacks[0].Outputs[?OutputKey=='SSLCertificateArn'].OutputValue" \
    --output text \
    --region "$AWS_REGION")

echo "📋 Certificate ARN: $CERTIFICATE_ARN"
echo "⏳ This may take several minutes..."

# Check certificate status
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    CERT_STATUS=$(aws acm describe-certificate \
        --certificate-arn "$CERTIFICATE_ARN" \
        --query "Certificate.Status" \
        --output text \
        --region "$AWS_REGION")
    
    if [ "$CERT_STATUS" = "ISSUED" ]; then
        echo "✅ SSL certificate validated and issued"
        break
    elif [ "$CERT_STATUS" = "FAILED" ]; then
        echo "❌ SSL certificate validation failed"
        exit 1
    else
        echo "⏳ Certificate status: $CERT_STATUS (attempt $attempt/$max_attempts)"
        sleep 30
        attempt=$((attempt + 1))
    fi
done

if [ $attempt -gt $max_attempts ]; then
    echo "⚠️  Certificate validation is taking longer than expected"
    echo "   Please check the AWS Console for validation status"
fi

# Get stack outputs
echo "📋 Getting deployment information..."
ALB_DNS=$(aws cloudformation describe-stacks \
    --stack-name dealsbasket-ssl \
    --query "Stacks[0].Outputs[?OutputKey=='LoadBalancerDNS'].OutputValue" \
    --output text \
    --region "$AWS_REGION")

CLOUDFRONT_DOMAIN=$(aws cloudformation describe-stacks \
    --stack-name dealsbasket-ssl \
    --query "Stacks[0].Outputs[?OutputKey=='CloudFrontDomainName'].OutputValue" \
    --output text \
    --region "$AWS_REGION")

APPLICATION_URL=$(aws cloudformation describe-stacks \
    --stack-name dealsbasket-ssl \
    --query "Stacks[0].Outputs[?OutputKey=='ApplicationURL'].OutputValue" \
    --output text \
    --region "$AWS_REGION")

# Update nginx configuration for SSL
echo "🔧 Updating nginx configuration for SSL..."
cat > nginx-ssl.conf << EOF
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '\$remote_addr - \$remote_user [\$time_local] "\$request" '
                    '\$status \$body_bytes_sent "\$http_referer" '
                    '"\$http_user_agent" "\$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;

    upstream django {
        server web:8000;
    }

    server {
        listen 80;
        server_name _;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        # Handle ALB health checks
        location /health/ {
            proxy_pass http://django;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_redirect off;
        }

        # Static files
        location /static/ {
            alias /app/staticfiles/;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }

        # Media files
        location /media/ {
            alias /app/media/;
            expires 7d;
            add_header Cache-Control "public";
        }

        # API endpoints
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://django;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_redirect off;
        }

        # Admin interface
        location /admin/ {
            proxy_pass http://django;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_redirect off;
        }

        # Default location
        location / {
            proxy_pass http://django;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_redirect off;
        }
    }
}
EOF

echo "✅ SSL/HTTPS setup completed successfully!"
echo ""
echo "🔒 SSL Configuration Summary:"
echo "  - Domain: $DOMAIN_NAME"
echo "  - Subdomain: $SUBDOMAIN_NAME"
echo "  - Certificate ARN: $CERTIFICATE_ARN"
echo "  - ALB DNS: $ALB_DNS"
echo "  - CloudFront Domain: $CLOUDFRONT_DOMAIN"
echo ""
echo "🌐 Application URLs:"
echo "  - Primary: $APPLICATION_URL"
echo "  - WWW: https://www.$DOMAIN_NAME"
echo "  - API: https://$SUBDOMAIN_NAME"
echo ""
echo "📝 Next Steps:"
echo "  1. Update your ECS service to use the new target group"
echo "  2. Test SSL certificate: https://www.ssllabs.com/ssltest/"
echo "  3. Update application settings with the new domain"
echo "  4. Configure CORS settings for the new domain"
echo "  5. Update any hardcoded URLs in your application"
echo ""
echo "⚠️  Important Notes:"
echo "  - DNS propagation may take up to 48 hours"
echo "  - Certificate validation requires DNS records to be properly configured"
echo "  - CloudFront distribution may take 15-20 minutes to deploy"
