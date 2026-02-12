import pytest


@pytest.fixture()
def sample_requirements() -> str:
    return "User login, data validation, performance, and security checks."


@pytest.fixture()
def sample_test_results() -> dict:
    return {
        "tests_run": 10,
        "passed": 8,
        "failed": 2,
        "severity": "high",
        "category": "security",
        "description": "Sample finding"
    }
