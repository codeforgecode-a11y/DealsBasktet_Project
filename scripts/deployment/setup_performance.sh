#!/bin/bash

# Performance Optimization Setup Script for DealsBasket
# This script sets up caching, auto-scaling, and performance monitoring

set -e

echo "🚀 Setting up performance optimizations for DealsBasket..."

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

# Get VPC and subnet information
echo "🔍 Getting VPC and subnet information..."
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=tag:Name,Values=DealsBasket-VPC" --query "Vpcs[0].VpcId" --output text 2>/dev/null || echo "None")

if [ "$VPC_ID" = "None" ] || [ -z "$VPC_ID" ]; then
    echo "❌ VPC not found. Please deploy the network stack first."
    exit 1
fi

PRIVATE_SUBNET_IDS=$(aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=*Private*" \
    --query "Subnets[].SubnetId" \
    --output text | tr '\t' ',')

if [ -z "$PRIVATE_SUBNET_IDS" ]; then
    echo "❌ Private subnets not found. Please deploy the network stack first."
    exit 1
fi

# Deploy performance stack
echo "🚀 Deploying performance optimization CloudFormation stack..."
aws cloudformation deploy \
    --template-file config/aws/performance-stack.yml \
    --stack-name dealsbasket-performance \
    --parameter-overrides \
        EnvironmentName=dealsbasket-prod \
        VpcId="$VPC_ID" \
        PrivateSubnetIds="$PRIVATE_SUBNET_IDS" \
        ECSClusterName=dealsbasket-cluster \
        ECSServiceName=dealsbasket-service \
    --capabilities CAPABILITY_IAM \
    --region "$AWS_REGION"

if [ $? -eq 0 ]; then
    echo "✅ Performance stack deployed successfully"
else
    echo "❌ Failed to deploy performance stack"
    exit 1
fi

# Get Redis endpoint
echo "📋 Getting Redis endpoint..."
REDIS_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name dealsbasket-performance \
    --query "Stacks[0].Outputs[?OutputKey=='RedisEndpoint'].OutputValue" \
    --output text \
    --region "$AWS_REGION")

REDIS_PORT=$(aws cloudformation describe-stacks \
    --stack-name dealsbasket-performance \
    --query "Stacks[0].Outputs[?OutputKey=='RedisPort'].OutputValue" \
    --output text \
    --region "$AWS_REGION")

echo "📍 Redis Endpoint: $REDIS_ENDPOINT:$REDIS_PORT"

# Update Django settings for Redis caching
echo "🔧 Creating Redis cache configuration..."
cat > config/cache_settings.py << EOF
# Redis Cache Configuration for Production
import os

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{os.environ.get("REDIS_ENDPOINT", "$REDIS_ENDPOINT")}:{os.environ.get("REDIS_PORT", "$REDIS_PORT")}/0',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 20,
                'retry_on_timeout': True,
                'socket_connect_timeout': 5,
                'socket_timeout': 5,
            },
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
        },
        'KEY_PREFIX': 'dealsbasket',
        'TIMEOUT': 300,  # 5 minutes default timeout
    },
    'sessions': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{os.environ.get("REDIS_ENDPOINT", "$REDIS_ENDPOINT")}:{os.environ.get("REDIS_PORT", "$REDIS_PORT")}/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'dealsbasket_sessions',
        'TIMEOUT': 86400,  # 24 hours for sessions
    }
}

# Use Redis for sessions
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'sessions'

# Cache middleware settings
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 300
CACHE_MIDDLEWARE_KEY_PREFIX = 'dealsbasket_cache'
EOF

# Create performance monitoring middleware
echo "📊 Creating performance monitoring middleware..."
mkdir -p server/middleware
cat > server/middleware/performance.py << EOF
import time
import logging
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)

