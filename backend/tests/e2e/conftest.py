import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from uuid import uuid4

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.main import app
from app.modules.auth.models import User


@pytest.fixture
def e2e_client():
    """E2E test client"""
    app.dependency_overrides.clear()
    return TestClient(app)


@pytest.fixture
def e2e_mock_user():
    """Mock user for E2E tests"""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "test@example.com"
    user.is_active = True
    return user


@pytest.fixture
def e2e_auth_client(e2e_client, e2e_mock_user):
    """Authenticated E2E test client"""
    from app.common.dependencies import get_current_user
    
    async def override_get_current_user():
        return e2e_mock_user
    
    e2e_client.app.dependency_overrides[get_current_user] = override_get_current_user
    
    yield e2e_client, e2e_mock_user
    
    e2e_client.app.dependency_overrides.clear()
