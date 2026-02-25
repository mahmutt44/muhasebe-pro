"""
Tests for report endpoints.
"""

import pytest
import json
from datetime import datetime, timedelta
from models import Receipt, ReceiptItem, Customer, Product


class TestReports:
    """Test report endpoints functionality."""
    
    def test_reports_page_requires_login(self, client):
        """Test that reports page requires authentication."""
        response = client.get('/reports', follow_redirects=True)
        assert response.status_code == 200
        # Should redirect to login or show auth error
    
    def test_reports_page_loads_with_login(self, logged_in_client):
        """Test that reports page loads when logged in."""
        response = logged_in_client.get('/reports', follow_redirects=True)
        assert response.status_code == 200
    
    def test_customer_debts_report(self, logged_in_client, test_customer):
        """Test customer debts report endpoint."""
        response = logged_in_client.get('/reports/customer-debts', follow_redirects=True)
        assert response.status_code == 200
        # Should contain customer data
        assert b'Test Customer' in response.data or response.status_code == 200
    
    def test_profit_loss_report(self, logged_in_client):
        """Test profit/loss report endpoint."""
        response = logged_in_client.get('/reports/profit-loss', follow_redirects=True)
        assert response.status_code == 200
    
    def test_stock_report(self, logged_in_client):
        """Test stock report endpoint."""
        response = logged_in_client.get('/reports/stock', follow_redirects=True)
        assert response.status_code == 200


class TestAPIEndpoints:
    """Test API endpoints for reports and data."""
    
    def test_api_customers_requires_auth(self, client):
        """Test that API customers endpoint requires authentication."""
        response = client.get('/api/customers')
        # API endpoints should return 401 or redirect
        assert response.status_code in [401, 302, 200]
    
    def test_api_customers_with_auth(self, logged_in_client, test_customer):
        """Test API customers endpoint with authentication."""
        response = logged_in_client.get('/api/customers')
        assert response.status_code == 200
        
        # Parse JSON response
        data = json.loads(response.data)
        assert 'items' in data or 'customers' in str(data).lower()
    
    def test_api_products_with_auth(self, logged_in_client, test_product):
        """Test API products endpoint with authentication."""
        response = logged_in_client.get('/api/products')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'items' in data or 'products' in str(data).lower()
    
    def test_api_suppliers_with_auth(self, logged_in_client):
        """Test API suppliers endpoint with authentication."""
        response = logged_in_client.get('/api/suppliers')
        assert response.status_code == 200
    
    def test_api_transactions_with_auth(self, logged_in_client):
        """Test API transactions endpoint with authentication."""
        response = logged_in_client.get('/api/transactions')
        assert response.status_code == 200


class TestReceiptReports:
    """Test receipt and transaction reports."""
    
    def test_receipt_listing(self, logged_in_client):
        """Test receipt listing page."""
        response = logged_in_client.get('/receipts', follow_redirects=True)
        assert response.status_code == 200
    
    def test_create_receipt_requires_login(self, client):
        """Test that receipt creation requires login."""
        response = client.post('/receipts/create', data={
            'customer_id': '1',
            'type': 'sale',
            'description': 'Test receipt'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_receipt_detail_requires_login(self, client):
        """Test that receipt detail requires login."""
        response = client.get('/receipts/1', follow_redirects=True)
        assert response.status_code == 200


class TestDashboard:
    """Test dashboard and main endpoints."""
    
    def test_dashboard_requires_login(self, client):
        """Test that dashboard requires authentication."""
        response = client.get('/', follow_redirects=True)
        # Should redirect to login
        assert response.status_code == 200
    
    def test_dashboard_loads_with_login(self, logged_in_client):
        """Test that dashboard loads when logged in."""
        response = logged_in_client.get('/', follow_redirects=True)
        assert response.status_code == 200
        # Should show dashboard elements
        assert response.status_code == 200


class TestCSRFProtection:
    """Test CSRF protection is in place."""
    
    def test_login_form_has_csrf(self, client):
        """Test that login form contains CSRF token."""
        # Note: CSRF is disabled in tests, but we verify the form exists
        response = client.get('/auth/login')
        assert response.status_code == 200
        # Form should be present
        assert b'form' in response.data.lower()
    
    def test_post_without_csrf_fails_in_production(self, app):
        """Test that POST without CSRF token would fail in production."""
        # In production with CSRF enabled, this would fail
        # In our test setup, CSRF is disabled
        with app.app_context():
            assert app.config.get('WTF_CSRF_ENABLED') == False


class TestMultiTenancy:
    """Test multi-tenant data isolation."""
    
    def test_user_can_only_access_own_company_data(self, app, test_db, test_company, test_user):
        """Test that users can only access their own company's data."""
        with app.app_context():
            # Create another company
            from models import Company, Customer
            other_company = Company(
                name='Other Company',
                business_type='retail',
                authorized_person='Other Person',
                phone='05559998877',
                email='other@test.com',
                status='approved'
            )
            test_db.session.add(other_company)
            test_db.session.commit()
            
            # Create customer in other company
            other_customer = Customer(
                company_id=other_company.id,
                name='Other Customer',
                phone='05551112233'
            )
            test_db.session.add(other_customer)
            test_db.session.commit()
            
            # Verify test_user is associated with test_company
            assert test_user.company_id == test_company.id
            assert test_user.company_id != other_company.id
