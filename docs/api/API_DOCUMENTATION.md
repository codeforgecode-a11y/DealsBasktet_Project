# DealsBasket API Documentation

## Overview

DealsBasket is a local e-commerce platform API built with Django REST Framework, featuring role-based access control, JWT authentication, and comprehensive order management.

## Base URL

```
http://localhost:8000/api/v1/
```

## Authentication

The API uses JWT token authentication. Include the JWT access token in the Authorization header:

```
Authorization: Bearer <jwt_access_token>
```

## User Roles

- **user**: Regular customers who can browse products and place orders
- **shopkeeper**: Shop owners who can manage their shops and products
- **delivery**: Delivery persons who can manage delivery assignments
- **admin**: System administrators with full access

## API Endpoints

### Authentication & Users

#### User Registration
```
POST /users/register/
```
Register a new user account.

#### User Profile
```
GET /users/profile/
PUT /users/profile/
```
Get or update current user profile.

#### Current User
```
GET /users/me/
```
Get current authenticated user details.

#### Change Password
```
POST /users/change-password/
```
Change user password.

### Shop Management

#### Shop Registration (Shopkeepers only)
```
POST /shops/register/
```
Register a new shop.

#### My Shop (Shopkeepers only)
```
GET /shops/my-shop/
PUT /shops/my-shop/
```
Get or update current user's shop.

#### Public Shop List
```
GET /shops/
```
List all approved and active shops.

#### Shop Search
```
GET /shops/search/?q=<query>&lat=<latitude>&lng=<longitude>
```
Search shops by name or location.

### Product Management

#### Public Product List
```
GET /products/
```
List all available products from approved shops.

#### Product Detail
```
GET /products/<id>/
```
Get detailed product information.

#### Product Search
```
GET /products/search/?q=<query>&category=<id>&shop=<id>&min_price=<price>&max_price=<price>
```
Search products with filters.

#### My Products (Shopkeepers only)
```
GET /products/my-products/
POST /products/my-products/
```
List or create products for current user's shop.

#### Product Management (Shopkeepers only)
```
GET /products/my-products/<id>/
PUT /products/my-products/<id>/
DELETE /products/my-products/<id>/
```
Manage individual products.

#### Image Upload (Shopkeepers only)
```
POST /products/upload-image/
```
Upload product images to Cloudinary.

#### Categories
```
GET /products/categories/
```
List all active product categories.

### Order Management

#### Place Order (Customers only)
```
POST /orders/create/
```
Create a new order.

#### Customer Orders
```
GET /orders/
GET /orders/<id>/
```
List customer's orders or get order details.

#### Cancel Order
```
POST /orders/<id>/cancel/
```
Cancel an order (if allowed).

#### Shop Orders (Shopkeepers only)
```
GET /orders/shop/
GET /orders/shop/<id>/
PUT /orders/shop/<id>/
```
Manage orders for current user's shop.

### Delivery Management

#### Delivery Profile (Delivery persons only)
```
GET /delivery/profile/
PUT /delivery/profile/
```
Get or update delivery person profile.

#### Delivery Assignments
```
GET /delivery/assignments/
GET /delivery/assignments/<id>/
PUT /delivery/assignments/<id>/
```
Manage delivery assignments.

#### Update Location
```
POST /delivery/update-location/
```
Update current location for tracking.

#### Delivery Statistics
```
GET /delivery/stats/
```
Get delivery person statistics.

#### Generate/Verify OTP
```
POST /orders/delivery/<id>/generate-otp/
POST /orders/delivery/<id>/verify-otp/
```
Generate and verify OTP for delivery confirmation.

### Admin Panel

#### Dashboard
```
GET /admin/dashboard/
```
Get system statistics and overview.

#### User Management
```
GET /users/
GET /users/<id>/
PUT /users/<id>/
DELETE /users/<id>/
```
Manage users (admin only).

#### Shop Management
```
GET /shops/admin/
PUT /shops/<id>/status/
```
Manage shop approvals and status.

#### System Settings
```
GET /admin/settings/
POST /admin/settings/
PUT /admin/settings/<id>/
```
Manage system-wide settings.

#### Statistics
```
GET /admin/stats/users/
GET /admin/stats/orders/
GET /admin/stats/revenue/
```
Get detailed system statistics.

#### Bulk Actions
```
POST /admin/bulk/users/
POST /admin/bulk/shops/
```
Perform bulk operations on users or shops.

#### Notifications
```
GET /admin/notifications/
POST /admin/notifications/
```
Manage system notifications.

## Response Format

### Success Response
```json
{
  "data": {...},
  "message": "Success message"
}
```

### Error Response
```json
{
  "error": "Error message",
  "details": {...}
}
```

### Pagination
```json
{
  "count": 100,
  "next": "http://api.example.org/accounts/?page=4",
  "previous": "http://api.example.org/accounts/?page=2",
  "results": [...]
}
```

## Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Permission denied
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

## Order Status Flow

1. **pending** - Order placed, awaiting shop acceptance
2. **accepted** - Shop accepted the order
3. **packed** - Order packed and ready for pickup
4. **out_for_delivery** - Order picked up by delivery person
5. **delivered** - Order delivered to customer
6. **cancelled** - Order cancelled

## Environment Variables

See `.env.example` for required environment variables including:
- Database configuration
- JWT configuration
- Cloudinary settings
- CORS configuration

## Interactive Documentation

- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`
- OpenAPI Schema: `/api/schema/`
