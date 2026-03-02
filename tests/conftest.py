"""
Pytest configuration and fixtures for FastAPI tests.

This module provides fixtures using the Arrange-Act-Assert pattern:
- Fixtures handle the Arrange phase (setup test data)
- Tests handle the Act phase (execute the operation)
- Tests handle the Assert phase (verify the results)
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """
    Fixture: Provide a TestClient instance for testing FastAPI endpoints.
    
    Arrange phase: Create test client without running a server.
    """
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """
    Fixture: Reset activities to a clean state before each test.
    
    Arrange phase: Initialize fresh test data.
    Cleanup phase: Reset after test completes.
    """
    # Store original state
    original_activities = {
        name: {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": details["participants"].copy()
        }
        for name, details in activities.items()
    }
    
    yield
    
    # Cleanup: Reset to original state after test
    activities.clear()
    activities.update(original_activities)


@pytest.fixture
def clean_activities(reset_activities):
    """
    Fixture: Provide clean activities with minimal test data.
    
    Arrange phase: Set up simplified activities for focused testing.
    """
    # Clear existing activities
    activities.clear()
    
    # Add minimal test data
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 2,
            "participants": ["alice@test.edu"]
        },
        "Programming": {
            "description": "Learn programming fundamentals",
            "schedule": "Tuesdays and Thursdays",
            "max_participants": 3,
            "participants": []
        }
    })
    
    return activities
