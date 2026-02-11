import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

@pytest.fixture
def mock_redis():
    """Mock Redis client for testing"""
    mock_client = Mock()
    mock_client.get.return_value = None
    mock_client.set.return_value = True
    mock_client.hgetall.return_value = {}
    mock_client.lrange.return_value = []
    return mock_client

@pytest.fixture
def mock_celery():
    """Mock Celery app for testing"""
    mock_app = Mock()
    mock_app.send_task.return_value = Mock(id="test-task-id")
    return mock_app

@pytest.fixture
def sample_requirements():
    """Sample user requirements for testing"""
    return """
    Need to test a user authentication system with the following features:
    - Login with email/password
    - Password reset functionality
    - Session management
    - Security validation
    """

@pytest.fixture
def sample_test_results():
    """Sample test results for testing"""
    return {
        "session_id": "test-session-123",
        "timestamp": "2024-01-01T12:00:00Z",
        "agent": "qa-analyst",
        "results": {
            "total_tests": 100,
            "passed": 85,
            "failed": 15,
            "coverage": 78.5,
            "findings": [
                {
                    "severity": "high",
                    "category": "security",
                    "description": "SQL injection vulnerability found"
                },
                {
                    "severity": "medium",
                    "category": "performance", 
                    "description": "Response time exceeds SLA"
                }
            ]
        }
    }

@pytest.fixture
def mock_llm():
    """Mock LLM for testing"""
    mock_llm = Mock()
    mock_llm.invoke.return_value = Mock(content="Mock LLM response")
    return mock_llm