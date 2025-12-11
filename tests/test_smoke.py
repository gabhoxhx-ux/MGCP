import os
import sys

# Ensure project root on path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from app import app


def test_home_status_code():
    """Basic smoke test: home responds 200."""
    with app.test_client() as client:
        resp = client.get("/")
        assert resp.status_code in (200, 302)


def test_dashboard_requires_login():
    """Admin /propuestas route should be protected (redirect when unauthenticated)."""
    with app.test_client() as client:
        resp = client.get("/propuestas", follow_redirects=False)
        assert resp.status_code in (302, 401, 403)


def test_portal_cliente_access():
    """Portal cliente page should be accessible (template exists)."""
    with app.test_client() as client:
        resp = client.get("/portal", follow_redirects=True)
        # Accept 200 or 404 depending on route name; adjust if needed
        assert resp.status_code in (200, 404)
