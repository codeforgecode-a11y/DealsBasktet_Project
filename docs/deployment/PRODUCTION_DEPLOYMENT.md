# 🚀 DealsBasket Production Deployment Guide

This guide covers deploying DealsBasket to production environments including Render, AWS, and other cloud platforms.

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL database
- Redis (optional, for caching)
- Cloudinary account (for media storage)
- Domain name (optional)

## 🔧 Environment Configuration

DealsBasket uses a single `.env` file for all environments. For production deployment:

### 1. Copy Environment Template

```bash
cp .env.example .env
```

### 2. Configure Production Variables

Update your `.env` file with production values:

```env
# PROJECT CONFIGURATION
PROJECT_NAME=DealsBasket
ENVIRONMENT=production

# DJANGO CONFIGURATION
SECRET_KEY=your-super-secure-secret-key-here
DEBUG=False
DJANGO_SETTINGS_MODULE=server.settings.production
ALLOWED_HOSTS=yourdomain.com,.onrender.com,.render.com

# DATABASE CONFIGURATION
# Option 1: Individual database settings
DB_ENGINE=django.db.backends.postgresql
DB_NAME=dealsbasket_prod
DB_USER=your_db_user
DB_PASSWORD=your_secure_db_password
DB_HOST=your-db-host.com
DB_PORT=5432

# Option 2: Database URL (preferred for cloud platforms)
# DATABASE_URL=postgresql://user:password@host:port/database

# SECURITY CONFIGURATION
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# CLOUDINARY CONFIGURATION
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
USE_CLOUDINARY_FOR_MEDIA=True

# CORS CONFIGURATION
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
CORS_ALLOW_CREDENTIALS=True

# EMAIL CONFIGURATION
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email-username
EMAIL_HOST_PASSWORD=your-email-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# CACHE CONFIGURATION
REDIS_URL=redis://your-redis-host:6379/0

# JWT CONFIGURATION
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7
JWT_ALLOW_REFRESH=True

# SUPERUSER CONFIGURATION
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@yourdomain.com
DJANGO_SUPERUSER_PASSWORD=your-secure-admin-password

# FRONTEND CONFIGURATION
FRONTEND_URL=https://yourdomain.com

# MONITORING (Optional)
SENTRY_DSN=https://your-sentry-dsn.ingest.sentry.io/
```

## 🌐 Render Deployment

### Quick Deploy

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/your-username/DealsBasket_Project)

### Manual Deployment

1. **Create Render Account**: Sign up at [render.com](https://render.com)

2. **Create Web Service**:
   - Connect your GitHub repository
   - Choose "Web Service"
   - Set build command: `./build.sh`
   - Set start command: `gunicorn --config gunicorn.conf.py server.wsgi:application`

3. **Configure Environment Variables**:
   Set all production variables from your `.env` file in Render dashboard

4. **Add PostgreSQL Database**:
   - Create PostgreSQL service in Render
   - Copy `DATABASE_URL` to your environment variables

5. **Deploy**: Render will automatically build and deploy your application

## 🐳 Docker Deployment

### Build Docker Image

```bash
docker build -t dealsbasket:latest .
```

### Run with Docker Compose

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## ☁️ AWS Deployment

### Using AWS Elastic Beanstalk

1. **Install EB CLI**:
```bash
pip install awsebcli
```

2. **Initialize EB Application**:
```bash
eb init dealsbasket
```

3. **Create Environment**:
```bash
eb create production
```

4. **Set Environment Variables**:
```bash
eb setenv SECRET_KEY=your-secret-key DEBUG=False
```

5. **Deploy**:
```bash
eb deploy
```

## 🔒 Security Checklist

- [ ] Generate new `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] Set `DEBUG=False`
- [ ] Configure proper `ALLOWED_HOSTS`
- [ ] Enable HTTPS security settings
- [ ] Use strong database passwords
- [ ] Configure CORS properly
- [ ] Set up monitoring (Sentry)
- [ ] Regular security updates
- [ ] Database backups
- [ ] SSL certificate

## 📊 Monitoring & Maintenance

### Health Check
Your application includes a health check endpoint:
```
GET /health/
```

### Logs
Monitor application logs for errors and performance issues.

### Database Backups
Set up regular database backups:
```bash
./scripts/backup_database.sh
```

### Updates
Keep dependencies updated:
```bash
pip install -r requirements.txt --upgrade
```

## 🚨 Troubleshooting

### Common Issues

1. **Static Files Not Loading**:
   - Run `python manage.py collectstatic`
   - Check `STATIC_URL` and `STATIC_ROOT` settings

2. **Database Connection Issues**:
   - Verify `DATABASE_URL` or individual DB settings
   - Check network connectivity
   - Verify database credentials

3. **CORS Errors**:
   - Update `CORS_ALLOWED_ORIGINS`
   - Check frontend URL configuration

4. **Email Not Working**:
   - Verify SMTP settings
   - Check email provider configuration

### Support

For deployment issues:
1. Check application logs
2. Verify environment variables
3. Test database connectivity
4. Review security settings

## 📚 Additional Resources

- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Render Documentation](https://render.com/docs)
- [AWS Elastic Beanstalk Guide](https://docs.aws.amazon.com/elasticbeanstalk/)
- [Docker Documentation](https://docs.docker.com/)
