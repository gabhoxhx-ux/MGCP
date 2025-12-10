import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def test_imports():
    """Verify all key modules import correctly."""
    try:
        from app import app, db
        from app.models import Cliente, Propuesta, DocumentoGenerado
        from app import routes
        assert True, "All imports successful"
    except Exception as e:
        assert False, f"Import failed: {e}"


def test_app_config():
    """Verify app configuration."""
    from app import app
    assert app.config['TESTING'] is not None, "App config missing"
    assert app.config.get('SQLALCHEMY_DATABASE_URI') is not None, "DB URI not configured"
