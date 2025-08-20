# 🚀 DealsBasket Deployment Guide for Render

This guide provides step-by-step instructions for deploying the DealsBasket Django application to Render.com.

## 📋 Prerequisites

1. **Render Account**: Sign up at [render.com](https://render.com)
2. **GitHub Repository**: Your code should be in a GitHub repository
3. **Domain (Optional)**: For custom domain setup

## 🛠️ Deployment Methods

### Method 1: Using render.yaml (Recommended)

1. **Fork/Clone the Repository**
   ```bash
   git clone https://github.com/your-username/DealsBasket_Project.git
   cd DealsBasket_Project
   ```

2. **Connect to Render**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New" → "Blueprint"
   - Connect your GitHub repository
   - Render will automatically detect the `render.yaml` file

3. **Configure Environment Variables**
   The `render.yaml` file includes most configurations, but you may need to set:
   - `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` (if using Cloudinary)
   - `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` (if using email features)
   - `CORS_ALLOWED_ORIGINS` (your frontend domain)

### Method 2: Manual Setup

#### Step 1: Create PostgreSQL Database

1. In Render Dashboard, click "New" → "PostgreSQL"
2. Configure:
   - **Name**: `dealsbasket-db`
   - **Database**: `dealsbasket`
   - **User**: `dealsbasket_user`
   - **Plan**: Starter (free) or higher
3. Note the connection details (automatically provided as `DATABASE_URL`)

#### Step 2: Create Web Service

1. Click "New" → "Web Service"
2. Connect your GitHub repository
3. Configure:
   - **Name**: `dealsbasket-web`
   - **Environment**: `Python 3`
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn --config gunicorn.conf.py server.wsgi:application`
   - **Plan**: Starter (free) or higher

#### Step 3: Environment Variables

**Note**: DealsBasket uses a single `.env` file for all environments. Use `.env.example` as your template and set the following variables in the Render dashboard:

```bash
# Required
DJANGO_SETTINGS_MODULE=server.settings.production
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=.onrender.com,localhost,127.0.0.1
ENVIRONMENT=production

# Database (automatically set by Render)
DATABASE_URL=postgresql://user:password@host:port/database

# Admin User
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@dealsbasket.com
DJANGO_SUPERUSER_PASSWORD=your-secure-password

# Optional: Cloudinary (for image storage)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Optional: Email Configuration
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password
DEFAULT_FROM_EMAIL=noreply@dealsbasket.com

# CORS (update with your frontend domain)
CORS_ALLOWED_ORIGINS=https://your-frontend.com

# JWT
JWT_SECRET_KEY=your-jwt-secret
```

## 🔧 Configuration Files

The deployment includes these key files:

- **`build.sh`**: Build script that installs dependencies and runs migrations
- **`gunicorn.conf.py`**: Gunicorn configuration optimized for Render
- **`render.yaml`**: Infrastructure as code configuration
- **`.env.example`**: Environment variables template (use this to create your .env file)

## 🚀 Deployment Process

1. **Push to GitHub**: Ensure your code is pushed to GitHub
2. **Deploy**: Render will automatically build and deploy
3. **Monitor**: Check the deployment logs in Render dashboard
4. **Test**: Visit your app URL to verify deployment

## 🔍 Health Checks

The application includes health check endpoints:

- **Simple**: `/health/simple/` - Basic health check
- **Detailed**: `/health/` - Comprehensive health check with database status

## 📊 Monitoring

### Logs
- View real-time logs in Render dashboard
- Logs include application, build, and system information

### Metrics
- Render provides basic metrics (CPU, memory, requests)
- Consider integrating Sentry for error tracking

## 🔒 Security Considerations

1. **Environment Variables**: Never commit secrets to Git
2. **HTTPS**: Render provides free SSL certificates
3. **Database**: Use strong passwords and connection limits
4. **CORS**: Configure allowed origins properly
5. **Rate Limiting**: Enabled by default in the application

## 🎯 Performance Optimization

1. **Gunicorn Workers**: Configured based on CPU cores
2. **Static Files**: Served efficiently with WhiteNoise
3. **Database**: Connection pooling enabled
4. **Caching**: Redis can be added for session/cache storage

## 🐛 Troubleshooting

### Common Issues

1. **Build Failures**
   - Check `build.sh` permissions: `chmod +x build.sh`
   - Verify all dependencies in `requirements.txt`

2. **Database Connection Issues**
   - Ensure `DATABASE_URL` is set correctly
   - Check database service status in Render

3. **Static Files Not Loading**
   - Verify `STATIC_URL` and `STATIC_ROOT` settings
   - Check WhiteNoise configuration

4. **Health Check Failures**
   - Verify `ALLOWED_HOSTS` includes your Render domain
   - Check application logs for errors

### Debug Commands

```bash
# Check Django configuration
python manage.py check --deploy

# Test database connection
python manage.py dbshell

# Collect static files manually
python manage.py collectstatic --noinput

# Create superuser manually
python manage.py createsuperuser
```

## 📈 Scaling

### Vertical Scaling
- Upgrade to higher Render plans for more CPU/memory
- Monitor resource usage in dashboard

### Horizontal Scaling
- Add Redis for session storage
- Consider CDN for static files
- Database read replicas for high traffic

## 🔄 Updates and Maintenance

1. **Code Updates**: Push to GitHub triggers automatic deployment
2. **Dependencies**: Update `requirements.txt` and redeploy
3. **Database Migrations**: Included in build process
4. **Backups**: Render provides automatic database backups

## 📞 Support

- **Render Documentation**: [docs.render.com](https://docs.render.com)
- **Community**: [community.render.com](https://community.render.com)
- **Status**: [status.render.com](https://status.render.com)

## 🎉 Post-Deployment

After successful deployment:

1. **Test all endpoints**: API, admin panel, health checks
2. **Create test data**: Products, categories, users
3. **Configure monitoring**: Set up alerts and notifications
4. **Update DNS**: Point your domain to Render (if using custom domain)
5. **SSL Certificate**: Verify HTTPS is working correctly

Your DealsBasket application should now be live and accessible via your Render URL!
