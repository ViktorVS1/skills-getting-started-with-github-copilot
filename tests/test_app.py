"""
FastAPI Tests for Mergington High School Activity Management System

Tests are structured using the AAA (Arrange-Act-Assert) pattern:
- Arrange: Set up test data and initial state
- Act: Perform the operation being tested
- Assert: Verify the response and state changes
"""

import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities as app_activities


# Store the original activities state before any tests run
ORIGINAL_ACTIVITIES = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
}


@pytest.fixture(autouse=False)
def client():
    """
    Fixture that provides a TestClient with a fresh copy of activities.
    This ensures test isolation by deep-copying the activities dict before each test.
    """
    # Create a fresh copy of activities for this test
    fresh_activities = copy.deepcopy(ORIGINAL_ACTIVITIES)
    
    # Clear and reset the app_activities dict with fresh data
    app_activities.clear()
    app_activities.update(fresh_activities)
    
    # Create and return test client
    client_instance = TestClient(app)
    yield client_instance
    
    # Cleanup: Reset activities to original state
    app_activities.clear()
    app_activities.update(copy.deepcopy(ORIGINAL_ACTIVITIES))


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """
        Test that GET /activities returns all activities with correct structure.
        
        Arrange: No setup needed for this test
        Act: GET /activities
        Assert: Response status 200 and all activities are returned
        """
        # Arrange
        # (Test fixture already provides a fresh app state)
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        activities_list = response.json()
        assert isinstance(activities_list, dict)
        assert "Chess Club" in activities_list
        assert "Programming Class" in activities_list
        assert "Gym Class" in activities_list
    
    def test_get_activities_has_correct_structure(self, client):
        """
        Test that each activity in the response has the required fields.
        
        Arrange: No setup needed
        Act: GET /activities
        Assert: Each activity has description, schedule, max_participants, and participants
        """
        # Arrange
        # (Test fixture already provides a fresh app state)
        
        # Act
        response = client.get("/activities")
        activities_list = response.json()
        
        # Assert
        for activity_name, activity_data in activities_list.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_successful_adds_participant(self, client):
        """
        Test that a valid signup adds the participant to the activity.
        
        Arrange: Prepare email and activity name
        Act: POST /activities/{activity_name}/signup
        Assert: Status 200, participant is added to the activity
        """
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
        
        # Verify the participant was actually added
        activities_response = client.get("/activities")
        updated_activity = activities_response.json()[activity_name]
        assert email in updated_activity["participants"]
    
    def test_signup_duplicate_rejected(self, client):
        """
        Test that a duplicate signup is rejected with appropriate error.
        
        Arrange: Student already signed up for an activity
        Act: Try to sign up the same student again for the same activity
        Assert: Status 400 with "already signed up" message
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already in Chess Club participants
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()
    
    def test_signup_nonexistent_activity_returns_404(self, client):
        """
        Test that signing up for a non-existent activity returns 404.
        
        Arrange: Activity name that does not exist
        Act: POST /activities/{nonexistent_activity}/signup
        Assert: Status 404 with "Activity not found" message
        """
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_signup_with_special_characters_in_activity_name(self, client):
        """
        Test that activity names with special characters are properly encoded.
        
        Arrange: Activity name that may need URL encoding
        Act: POST with properly encoded activity name
        Assert: Status 404 for non-existent activity (but not 422 encoding error)
        """
        # Arrange
        activity_name = "Non/Existent"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_successful_removes_participant(self, client):
        """
        Test that unregistering removes a participant from an activity.
        
        Arrange: Identify a participant already in an activity
        Act: DELETE /activities/{activity_name}/unregister
        Assert: Status 200, participant is removed from the activity
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already in participants
        
        # Verify participant is in the activity before
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity_name]["participants"]
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
        
        # Verify the participant was actually removed
        activities_response = client.get("/activities")
        assert email not in activities_response.json()[activity_name]["participants"]
    
    def test_unregister_nonexistent_participant_returns_404(self, client):
        """
        Test that unregistering a non-existent participant returns 404.
        
        Arrange: Email that is not in the activity's participants list
        Act: DELETE /activities/{activity_name}/unregister with non-existent email
        Assert: Status 404 with "Participant not found" message
        """
        # Arrange
        activity_name = "Chess Club"
        email = "nonexistent@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_unregister_nonexistent_activity_returns_404(self, client):
        """
        Test that unregistering from a non-existent activity returns 404.
        
        Arrange: Activity name that does not exist
        Act: DELETE /activities/{nonexistent_activity}/unregister
        Assert: Status 404 with "Activity not found" message
        """
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_unregister_same_participant_twice_fails_second_time(self, client):
        """
        Test that unregistering the same participant twice fails on the second attempt.
        
        Arrange: Unregister a participant successfully
        Act: Try to unregister the same participant again
        Assert: First attempt succeeds (200), second attempt fails (404)
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act - First unregister (should succeed)
        response1 = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert - First unregister succeeds
        assert response1.status_code == 200
        
        # Act - Second unregister (should fail)
        response2 = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert - Second unregister fails
        assert response2.status_code == 404


class TestRootRedirect:
    """Tests for GET / endpoint"""
    
    def test_root_redirects_to_index(self, client):
        """
        Test that GET / redirects to /static/index.html.
        
        Arrange: No setup needed
        Act: GET /
        Assert: Response is a redirect (307) to /static/index.html
        """
        # Arrange
        # (Test fixture already provides a fresh app state)
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestDataConsistency:
    """Integration tests for data consistency across operations"""
    
    def test_participant_count_updates_after_signup(self, client):
        """
        Test that participant count is correctly updated after signup.
        
        Arrange: Record initial participant count for an activity
        Act: Sign up a new participant
        Assert: Participant count increases by 1
        """
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity_name]["participants"])
        
        # Act
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        updated_response = client.get("/activities")
        updated_count = len(updated_response.json()[activity_name]["participants"])
        assert updated_count == initial_count + 1
    
    def test_participant_count_updates_after_unregister(self, client):
        """
        Test that participant count is correctly updated after unregister.
        
        Arrange: Record initial participant count for an activity
        Act: Unregister an existing participant
        Assert: Participant count decreases by 1
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity_name]["participants"])
        
        # Act
        client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        updated_response = client.get("/activities")
        updated_count = len(updated_response.json()[activity_name]["participants"])
        assert updated_count == initial_count - 1
    
    def test_multiple_signups_and_unregistrations(self, client):
        """
        Test that multiple signups and unregistrations maintain data consistency.
        
        Arrange: Multiple students and activities ready
        Act: Perform multiple signup and unregister operations
        Assert: Final state is consistent with operations performed
        """
        # Arrange
        activity = "Programming Class"
        student1 = "alice@mergington.edu"
        student2 = "bob@mergington.edu"
        student3 = "charlie@mergington.edu"
        
        # Act & Assert - Sign up multiple students
        response1 = client.post(f"/activities/{activity}/signup", params={"email": student1})
        assert response1.status_code == 200
        
        response2 = client.post(f"/activities/{activity}/signup", params={"email": student2})
        assert response2.status_code == 200
        
        response3 = client.post(f"/activities/{activity}/signup", params={"email": student3})
        assert response3.status_code == 200
        
        # Verify all 3 are signed up
        get_response = client.get("/activities")
        participants = get_response.json()[activity]["participants"]
        assert student1 in participants
        assert student2 in participants
        assert student3 in participants
        
        # Act & Assert - Unregister one student
        unregister_response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": student2}
        )
        assert unregister_response.status_code == 200
        
        # Verify student2 is removed but others remain
        get_response = client.get("/activities")
        participants = get_response.json()[activity]["participants"]
        assert student1 in participants
        assert student2 not in participants
        assert student3 in participants
