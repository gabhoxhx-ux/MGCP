import os
import sys
import pytest

# Ensure project root on path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from app import app, db
from app.models import Cliente, Propuesta


@pytest.fixture
def client():
    """Flask test client with app context."""
    app.config['TESTING'] = True
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


class TestAccess:
    """Test basic access and routing."""

    def test_home_accessible(self, client):
        """Home page should be accessible."""
        resp = client.get("/")
        assert resp.status_code in (200, 302), "Home not accessible"

    def test_dashboard_protected(self, client):
        """Dashboard should redirect unauthenticated users."""
        resp = client.get("/dashboard", follow_redirects=False)
        assert resp.status_code in (302, 401, 403), "Dashboard not protected"

    def test_login_page_accessible(self, client):
        """Login page should be accessible."""
        resp = client.get("/login")
        assert resp.status_code == 200, "Login page not found"


class TestDatabase:
    """Test database integrity."""

    def test_cliente_table_exists(self, client):
        """Cliente table should exist and be queryable."""
        with app.app_context():
            count = Cliente.query.count()
            assert count >= 0, "Cliente table not accessible"

    def test_propuesta_table_exists(self, client):
        """Propuesta table should exist and be queryable."""
        with app.app_context():
            count = Propuesta.query.count()
            assert count >= 0, "Propuesta table not accessible"


class TestSecurity:
    """Test security headers and basic access control."""

    def test_security_headers_present(self, client):
        """Security headers should be present in responses."""
        resp = client.get("/")
        # Check for common security headers
        has_headers = (
            'X-Content-Type-Options' in resp.headers or
            'X-Frame-Options' in resp.headers or
            'Strict-Transport-Security' in resp.headers
        )
        assert has_headers, "Security headers missing"

    def test_no_sensitive_data_in_home(self, client):
        """Home page should not expose sensitive paths in clear text."""
        resp = client.get("/")
        # Very basic check: not expecting database URLs or secrets
        assert 'password' not in resp.data.decode().lower(), "Possible credential exposure"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
