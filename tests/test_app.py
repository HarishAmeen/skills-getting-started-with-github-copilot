"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


client = TestClient(app)


def test_root_redirect():
    """Test that root endpoint redirects to static/index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities():
    """Test that activities endpoint returns all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    activities = response.json()
    
    # Check that we have activities
    assert len(activities) > 0
    
    # Check that each activity has required fields
    for activity_name, details in activities.items():
        assert "description" in details
        assert "schedule" in details
        assert "max_participants" in details
        assert "participants" in details
        assert isinstance(details["participants"], list)


def test_get_activities_content():
    """Test that activities contain expected data"""
    response = client.get("/activities")
    activities = response.json()
    
    # Verify specific activities exist
    assert "Basketball" in activities
    assert "Tennis Club" in activities
    assert "Art Studio" in activities
    
    # Verify Basketball activity data
    basketball = activities["Basketball"]
    assert basketball["description"] == "Learn basketball skills and compete in friendly games"
    assert basketball["max_participants"] == 15
    assert "alex@mergington.edu" in basketball["participants"]


def test_signup_new_participant():
    """Test signing up a new participant for an activity"""
    response = client.post(
        "/activities/Chess Club/signup?email=newstudent@mergington.edu"
    )
    assert response.status_code == 200
    result = response.json()
    assert "message" in result
    assert "newstudent@mergington.edu" in result["message"]
    assert "Chess Club" in result["message"]


def test_signup_already_registered():
    """Test that already registered students can't sign up again"""
    # First signup
    client.post("/activities/Drama Club/signup?email=test@mergington.edu")
    
    # Try to signup again - should fail
    response = client.post(
        "/activities/Drama Club/signup?email=test@mergington.edu"
    )
    assert response.status_code == 400
    result = response.json()
    assert "already signed up" in result["detail"]


def test_signup_nonexistent_activity():
    """Test that signup to non-existent activity fails"""
    response = client.post(
        "/activities/Nonexistent/signup?email=student@mergington.edu"
    )
    assert response.status_code == 404
    result = response.json()
    assert "not found" in result["detail"]


def test_verify_signup_persistence():
    """Test that signup persists when fetching activities"""
    email = "verify@mergington.edu"
    activity = "Science Club"
    
    # Signup
    client.post(f"/activities/{activity}/signup?email={email}")
    
    # Fetch activities and verify signup
    response = client.get("/activities")
    activities = response.json()
    assert email in activities[activity]["participants"]


def test_remove_participant():
    """Test removing a participant from an activity"""
    email = "remove@mergington.edu"
    activity = "Programming Class"
    
    # First signup
    client.post(f"/activities/{activity}/signup?email={email}")
    
    # Verify they're registered
    response = client.get("/activities")
    activities = response.json()
    assert email in activities[activity]["participants"]
    original_count = len(activities[activity]["participants"])
    
    # Remove participant
    response = client.delete(f"/activities/{activity}/participants/{email}")
    assert response.status_code == 200
    result = response.json()
    assert "message" in result
    assert email in result["message"]
    
    # Verify they're removed
    response = client.get("/activities")
    activities = response.json()
    assert email not in activities[activity]["participants"]
    assert len(activities[activity]["participants"]) == original_count - 1


def test_remove_nonexistent_participant():
    """Test that removing non-existent participant fails"""
    response = client.delete(
        "/activities/Tennis Club/participants/notregistered@mergington.edu"
    )
    assert response.status_code == 400
    result = response.json()
    assert "not signed up" in result["detail"]


def test_remove_from_nonexistent_activity():
    """Test that removing from non-existent activity fails"""
    response = client.delete(
        "/activities/Nonexistent/participants/student@mergington.edu"
    )
    assert response.status_code == 404
    result = response.json()
    assert "not found" in result["detail"]


def test_activity_availability():
    """Test that activity availability is correctly calculated"""
    response = client.get("/activities")
    activities = response.json()
    
    gym_class = activities["Gym Class"]
    current_participants = len(gym_class["participants"])
    expected_spots_left = gym_class["max_participants"] - current_participants
    
    # Backend calculation
    assert gym_class["max_participants"] == 30
    assert current_participants <= gym_class["max_participants"]
    assert expected_spots_left >= 0


def test_signup_and_remove_flow():
    """Test complete flow of signup and removal"""
    email = "flow@mergington.edu"
    activity = "Debate Team"
    
    # Get initial state
    response = client.get("/activities")
    initial_count = len(response.json()[activity]["participants"])
    
    # Signup
    response = client.post(f"/activities/{activity}/signup?email={email}")
    assert response.status_code == 200
    
    # Verify count increased
    response = client.get("/activities")
    current_count = len(response.json()[activity]["participants"])
    assert current_count == initial_count + 1
    
    # Remove
    response = client.delete(f"/activities/{activity}/participants/{email}")
    assert response.status_code == 200
    
    # Verify count decreased
    response = client.get("/activities")
    final_count = len(response.json()[activity]["participants"])
    assert final_count == initial_count
