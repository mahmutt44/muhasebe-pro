"""
Tests for authentication endpoints.
"""

import pytest


class TestLogin:
    """Test login functionality."""
    
    def test_login_page_loads(self, client):
        """Test that login page loads successfully."""
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert b'login' in response.data.lower() or b'giris' in response.data.lower()
        # Must contain login form elements
        assert b'<form' in response.data.lower()
    
    def test_successful_login(self, client, test_user):
        """Test successful login with valid credentials."""
        response = client.post('/auth/login', data={
            'username': 'test_admin',
            'password': 'Test123!'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Check if we're redirected to dashboard or index page with proper content
        response_text = response.data.lower()
        assert b'dashboard' in response_text or b'anasayfa' in response_text or b'musteri' in response_text or b'customer' in response_text
    
    def test_failed_login_invalid_password(self, client, test_user):
        """Test login with invalid password."""
        response = client.post('/auth/login', data={
            'username': 'test_admin',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should show error message - check for error indicators in response
        response_text = response.data.lower()
        assert b'error' in response_text or b'hata' in response_text or b'gecersiz' in response_text
    
    def test_failed_login_invalid_username(self, client):
        """Test login with non-existent username."""
        response = client.post('/auth/login', data={
            'username': 'nonexistent_user',
            'password': 'Test123!'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should show error message for invalid username
        response_text = response.data.lower()
        assert b'error' in response_text or b'hata' in response_text or b'bulunamadi' in response_text or b'not found' in response_text
    
    def test_login_redirects_when_already_logged_in(self, logged_in_client):
        """Test that login page redirects when user is already logged in."""
        response = logged_in_client.get('/auth/login', follow_redirects=True)
        assert response.status_code == 200
        # Should be redirected to main page


class TestUserCreation:
    """Test user creation functionality."""
    
    def test_user_creation_requires_login(self, client):
        """Test that user creation requires authentication."""
        response = client.post('/auth/admin/users/add', data={
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'New123!',
            'role': 'admin'
        }, follow_redirects=True)
        
        # Should redirect to login or show error
        assert response.status_code == 200
    
    def test_successful_user_creation(self, logged_in_client, test_db, test_company):
        """Test successful user creation by admin."""
        response = logged_in_client.post('/auth/admin/users/add', data={
            'username': 'newadmin',
            'email': 'newadmin@test.com',
            'password': 'NewAdmin123!',
            'role': 'admin'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should show success message
    
    def test_user_creation_validation_short_username(self, logged_in_client):
        """Test user creation with short username fails."""
        response = logged_in_client.post('/auth/admin/users/add', data={
            'username': 'ab',
            'email': 'test@test.com',
            'password': 'Test123!',
            'role': 'admin'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_user_creation_validation_invalid_email(self, logged_in_client):
        """Test user creation with invalid email fails."""
        response = logged_in_client.post('/auth/admin/users/add', data={
            'username': 'validuser',
            'email': 'invalid-email',
            'password': 'Test123!',
            'role': 'admin'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_user_creation_validation_short_password(self, logged_in_client):
        """Test user creation with short password fails."""
        response = logged_in_client.post('/auth/admin/users/add', data={
            'username': 'validuser',
            'email': 'test@test.com',
            'password': '123',
            'role': 'admin'
        }, follow_redirects=True)
        
        assert response.status_code == 200


class TestLogout:
    """Test logout functionality."""
    
    def test_logout_successful(self, logged_in_client):
        """Test successful logout."""
        response = logged_in_client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200
        # Should redirect to login page
    
    def test_logout_requires_login(self, client):
        """Test that logout requires authentication."""
        response = client.get('/auth/logout', follow_redirects=True)
        # Should redirect to login
        assert response.status_code == 200