class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """
    Middleware to monitor application performance metrics
    """
    
    def process_request(self, request):
        request.start_time = time.time()
        return None
    
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            response_time = (time.time() - request.start_time) * 1000  # Convert to milliseconds
            
            # Log slow requests
            if response_time > 1000:  # Log requests slower than 1 second
                logger.warning(f"Slow request: {request.path} took {response_time:.2f}ms")
            
            # Store performance metrics in cache for monitoring
            cache_key = f"performance_metrics_{int(time.time() // 60)}"  # Per minute bucket
            metrics = cache.get(cache_key, {
                'total_requests': 0,
                'total_response_time': 0,
                'slow_requests': 0,
                'error_requests': 0
            })
            
            metrics['total_requests'] += 1
            metrics['total_response_time'] += response_time
            
            if response_time > 1000:
                metrics['slow_requests'] += 1
            
            if response.status_code >= 400:
                metrics['error_requests'] += 1
            
            cache.set(cache_key, metrics, 120)  # Store for 2 minutes
            
            # Add performance headers
            response['X-Response-Time'] = f"{response_time:.2f}ms"
            
        return response

class CacheControlMiddleware(MiddlewareMixin):
    """
    Middleware to add appropriate cache control headers
    """
    
    def process_response(self, request, response):
        # Add cache control headers for static content
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            response['Cache-Control'] = 'public, max-age=31536000'  # 1 year
        elif request.path.startswith('/api/'):
            # API responses - short cache for GET requests
            if request.method == 'GET' and response.status_code == 200:
                response['Cache-Control'] = 'public, max-age=300'  # 5 minutes
            else:
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        else:
            response['Cache-Control'] = 'public, max-age=3600'  # 1 hour for other content
        
        return response
EOF

# Create database optimization script
echo "🗄️ Creating database optimization script..."
cat > scripts/deployment/optimize_database.py << EOF
#!/usr/bin/env python3
"""
Database optimization script for DealsBasket
"""
import os
import sys
import django
from django.conf import settings
from django.db import connection

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings.production')
django.setup()

def optimize_database():
    """Run database optimization queries"""
    with connection.cursor() as cursor:
        print("🔧 Running database optimizations...")
        
        # Update table statistics
        cursor.execute("ANALYZE;")
        print("✅ Updated table statistics")
        
        # Vacuum analyze for better performance
        cursor.execute("VACUUM ANALYZE;")
        print("✅ Vacuumed and analyzed tables")
        
        # Create additional performance indexes
        optimizations = [
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_last_login ON users_user(last_login);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_price ON products_product(price);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_user_created ON orders_order(user_id, created_at);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_status_created ON orders_order(status, created_at);",
        ]
        
        for optimization in optimizations:
            try:
                cursor.execute(optimization)
                print(f"✅ {optimization}")
            except Exception as e:
                print(f"⚠️  {optimization} - {e}")

if __name__ == "__main__":
    optimize_database()
    print("🎉 Database optimization completed!")
EOF

chmod +x scripts/deployment/optimize_database.py

# Update requirements.txt with performance packages
echo "📦 Adding performance optimization packages..."
if ! grep -q "django-redis" requirements.txt; then
    echo "django-redis==5.4.0" >> requirements.txt
fi

if ! grep -q "redis" requirements.txt; then
    echo "redis==5.0.1" >> requirements.txt
fi

if ! grep -q "django-cachalot" requirements.txt; then
    echo "django-cachalot==2.6.1" >> requirements.txt
fi

echo ""
echo "✅ Performance optimization setup completed successfully!"
echo ""
echo "🚀 Performance Optimizations Implemented:"
echo "  - Redis cluster for caching and sessions"
echo "  - ECS auto-scaling based on CPU and memory"
echo "  - Performance monitoring middleware"
echo "  - Cache control headers"
echo "  - Database optimization scripts"
echo "  - CloudWatch performance metrics"
echo ""
echo "📊 Performance Monitoring:"
echo "  - Redis Endpoint: $REDIS_ENDPOINT:$REDIS_PORT"
echo "  - Auto-scaling: 2-10 instances based on load"
echo "  - Performance metrics in CloudWatch"
echo "  - Response time monitoring"
echo ""
echo "🔧 Next Steps:"
echo "  1. Update your Django settings to include cache configuration"
echo "  2. Add performance middleware to MIDDLEWARE setting"
echo "  3. Run database optimization script"
echo "  4. Test caching functionality"
echo "  5. Monitor performance metrics in CloudWatch"
echo ""
echo "💡 Configuration Files Created:"
echo "  - config/cache_settings.py"
echo "  - server/middleware/performance.py"
echo "  - scripts/deployment/optimize_database.py"
echo ""
echo "📝 To apply cache settings, add this to your production settings:"
echo "  from .cache_settings import *"
