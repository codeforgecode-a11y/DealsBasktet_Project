#!/usr/bin/env python
"""
Test setup script for DealsBasket project
This script helps set up the testing environment and validates the test configuration
"""
import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required for testing")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def check_django_installation():
    """Check if Django is installed"""
    try:
        import django
        print(f"✅ Django {django.get_version()} is installed")
        return True
    except ImportError:
        print("❌ Django is not installed")
        return False

def install_testing_dependencies():
    """Install testing dependencies"""
    dependencies = [
        'factory-boy==3.3.1',
        'coverage==7.6.1',
        'pytest==8.3.3',
        'pytest-django==4.9.0',
        'pytest-cov==5.0.0',
        'pytest-mock==3.14.0',
        'model-bakery==1.19.5'
    ]
    
    print("📦 Installing testing dependencies...")
    for dep in dependencies:
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', dep], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Installed {dep}")
            else:
                print(f"❌ Failed to install {dep}: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error installing {dep}: {e}")
            return False
    
    return True

def check_test_settings():
    """Check if test settings file exists and is valid"""
    test_settings_path = Path('server/settings/test.py')
    if not test_settings_path.exists():
        print("❌ Test settings file not found")
        return False
    
    print("✅ Test settings file exists")
    return True

def check_test_directories():
    """Check if test directories are properly set up"""
    apps = ['users', 'shop', 'products', 'orders', 'delivery', 'adminpanel']
    all_good = True
    
    for app in apps:
        test_dir = Path(f'{app}/tests')
        if test_dir.exists():
            print(f"✅ {app}/tests directory exists")
        else:
            print(f"❌ {app}/tests directory missing")
            all_good = False
    
    return all_good

def validate_test_configuration():
    """Validate test configuration files"""
    config_files = [
        'pytest.ini',
        '.coveragerc',
        'conftest.py'
    ]
    
    all_good = True
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"✅ {config_file} exists")
        else:
            print(f"❌ {config_file} missing")
            all_good = False
    
    return all_good

def run_basic_django_check():
    """Run basic Django system check"""
    try:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'server.settings.test'
        result = subprocess.run([sys.executable, 'manage.py', 'check', '--deploy'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Django system check passed")
            return True
        else:
            print(f"❌ Django system check failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error running Django check: {e}")
        return False

def create_test_database():
    """Create test database and run migrations"""
    try:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'server.settings.test'
        
        # Run migrations
        result = subprocess.run([sys.executable, 'manage.py', 'migrate', '--run-syncdb'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Test database migrations completed")
            return True
        else:
            print(f"❌ Test database migration failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error creating test database: {e}")
        return False

def run_sample_test():
    """Run a simple test to verify everything works"""
    try:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'server.settings.test'
        
        # Create a simple test file
        simple_test = '''
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
def test_user_creation():
    """Simple test to verify test setup works"""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    assert user.username == 'testuser'
    assert user.email == 'test@example.com'

class SimpleTestCase(TestCase):
    def test_simple(self):
        """Simple Django test case"""
        self.assertTrue(True)
'''
        
        # Write test file
        with open('simple_test.py', 'w') as f:
            f.write(simple_test)
        
        # Run the test
        result = subprocess.run([sys.executable, 'manage.py', 'test', 'simple_test'], 
                              capture_output=True, text=True)
        
        # Clean up
        os.remove('simple_test.py')
        
        if result.returncode == 0:
            print("✅ Sample test passed")
            return True
        else:
            print(f"❌ Sample test failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error running sample test: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up DealsBasket testing environment...\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("Django Installation", check_django_installation),
        ("Test Settings", check_test_settings),
        ("Test Directories", check_test_directories),
        ("Test Configuration", validate_test_configuration),
    ]
    
    # Run basic checks
    all_passed = True
    for name, check_func in checks:
        print(f"\n📋 Checking {name}...")
        if not check_func():
            all_passed = False
    
    if not all_passed:
        print("\n❌ Some basic checks failed. Please fix the issues above.")
        return False
    
    # Install dependencies
    print("\n📦 Installing dependencies...")
    if not install_testing_dependencies():
        print("\n❌ Failed to install testing dependencies.")
        return False
    
    # Run Django checks
    print("\n🔧 Running Django checks...")
    if not run_basic_django_check():
        print("\n❌ Django configuration check failed.")
        return False
    
    # Create test database
    print("\n🗄️ Setting up test database...")
    if not create_test_database():
        print("\n❌ Test database setup failed.")
        return False
    
    # Run sample test
    print("\n🧪 Running sample test...")
    if not run_sample_test():
        print("\n❌ Sample test failed.")
        return False
    
    print("\n✅ Test environment setup completed successfully!")
    print("\n📚 Next steps:")
    print("1. Run tests: python manage.py test --settings=server.settings.test")
    print("2. Run with coverage: python run_tests.py coverage")
    print("3. Run specific app tests: python run_tests.py users")
    print("4. Read TESTING_GUIDE.md for detailed instructions")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
