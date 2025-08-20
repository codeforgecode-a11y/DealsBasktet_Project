# DealsBasket - Local E-commerce Platform API

A comprehensive Django REST Framework backend for a local e-commerce platform with role-based access control, JWT authentication, and real-time order management.

## Features

### 🔐 Authentication & Authorization
- JWT token authentication with access and refresh tokens
- Role-based access control (User, Shopkeeper, Delivery, Admin)
- Custom permission classes for each role
- Token blacklisting for secure logout

### 🏪 Shop Management
- Shop registration and approval workflow
- Shop profile management
- Location-based shop discovery
- Shop status management (pending, approved, suspended)

### 📦 Product Catalog
- Product CRUD operations with role-based permissions
- Cloudinary integration for image storage
- Category management
- Advanced product search and filtering
- Stock management

### 🛒 Order Management
- Complete order lifecycle management
- Order status tracking (pending → delivered)
- Role-specific order views
- Order cancellation with stock restoration

### 🚚 Delivery System
- Delivery person profiles and management
- Order assignment to delivery persons
- Real-time location tracking
- OTP-based delivery verification
- Delivery zones and fee management

### 👨‍💼 Admin Panel
- Comprehensive dashboard with analytics
- User and shop management
- Bulk operations
- System notifications
- Audit trail for admin actions
- Revenue and order statistics

## Technology Stack

- **Backend**: Django 5.2.4 + Django REST Framework 3.15.2
- **Database**: PostgreSQL (production) / SQLite (development)
- **Authentication**: JWT (JSON Web Tokens)
- **File Storage**: Cloudinary
- **API Documentation**: drf-spectacular (Swagger/OpenAPI)
- **Deployment**: Docker + Nginx + Gunicorn

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL (for production)
- Cloudinary account

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd DealsBasket_Project
```

2. **Create virtual environment**
```bash
python -m venv env
source env/bin/activate  # Linux/Mac
# or
env\Scripts\activate  # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment setup**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Database setup**
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

6. **Run development server**
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/`

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`. This single file works for all environments (development, testing, production, and Render deployment):

```env
# =============================================================================
# DEALSBASKET ENVIRONMENT CONFIGURATION
# =============================================================================
# This file contains all environment variables for DealsBasket application
# Works for development, testing, production, and Render deployment
# =============================================================================

# PROJECT CONFIGURATION
PROJECT_NAME=DealsBasket
ENVIRONMENT=development

# DJANGO CONFIGURATION
SECRET_KEY=your-secret-key-here-generate-a-new-one-for-production
DEBUG=True
DJANGO_SETTINGS_MODULE=server.settings.development
ALLOWED_HOSTS=localhost,127.0.0.1

# DATABASE CONFIGURATION
DB_ENGINE=django.db.backends.postgresql
DB_NAME=dealsbasket_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

# For Render deployment, DATABASE_URL will be automatically set

# CLOUDINARY CONFIGURATION (Media Storage)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
USE_CLOUDINARY_FOR_MEDIA=True

# CORS CONFIGURATION
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
CORS_ALLOW_CREDENTIALS=True

# JWT CONFIGURATION
JWT_SECRET_KEY=your-jwt-secret-key-generate-a-new-one
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7
JWT_ALLOW_REFRESH=True

# SUPERUSER CONFIGURATION (for automated deployment)
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@dealsbasket.com
DJANGO_SUPERUSER_PASSWORD=your-secure-admin-password
```

**Environment-Specific Notes:**

- **Development**: Set `DEBUG=True`, `ENVIRONMENT=development`
- **Production**: Set `DEBUG=False`, `ENVIRONMENT=production`, generate new secret keys
- **Render**: Set `ALLOWED_HOSTS=.onrender.com,localhost,127.0.0.1`, enable security settings



### Cloudinary Setup

1. Create a Cloudinary account
2. Get your cloud name, API key, and API secret
3. Add credentials to your `.env` file

## API Documentation

### Interactive Documentation
- **Swagger UI**: `http://localhost:8000/api/docs/`
- **ReDoc**: `http://localhost:8000/api/redoc/`
- **OpenAPI Schema**: `http://localhost:8000/api/schema/`

### API Endpoints

#### Authentication
- `POST /api/v1/users/register/` - User registration
- `GET /api/v1/users/me/` - Current user info
- `PUT /api/v1/users/profile/` - Update profile

#### Shops
- `GET /api/v1/shops/` - List approved shops
- `POST /api/v1/shops/register/` - Register shop (shopkeepers)
- `GET /api/v1/shops/my-shop/` - My shop details

#### Products
- `GET /api/v1/products/` - List products
- `GET /api/v1/products/search/` - Search products
- `POST /api/v1/products/my-products/` - Create product (shopkeepers)

#### Orders
- `POST /api/v1/orders/create/` - Place order
- `GET /api/v1/orders/` - My orders
- `GET /api/v1/orders/shop/` - Shop orders (shopkeepers)

#### Delivery
- `GET /api/v1/delivery/assignments/` - Delivery assignments
- `POST /api/v1/delivery/update-location/` - Update location

#### Admin
- `GET /api/v1/admin/dashboard/` - Admin dashboard
- `POST /api/v1/admin/bulk/users/` - Bulk user actions

## Deployment

### Docker Deployment

1. **Build and run with Docker Compose**
```bash
docker-compose up -d
```

2. **Run migrations**
```bash
docker-compose exec web python manage.py migrate
```

3. **Create superuser**
```bash
docker-compose exec web python manage.py createsuperuser
```

### Manual Deployment

1. **Set production environment**
```bash
export DJANGO_SETTINGS_MODULE=server.settings.production
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Collect static files**
```bash
python manage.py collectstatic
```

4. **Run migrations**
```bash
python manage.py migrate
```

5. **Start with Gunicorn**
```bash
gunicorn server.wsgi:application --bind 0.0.0.0:8000
```

## Project Structure

```
DealsBasket_Project/
├── server/                 # Django project settings
│   ├── settings/          # Split settings (base, dev, prod)
│   ├── urls.py           # Main URL configuration
│   └── wsgi.py           # WSGI configuration
├── users/                 # User management & authentication
├── shop/                  # Shop management
├── products/              # Product catalog
├── orders/                # Order management
├── delivery/              # Delivery system
├── adminpanel/            # Admin functionality
├── requirements.txt       # Python dependencies
├── docker-compose.yml     # Docker configuration
├── Dockerfile            # Docker image definition
├── nginx.conf            # Nginx configuration
└── README.md             # This file
```

## Testing

Run tests with:
```bash
python manage.py test
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please open an issue in the repository.
