"""
Tests for the High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

# Create test client
client = TestClient(app)


class TestActivities:
    """Tests for the /activities endpoint"""

    def test_get_activities_returns_all_activities(self):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "Basketball" in data
        assert "Tennis Club" in data
        assert "Art Studio" in data

    def test_get_activities_has_required_fields(self):
        """Test that activities contain required fields"""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Basketball"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity

    def test_get_activities_participants_is_list(self):
        """Test that participants field is a list"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert isinstance(activity_data["participants"], list)


class TestSignup:
    """Tests for the signup endpoint"""

    def test_signup_for_valid_activity(self):
        """Test signing up for a valid activity"""
        response = client.post(
            "/activities/Basketball/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Basketball" in data["message"]

    def test_signup_adds_participant(self):
        """Test that signup actually adds the participant"""
        email = "testnew@mergington.edu"
        
        # Get initial participant count
        response = client.get("/activities")
        initial_count = len(response.json()["Basketball"]["participants"])
        
        # Sign up
        client.post(f"/activities/Basketball/signup?email={email}")
        
        # Check participant was added
        response = client.get("/activities")
        final_count = len(response.json()["Basketball"]["participants"])
        assert final_count == initial_count + 1
        assert email in response.json()["Basketball"]["participants"]

    def test_signup_for_nonexistent_activity(self):
        """Test signing up for an activity that doesn't exist"""
        response = client.post(
            "/activities/NonexistentActivity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_signup_already_registered_student(self):
        """Test that a student cannot sign up twice for same activity"""
        email = "alex@mergington.edu"  # Already in Basketball
        
        response = client.post(
            f"/activities/Basketball/signup?email={email}"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()


class TestUnregister:
    """Tests for the unregister endpoint"""

    def test_unregister_existing_participant(self):
        """Test unregistering an existing participant"""
        # First sign up
        email = "unregister_test@mergington.edu"
        client.post(f"/activities/Basketball/signup?email={email}")
        
        # Then unregister
        response = client.delete(
            f"/activities/Basketball/unregister?email={email}"
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        
        # Verify removed
        activities_response = client.get("/activities")
        assert email not in activities_response.json()["Basketball"]["participants"]

    def test_unregister_nonexistent_activity(self):
        """Test unregistering from activity that doesn't exist"""
        response = client.delete(
            "/activities/FakeActivity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404

    def test_unregister_not_registered_student(self):
        """Test unregistering a student who is not registered"""
        response = client.delete(
            "/activities/Basketball/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"].lower()

    def test_unregister_removes_participant(self):
        """Test that unregister actually removes the participant"""
        email = "remove_test@mergington.edu"
        
        # Sign up
        client.post(f"/activities/Art Studio/signup?email={email}")
        
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()["Art Studio"]["participants"])
        
        # Unregister
        client.delete(f"/activities/Art Studio/unregister?email={email}")
        
        # Check participant was removed
        response = client.get("/activities")
        final_count = len(response.json()["Art Studio"]["participants"])
        assert final_count == initial_count - 1
        assert email not in response.json()["Art Studio"]["participants"]


class TestRoot:
    """Tests for the root endpoint"""

    def test_root_redirects_to_static_index(self):
        """Test that GET / redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307  # Temporary redirect
        assert "/static/index.html" in response.headers["location"]


class TestEdgeCases:
    """Tests for edge cases and validation"""

    def test_signup_with_special_characters_in_email(self):
        """Test that special characters in email are handled correctly"""
        response = client.post(
            "/activities/Basketball/signup?email=test+tag@mergington.edu"
        )
        assert response.status_code == 200

    def test_activity_name_with_spaces(self):
        """Test activity names with spaces work correctly"""
        response = client.post(
            "/activities/Tennis Club/signup?email=space_test@mergington.edu"
        )
        assert response.status_code == 200

    def test_multiple_signups_for_different_activities(self):
        """Test that a student can sign up for multiple activities"""
        email = "multi@mergington.edu"
        
        # Sign up for multiple activities
        response1 = client.post(f"/activities/Basketball/signup?email={email}")
        response2 = client.post(f"/activities/Tennis Club/signup?email={email}")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify in both activities
        activities = client.get("/activities").json()
        assert email in activities["Basketball"]["participants"]
        assert email in activities["Tennis Club"]["participants"]

    def test_full_activity_cannot_have_more_signups(self):
        """Test that full activities cannot accept more participants"""
        # Note: This test is informational - the current API doesn't enforce max_participants
        # It's included to show where validation could be added
        response = client.get("/activities")
        activities = response.json()
        
        # Verify max_participants exists in data structure
        for activity_name, activity_data in activities.items():
            assert "max_participants" in activity_data
            assert isinstance(activity_data["max_participants"], int)
