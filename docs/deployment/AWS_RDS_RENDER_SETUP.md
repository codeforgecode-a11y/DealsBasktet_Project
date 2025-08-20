# 🔗 AWS RDS PostgreSQL with Render Deployment Guide

This guide explains how to deploy DealsBasket on Render while using an external AWS RDS PostgreSQL database.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Render.com    │    │   AWS RDS        │    │   Cloudinary    │
│   Web Service   │───▶│   PostgreSQL     │    │   Media Storage │
│   (Django App)  │    │   Database       │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

### AWS RDS Setup
- ✅ AWS RDS PostgreSQL instance running
- ✅ Database security group configured
- ✅ Database credentials available
- ✅ Network connectivity verified

### Render Account
- ✅ Render.com account created
- ✅ GitHub repository connected
- ✅ Environment variables access

## 🔧 Configuration Steps

### 1. AWS RDS Security Group Configuration

**Allow Render IP Ranges:**
```bash
# Add these IP ranges to your RDS security group
# Render's IP ranges (check Render docs for latest)
0.0.0.0/0  # For simplicity, but restrict in production
```

**Recommended Security Group Rules:**
```
Type: PostgreSQL
Protocol: TCP
Port: 5432
Source: Custom (Render IP ranges or 0.0.0.0/0 for testing)
```

### 2. Database Connection Testing

**Test from local machine:**
```bash
# Test connection to AWS RDS
psql -h dealsbasket.chi4u4q4kiid.ap-south-1.rds.amazonaws.com \
     -U durgesh \
     -d dealsbasket \
     -p 5432

# Or using Django
python manage.py dbshell
```

### 3. Render Environment Variables

**Required Database Variables:**
```env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=dealsbasket
DB_USER=durgesh
DB_PASSWORD=DUrg7080
DB_HOST=dealsbasket.chi4u4q4kiid.ap-south-1.rds.amazonaws.com
DB_PORT=5432
```

**Alternative DATABASE_URL Format:**
```env
DATABASE_URL=postgresql://durgesh:DUrg7080@dealsbasket.chi4u4q4kiid.ap-south-1.rds.amazonaws.com:5432/dealsbasket
```

### 4. Render Deployment Configuration

The `render.yaml` file is already configured for AWS RDS. Key points:

- ✅ Render's managed PostgreSQL service is disabled
- ✅ AWS RDS connection variables are set
- ✅ Django settings will use external database
- ✅ Migrations will run against AWS RDS

## 🚀 Deployment Process

### 1. Deploy to Render

```bash
# Push to GitHub (triggers auto-deploy)
git push origin main

# Or deploy manually via Render dashboard
```

### 2. Monitor Deployment

**Check deployment logs for:**
- ✅ Database connection successful
- ✅ Migrations completed
- ✅ Static files collected
- ✅ Application started

### 3. Verify Database Connection

**Test endpoints:**
```bash
# Health check
curl https://your-app.onrender.com/health/

# Admin panel
curl https://your-app.onrender.com/admin/

# API root
curl https://your-app.onrender.com/api/
```

## 🔒 Security Best Practices

### Database Security
- [ ] Use strong passwords
- [ ] Enable SSL/TLS encryption
- [ ] Restrict security group access
- [ ] Enable database logging
- [ ] Regular security updates
- [ ] Monitor access patterns

### Network Security
- [ ] Use VPC for RDS (recommended)
- [ ] Implement database firewall rules
- [ ] Monitor network traffic
- [ ] Use IAM database authentication (optional)

### Application Security
- [ ] Secure environment variables in Render
- [ ] Enable HTTPS only
- [ ] Configure proper CORS
- [ ] Use secure session settings

## 📊 Monitoring & Maintenance

### Database Monitoring
```bash
# Check database performance
# Use AWS CloudWatch metrics
# Monitor connection counts
# Track query performance
```

### Application Monitoring
```bash
# Check application logs
render logs --service dealsbasket-web

# Monitor health endpoint
curl https://your-app.onrender.com/health/
```

### Backup Strategy
- ✅ AWS RDS automated backups enabled
- ✅ Point-in-time recovery configured
- ✅ Cross-region backup replication (optional)
- ✅ Regular backup testing

## 🚨 Troubleshooting

### Common Issues

**1. Connection Timeout**
```bash
# Check security group rules
# Verify RDS endpoint
# Test network connectivity
```

**2. Authentication Failed**
```bash
# Verify username/password
# Check database user permissions
# Ensure database exists
```

**3. SSL Connection Issues**
```bash
# Add to Django settings:
DATABASES['default']['OPTIONS'] = {
    'sslmode': 'require',
}
```

### Debug Commands

**Test database connection:**
```python
# In Django shell
from django.db import connection
cursor = connection.cursor()
cursor.execute("SELECT version();")
print(cursor.fetchone())
```

**Check environment variables:**
```bash
# In Render shell
echo $DB_HOST
echo $DB_NAME
echo $DATABASE_URL
```

## 💰 Cost Optimization

### AWS RDS Costs
- Use appropriate instance size
- Enable storage autoscaling
- Consider Reserved Instances
- Monitor unused connections
- Optimize query performance

### Render Costs
- Choose appropriate service plan
- Monitor resource usage
- Optimize application performance
- Use caching effectively

## 📚 Additional Resources

- [AWS RDS Documentation](https://docs.aws.amazon.com/rds/)
- [Render Documentation](https://render.com/docs)
- [Django Database Configuration](https://docs.djangoproject.com/en/stable/ref/settings/#databases)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/security.html)

## 🔄 Migration from Render PostgreSQL

If migrating from Render's managed PostgreSQL:

1. **Export data from Render PostgreSQL**
2. **Import data to AWS RDS**
3. **Update environment variables**
4. **Test application thoroughly**
5. **Monitor performance**

---

**Configuration Status**: ✅ Ready for AWS RDS deployment
**Last Updated**: August 20, 2025
**Tested With**: Django 5.0+, PostgreSQL 15+
