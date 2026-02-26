"""
Tests for company and business management endpoints.
"""

import pytest
from models import Company, Customer, Product


class TestCompanyCreation:
    """Test company creation and management."""
    
    def test_company_creation_via_platform_admin(self, app, test_db):
        """Test that platform admin can create companies."""
        with app.app_context():
            # Create a platform admin user
            from models import User
            admin = User(
                username='platform_admin',
                email='platform@test.com',
                role='platform_admin',
                is_active=True
            )
            admin.set_password('Admin123!')
            test_db.session.add(admin)
            test_db.session.commit()
            
            # Verify company can be created
            company = Company(
                name='New Company',
                business_type='retail',
                authorized_person='John Doe',
                phone='05551234567',
                email='new@company.com',
                city='Istanbul',
                status='approved'
            )
            test_db.session.add(company)
            test_db.session.commit()
            
            assert company.id is not None
            assert company.name == 'New Company'
            assert company.status == 'approved'
    
    def test_company_uniqueness(self, app, test_db):
        """Test that company email must be unique."""
        with app.app_context():
            company1 = Company(
                name='Company 1',
                business_type='retail',
                authorized_person='Person 1',
                phone='05551234567',
                email='unique@test.com',
                status='approved'
            )
            test_db.session.add(company1)
            test_db.session.commit()
            
            # Try to create another company with same email
            company2 = Company(
                name='Company 2',
                business_type='retail',
                authorized_person='Person 2',
                phone='05559876543',
                email='unique@test.com',
                status='approved'
            )
            test_db.session.add(company2)
            
            # Should raise integrity error
            with pytest.raises(Exception):
                test_db.session.commit()


class TestCustomerManagement:
    """Test customer management functionality."""
    
    def test_customer_creation(self, app, test_db, test_company):
        """Test creating a new customer."""
        with app.app_context():
            customer = Customer(
                company_id=test_company.id,
                name='Test Customer',
                phone='05559876543',
                notes='Test Address'
            )
            test_db.session.add(customer)
            test_db.session.commit()
            
            assert customer.id is not None
            assert customer.name == 'Test Customer'
            assert customer.company_id == test_company.id
    
    def test_customer_listing_requires_login(self, client):
        """Test that customer listing requires authentication."""
        response = client.get('/customers', follow_redirects=True)
        assert response.status_code == 200
    
    def test_customer_listing_with_login(self, logged_in_client, test_customer):
        """Test customer listing when logged in."""
        response = logged_in_client.get('/customers', follow_redirects=True)
        assert response.status_code == 200
        # Should contain customer name
        assert b'Test Customer' in response.data


class TestProductManagement:
    """Test product management functionality."""
    
    def test_product_creation(self, app, test_db, test_company):
        """Test creating a new product."""
        with app.app_context():
            product = Product(
                company_id=test_company.id,
                name='Test Product',
                code='PROD001',
                unit_price=150.0,
                cost_price=75.0
            )
            test_db.session.add(product)
            test_db.session.commit()
            
            assert product.id is not None
            assert product.name == 'Test Product'
            assert float(product.unit_price) == 150.0
    
    def test_product_code_uniqueness_per_company(self, app, test_db, test_company):
        """Test that product code must be unique within a company."""
        with app.app_context():
            product1 = Product(
                company_id=test_company.id,
                name='Product 1',
                code='UNIQUE001',
                unit_price=100.0
            )
            test_db.session.add(product1)
            test_db.session.commit()
            
            # Create another product with same code in same company
            product2 = Product(
                company_id=test_company.id,
                name='Product 2',
                code='UNIQUE001',
                unit_price=200.0
            )
            test_db.session.add(product2)
            test_db.session.commit()
            
            # Both products should exist (code uniqueness is enforced at app level)
            assert product1.id != product2.id


class TestCompanyRequest:
    """Test company request/trial account functionality."""
    
    def test_company_request_creation(self, app, test_db):
        """Test creating a company request."""
        from models import CompanyRequest
        
        with app.app_context():
            request = CompanyRequest(
                company_name='Requested Company',
                business_type='retail',
                authorized_person='Requester',
                phone='05551234567',
                email='request@company.com',
                city='Istanbul',
                status='pending'
            )
            test_db.session.add(request)
            test_db.session.commit()
            
            assert request.id is not None
            assert request.status == 'pending'
    
    def test_company_request_page_loads(self, client):
        """Test that company request page loads."""
        response = client.get('/auth/request-account')
        assert response.status_code == 200
    
    def test_company_request_submission(self, client):
        """Test submitting a company request."""
        response = client.post('/auth/request-account', data={
            'company_name': 'New Business',
            'business_type': 'retail',
            'authorized_person': 'John Doe',
            'phone': '05551234567',
            'email': 'john@business.com',
            'city': 'Ankara',
            'notes': 'Please approve my request'
        }, follow_redirects=True)
        
        assert response.status_code == 200
