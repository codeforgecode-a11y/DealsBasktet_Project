# DealsBasket Authentication System Documentation

## Overview

The DealsBasket application implements a comprehensive JWT-based authentication system:

1. **JWT (JSON Web Tokens)** - Native username/password authentication with access and refresh tokens

## Architecture

### Authentication Backend

#### JWT Authentication (`JWTAuthentication`)
- Native Django authentication using JWT tokens
- Supports access and refresh tokens
- Token blacklisting for secure logout
- Configurable token expiration times
- Role-based access control

### Security Features

#### Rate Limiting
- Login attempts: 5 per 5 minutes
- Token refresh: 20 per 5 minutes
- User registration: 3 per hour

#### Security Headers
- Content Security Policy (CSP)
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection
- Strict Transport Security (HTTPS)
- Referrer Policy

#### Authentication Logging
- All authentication attempts logged
- Failed login attempt tracking
- Suspicious activity detection
- IP-based monitoring

## API Endpoints

### JWT Authentication

#### Login
```http
POST /api/auth/jwt/login/
Content-Type: application/json

{
    "username": "user@example.com",  // or username
    "password": "password123"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Login successful",
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "access_token_expires": "2024-01-01T12:00:00Z",
    "refresh_token_expires": "2024-01-08T12:00:00Z",
    "user": { /* user profile data */ }
}
```

#### Token Refresh
```http
POST /api/auth/jwt/refresh/
Content-Type: application/json

{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Logout
```http
POST /api/auth/jwt/logout/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Token Verification
```http
POST /api/auth/jwt/verify/
Content-Type: application/json

{
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```



### User Management

#### Get Profile
```http
GET /api/auth/profile/
Authorization: Bearer <token>
```

#### Change Password
```http
POST /api/auth/jwt/change-password/
Authorization: Bearer <token>
Content-Type: application/json

{
    "old_password": "current_password",
    "new_password": "new_password123"
}
```

## Configuration

### Environment Variables

```bash
# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7
JWT_ALLOW_REFRESH=true



# Redis Configuration (for token blacklisting)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# CORS Configuration
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### Django Settings

```python
# Authentication backends
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'users.jwt_authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
}

# Security middleware
MIDDLEWARE = [
    'users.security_middleware.SecurityHeadersMiddleware',
    'users.security_middleware.RateLimitMiddleware',
    'users.security_middleware.AuthenticationLoggingMiddleware',
    # ... other middleware
]
```

## Frontend Integration

### JWT Authentication Flow

```javascript
// Login
const loginResponse = await fetch('/api/auth/jwt/login/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        username: 'user@example.com',
        password: 'password123'
    })
});

const { access_token, refresh_token } = await loginResponse.json();

// Store tokens securely
localStorage.setItem('access_token', access_token);
localStorage.setItem('refresh_token', refresh_token);

// Use token for authenticated requests
const response = await fetch('/api/v1/users/me/', {
    headers: {
        'Authorization': `Bearer ${access_token}`
    }
});
```



## Security Best Practices

### Token Storage
- Store JWT tokens in httpOnly cookies (recommended)
- Avoid localStorage for sensitive tokens
- Implement secure token refresh mechanism

### HTTPS
- Always use HTTPS in production
- Enable HSTS headers
- Use secure cookie flags

### Rate Limiting
- Monitor authentication endpoints
- Implement progressive delays for failed attempts
- Use IP-based and user-based rate limiting

### Logging and Monitoring
- Log all authentication events
- Monitor for suspicious patterns
- Set up alerts for multiple failed attempts

## Troubleshooting

### Common Issues



#### JWT Token Expired
```
Error: Token has expired
```
**Solution:** Use refresh token to get new access token

#### Rate Limit Exceeded
```
Error: Rate limit exceeded
```
**Solution:** Wait for rate limit window to reset or implement exponential backoff

### Testing Authentication

```bash
# Run authentication tests
python manage.py test users.tests.test_jwt_authentication
python manage.py test users.tests.test_authentication
python manage.py test users.tests.test_enhanced_authentication

# Run with coverage
python -m pytest users/tests/ --cov=users --cov-report=html
```

## Migration Guide

### JWT Authentication Setup

1. Configure JWT settings in environment variables
2. Update Django settings for JWT authentication
3. Implement JWT endpoints in frontend
4. Set up token refresh mechanism

### Security Considerations

- Rotate JWT secret keys regularly
- Monitor authentication logs
- Implement account lockout policies
- Use strong password requirements
- Enable two-factor authentication (future enhancement)
