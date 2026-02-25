"""
Pytest configuration for Muhasebe Pro tests.

This module sets up the test environment with SQLite database
and provides fixtures for testing the Flask application.
"""

import os
import sys
import pytest
from datetime import datetime, timedelta

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import create_app, db
from models import User, Company, Customer, Product, Receipt, ReceiptItem


@pytest.fixture(scope='session')
def app():
    """Create application for testing with SQLite database."""
    # Set test environment variables
    os.environ['ENV'] = 'development'
    os.environ['FLASK_SECRET_KEY'] = 'test-secret-key'
    
    # Create app with test configuration
    app = create_app()
    
    # Configure test database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    
    with app.app_context():
        # Create all tables
        db.create_all()
        yield app
        # Clean up after tests
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Create test client for making HTTP requests."""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def test_db(app):
    """Provide database access for tests."""
    with app.app_context():
        yield db


@pytest.fixture(scope='function')
def test_company(app, test_db):
    """Create a test company."""
    with app.app_context():
        company = Company(
            name='Test Company',
            business_type='retail',
            authorized_person='Test Admin',
            phone='05551234567',
            email='test@company.com',
            city='Istanbul',
            status='approved'
        )
        test_db.session.add(company)
        test_db.session.commit()
        return company


@pytest.fixture(scope='function')
def test_user(app, test_db, test_company):
    """Create a test admin user."""
    with app.app_context():
        user = User(
            company_id=test_company.id,
            username='test_admin',
            email='admin@test.com',
            role='admin',
            is_active=True,
            force_password_change=False
        )
        user.set_password('Test123!')
        test_db.session.add(user)
        test_db.session.commit()
        return user


@pytest.fixture(scope='function')
def logged_in_client(client, test_user):
    """Create a logged-in test client."""
    # Login the test user
    response = client.post('/auth/login', data={
        'username': 'test_admin',
        'password': 'Test123!'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    return client


@pytest.fixture(scope='function')
def test_customer(app, test_db, test_company):
    """Create a test customer."""
    with app.app_context():
        customer = Customer(
            company_id=test_company.id,
            name='Test Customer',
            phone='05559876543',
            email='customer@test.com'
        )
        test_db.session.add(customer)
        test_db.session.commit()
        return customer


@pytest.fixture(scope='function')
def test_product(app, test_db, test_company):
    """Create a test product."""
    with app.app_context():
        product = Product(
            company_id=test_company.id,
            name='Test Product',
            code='TEST001',
            unit_price=100.0,
            cost_price=50.0
        )
        test_db.session.add(product)
        test_db.session.commit()
        return product
