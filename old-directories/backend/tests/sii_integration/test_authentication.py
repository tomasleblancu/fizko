"""
Test suite for SII authentication functionality
"""
import pytest
from app.integrations.sii import SIIClient


class TestAuthentication:
    """Test cases for SII login and authentication"""

    def test_login_success(self, sii_client_no_login, test_credentials):
        """Test successful login with valid credentials"""
        success = sii_client_no_login.login()

        assert success is True, "Login should succeed with valid credentials"
        assert sii_client_no_login.is_authenticated(), "Client should be authenticated after successful login"

    def test_authentication_state(self, sii_client):
        """Test that authenticated client reports correct state"""
        assert sii_client.is_authenticated(), "Logged-in client should report as authenticated"

    def test_cookies_obtained_after_login(self, sii_client):
        """Test that cookies are obtained after successful login"""
        cookies = sii_client.get_cookies()

        assert cookies is not None, "Cookies should not be None"
        assert len(cookies) > 0, "Should have at least one cookie after login"
        assert len(cookies) >= 10, f"Expected at least 10 cookies, got {len(cookies)}"

    def test_cookie_content(self, sii_client):
        """Test that obtained cookies have required fields"""
        cookies = sii_client.get_cookies()

        # Check first cookie has required fields
        cookie = cookies[0]
        assert 'name' in cookie, "Cookie should have 'name' field"
        assert cookie['name'], "Cookie name should not be empty"
