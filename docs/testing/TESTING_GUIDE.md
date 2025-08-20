# DealsBasket Testing Guide

## Overview

This guide provides comprehensive information about testing the DealsBasket Django backend API. The testing infrastructure includes unit tests, integration tests, API tests, and coverage reporting.

## Testing Stack

- **Django Test Framework**: Built-in Django testing capabilities
- **pytest**: Modern Python testing framework with powerful fixtures
- **pytest-django**: Django integration for pytest
- **factory-boy**: Test data generation
- **coverage.py**: Code coverage measurement
- **model-bakery**: Alternative test data generation

## Setup Instructions

### 1. Install Testing Dependencies

```bash
# Activate virtual environment
source env/bin/activate  # Linux/Mac
# or
env\Scripts\activate  # Windows

# Install testing packages
pip install factory-boy coverage pytest pytest-django pytest-cov pytest-mock model-bakery
```

### 2. Configure Environment

The project includes test-specific settings in `server/settings/test.py`:

- In-memory SQLite database for speed
- Disabled migrations for faster test runs
- Mock Cloudinary configurations
- Simplified password hashing
- Null logging handler

### 3. Run Tests

```bash
# Run all Django tests
python manage.py test --settings=server.settings.test

# Run specific app tests
python manage.py test users.tests --settings=server.settings.test
python manage.py test shop.tests --settings=server.settings.test
python manage.py test products.tests --settings=server.settings.test

# Run with pytest
pytest --verbose

# Run with coverage
pytest --cov=. --cov-report=html --cov-report=term-missing

# Use the test runner script
python run_tests.py
python run_tests.py users
python run_tests.py coverage
```

## Test Structure

### Directory Organization

```
app_name/
├── tests/
│   ├── __init__.py
│   ├── test_models.py      # Model tests
│   ├── test_views.py       # API endpoint tests
│   ├── test_serializers.py # Serializer tests
│   ├── test_permissions.py # Permission tests
│   └── test_utils.py       # Utility function tests
└── tests.py               # Legacy file (kept for Django discovery)
```

### Test Categories

#### 1. Model Tests (`test_models.py`)
- Model creation and validation
- Field constraints and relationships
- Model methods and properties
- Database constraints

#### 2. View Tests (`test_views.py`)
- API endpoint functionality
- HTTP status codes
- Request/response data
- Authentication and permissions
- Error handling

#### 3. Serializer Tests (`test_serializers.py`)
- Data serialization/deserialization
- Field validation
- Custom serializer methods
- Nested serializers

#### 4. Permission Tests (`test_permissions.py`)
- Role-based access control
- Object-level permissions
- Authentication requirements

## Test Examples

### Model Test Example

```python
@pytest.mark.django_db
class TestUserModel:
    def test_create_user(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            role='user'
        )
        assert user.username == 'testuser'
        assert user.is_user is True
```

### API Test Example

```python
@pytest.mark.django_db
class TestUserRegistration:
    def test_user_registration_success(self, api_client):
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123'
        }
        response = api_client.post('/api/v1/users/register/', data)
        assert response.status_code == 201
        assert 'user' in response.data
```

### Permission Test Example

```python
def test_shopkeeper_permission(self):
    permission = IsShopkeeper()
    request = self.factory.get('/')
    request.user = self.shopkeeper
    assert permission.has_permission(request, self.view) is True
```

## Fixtures and Test Data

### Global Fixtures (conftest.py)

- `api_client`: Unauthenticated API client
- `authenticated_client`: Authenticated API client
- `user`, `admin_user`, `shopkeeper_user`, `delivery_user`: User instances
- `mock_firebase_auth`: Mock Firebase authentication
- `mock_cloudinary`: Mock Cloudinary uploads

### Using Fixtures

```python
def test_with_authenticated_user(authenticated_client, user):
    response = authenticated_client.get('/api/v1/users/profile/')
    assert response.status_code == 200
    assert response.data['username'] == user.username
```

## Coverage Requirements

- **Minimum Coverage**: 70% overall
- **Target Coverage**: 80%+ for critical components
- **Critical Areas**: Authentication, permissions, order processing

### Coverage Commands

```bash
# Generate coverage report
coverage run --source='.' manage.py test --settings=server.settings.test
coverage html
coverage report

# View coverage report
open htmlcov/index.html  # Mac
start htmlcov/index.html  # Windows
```

## Testing Best Practices

### 1. Test Naming
- Use descriptive test names: `test_user_registration_with_invalid_email`
- Follow pattern: `test_<action>_<condition>_<expected_result>`

### 2. Test Organization
- One test class per model/view/serializer
- Group related tests together
- Use setup methods for common test data

### 3. Test Data
- Use factories for complex objects
- Keep test data minimal and focused
- Clean up test data automatically

### 4. Assertions
- Use specific assertions: `assert user.is_active is True`
- Test both positive and negative cases
- Verify database state changes

### 5. Mocking
- Mock external services (Firebase, Cloudinary)
- Mock time-dependent operations
- Don't mock the code under test

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Run tests
      run: |
        python manage.py test --settings=server.settings.test
    - name: Generate coverage
      run: |
        coverage run --source='.' manage.py test --settings=server.settings.test
        coverage xml
    - name: Upload coverage
      uses: codecov/codecov-action@v1
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `DJANGO_SETTINGS_MODULE` is set correctly
2. **Database Errors**: Use `@pytest.mark.django_db` for database tests
3. **Permission Errors**: Check user roles and authentication in tests
4. **Mock Failures**: Verify mock paths and return values

### Debug Commands

```bash
# Run specific test with verbose output
python manage.py test users.tests.test_models.TestUserModel.test_create_user --verbosity=2

# Run with pdb debugging
pytest --pdb

# Run with print statements
pytest -s
```

## Performance Testing

### Load Testing with Locust

```python
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def get_products(self):
        self.client.get("/api/v1/products/")
    
    @task
    def get_shops(self):
        self.client.get("/api/v1/shops/")
```

## Security Testing

### Authentication Tests
- Test invalid tokens
- Test expired tokens
- Test role-based access

### Input Validation Tests
- Test SQL injection attempts
- Test XSS attempts
- Test malformed data

## Monitoring and Alerts

### Test Metrics to Track
- Test execution time
- Coverage percentage
- Test failure rate
- Flaky test identification

### Alerts
- Coverage drops below threshold
- Test failures in CI/CD
- Performance regression

## Next Steps

1. **Implement remaining test suites** for orders, delivery, and admin panel
2. **Set up CI/CD pipeline** with automated testing
3. **Add performance benchmarks** for critical endpoints
4. **Implement security testing** for authentication flows
5. **Add integration tests** for complete user workflows
