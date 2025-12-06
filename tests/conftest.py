import os
import pytest
import hmac
import hashlib
from fastapi.testclient import TestClient
from app.main import app
from app.storage import db_repo
from app.config import settings

@pytest.fixture(autouse=True)
def test_db():
    """
    Overrides the database for tests to use a temporary file.
    """
    original_db = db_repo.db_path
    test_db_path = "/tmp/test_app.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    db_repo.db_path = test_db_path
    db_repo._init_db()
    
    yield
    
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    db_repo.db_path = original_db

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def valid_signature():
    def _sign(body: str, secret: str = settings.webhook_secret):
        return hmac.new(
            secret.encode(), 
            body.encode(), 
            hashlib.sha256
        ).hexdigest()
    return _sign