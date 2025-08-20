#!/usr/bin/env python
"""
Test runner script for DealsBasket project
"""
import os
import sys
import subprocess
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(project_dir))

# Set Django settings module for tests
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings.test')

def run_django_tests():
    """Run Django tests"""
    print("🧪 Running Django Tests...")
    cmd = [sys.executable, 'manage.py', 'test', '--verbosity=2']
    result = subprocess.run(cmd, cwd=project_dir)
    return result.returncode == 0

def run_pytest():
    """Run pytest tests"""
    print("🧪 Running Pytest Tests...")
    cmd = [
        sys.executable, '-m', 'pytest',
        '--verbose',
        '--tb=short',
        '--cov=.',
        '--cov-report=html',
        '--cov-report=term-missing',
        '--cov-fail-under=70'
    ]
    result = subprocess.run(cmd, cwd=project_dir)
    return result.returncode == 0

def run_specific_app_tests(app_name):
    """Run tests for a specific app"""
    print(f"🧪 Running tests for {app_name} app...")
    cmd = [sys.executable, 'manage.py', 'test', f'apps.{app_name}.tests', '--verbosity=2']
    result = subprocess.run(cmd, cwd=project_dir)
    return result.returncode == 0

def run_coverage_report():
    """Generate coverage report"""
    print("📊 Generating coverage report...")
    cmd = [sys.executable, '-m', 'coverage', 'html']
    result = subprocess.run(cmd, cwd=project_dir)
    if result.returncode == 0:
        print("📊 Coverage report generated in htmlcov/index.html")
    return result.returncode == 0

def main():
    """Main test runner"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'django':
            success = run_django_tests()
        elif command == 'pytest':
            success = run_pytest()
        elif command == 'coverage':
            success = run_coverage_report()
        elif command in ['users', 'shop', 'products', 'orders', 'delivery', 'adminpanel']:
            success = run_specific_app_tests(command)
        else:
            print(f"❌ Unknown command: {command}")
            print("Available commands: django, pytest, coverage, users, shop, products, orders, delivery, adminpanel")
            sys.exit(1)
    else:
        # Run all tests
        print("🚀 Running all tests...")
        django_success = run_django_tests()
        pytest_success = run_pytest()
        coverage_success = run_coverage_report()
        
        success = django_success and pytest_success and coverage_success
    
    if success:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()
