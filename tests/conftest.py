import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Provide a TestClient for making requests to the app"""
    return TestClient(app)
