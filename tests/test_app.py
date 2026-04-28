import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def setup_activities(monkeypatch):
    """Reset activities to a known state before each test"""
    test_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu"]
        }
    }
    
    activities.clear()
    activities.update(test_activities)
    yield
    
    # Cleanup
    activities.clear()
    activities.update(test_activities)


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_success(self, client, setup_activities):
        """Test retrieving all activities"""
        # Arrange
        expected_activities = ["Chess Club", "Programming Class"]
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert len(data) == 2
    
    def test_get_activities_returns_activity_details(self, client, setup_activities):
        """Test that activities return all required fields"""
        # Arrange
        expected_description = "Learn strategies and compete in chess tournaments"
        expected_schedule = "Fridays, 3:30 PM - 5:00 PM"
        expected_max_participants = 12
        
        # Act
        response = client.get("/activities")
        activity = response.json()["Chess Club"]
        
        # Assert
        assert activity["description"] == expected_description
        assert activity["schedule"] == expected_schedule
        assert activity["max_participants"] == expected_max_participants
        assert activity["participants"] == ["michael@mergington.edu"]


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client, setup_activities):
        """Test successful signup for an activity"""
        # Arrange
        activity_name = "Chess Club"
        new_email = "john@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={new_email}"
        )
        
        # Assert
        assert response.status_code == 200
        assert f"Signed up {new_email} for {activity_name}" in response.json()["message"]
        assert new_email in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == initial_count + 1
    
    def test_signup_nonexistent_activity(self, client, setup_activities):
        """Test signup for an activity that doesn't exist"""
        # Arrange
        nonexistent_activity = "Nonexistent Club"
        student_email = "john@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{nonexistent_activity}/signup?email={student_email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_signup_duplicate_email(self, client, setup_activities):
        """Test that a student cannot sign up twice for the same activity"""
        # Arrange
        activity_name = "Chess Club"
        duplicate_email = "michael@mergington.edu"  # Already signed up
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={duplicate_email}"
        )
        
        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"
    
    def test_signup_multiple_students(self, client, setup_activities):
        """Test multiple students signing up for the same activity"""
        # Arrange
        activity_name = "Chess Club"
        new_students = ["alice@mergington.edu", "bob@mergington.edu"]
        initial_participants = len(activities[activity_name]["participants"])
        
        # Act
        for email in new_students:
            client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Assert
        participants = activities[activity_name]["participants"]
        assert "alice@mergington.edu" in participants
        assert "bob@mergington.edu" in participants
        assert len(participants) == initial_participants + len(new_students)


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self, client, setup_activities):
        """Test successful unregistration from an activity"""
        # Arrange
        activity_name = "Chess Club"
        email_to_remove = "michael@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email_to_remove}"
        )
        
        # Assert
        assert response.status_code == 200
        assert f"Unregistered {email_to_remove} from {activity_name}" in response.json()["message"]
        assert email_to_remove not in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == initial_count - 1
    
    def test_unregister_nonexistent_activity(self, client, setup_activities):
        """Test unregistering from an activity that doesn't exist"""
        # Arrange
        nonexistent_activity = "Nonexistent Club"
        student_email = "michael@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{nonexistent_activity}/unregister?email={student_email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_unregister_nonexistent_participant(self, client, setup_activities):
        """Test unregistering a participant who is not signed up"""
        # Arrange
        activity_name = "Chess Club"
        non_participant_email = "john@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={non_participant_email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Participant not found in activity"
    
    def test_unregister_then_signup_again(self, client, setup_activities):
        """Test that a student can sign up again after unregistering"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act - Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        # Assert - Unregister succeeded
        assert unregister_response.status_code == 200
        assert email not in activities[activity_name]["participants"]
        
        # Act - Sign up again
        signup_response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert - Sign up succeeded
        assert signup_response.status_code == 200
        assert email in activities[activity_name]["participants"]


class TestIntegration:
    """Integration tests combining multiple endpoints"""
    
    def test_signup_and_view_in_activities_list(self, client, setup_activities):
        """Test that newly signed up participant appears in activities list"""
        # Arrange
        activity_name = "Chess Club"
        new_email = "test@mergington.edu"
        
        # Act
        client.post(f"/activities/{activity_name}/signup?email={new_email}")
        response = client.get("/activities")
        
        # Assert
        participants = response.json()[activity_name]["participants"]
        assert new_email in participants
    
    def test_full_workflow(self, client, setup_activities):
        """Test complete workflow: signup, view, unregister, view"""
        # Arrange
        activity_name = "Programming Class"
        new_email = "workflow@mergington.edu"
        
        # Act - Step 1: User signs up
        signup_response = client.post(
            f"/activities/{activity_name}/signup?email={new_email}"
        )
        
        # Assert - Step 1: Signup succeeded
        assert signup_response.status_code == 200
        
        # Act - Step 2: Get activities to verify participation
        get_response = client.get("/activities")
        
        # Assert - Step 2: User appears in list
        assert new_email in get_response.json()[activity_name]["participants"]
        
        # Act - Step 3: User unregisters
        unregister_response = client.delete(
            f"/activities/{activity_name}/unregister?email={new_email}"
        )
        
        # Assert - Step 3: Unregister succeeded
        assert unregister_response.status_code == 200
        
        # Act - Step 4: Get activities to verify removal
        final_response = client.get("/activities")
        
        # Assert - Step 4: User no longer in list
        assert new_email not in final_response.json()[activity_name]["participants"]
