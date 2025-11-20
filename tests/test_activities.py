import pytest
from fastapi import HTTPException


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities(self, client, reset_activities):
        """Test that all activities are returned"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) == 9
        assert "Chess Club" in activities
        assert "Programming Class" in activities
    
    def test_activity_structure(self, client, reset_activities):
        """Test that activity objects have the correct structure"""
        response = client.get("/activities")
        activities = response.json()
        
        activity = activities["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)
    
    def test_activity_participants(self, client, reset_activities):
        """Test that initial participants are correct"""
        response = client.get("/activities")
        activities = response.json()
        
        chess_club = activities["Chess Club"]
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client, reset_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newestudent@mergington.edu"
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "message" in result
        assert "newestudent@mergington.edu" in result["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "newestudent@mergington.edu" in activities["Chess Club"]["participants"]
    
    def test_signup_nonexistent_activity(self, client, reset_activities):
        """Test signup for activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_duplicate_email(self, client, reset_activities):
        """Test that duplicate signups are rejected"""
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_at_capacity(self, client, reset_activities):
        """Test that signup is rejected when activity is at capacity"""
        from app import activities
        
        # Set participants to max capacity
        activities["Chess Club"]["participants"] = [
            f"student{i}@mergington.edu" for i in range(12)
        ]
        
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 400
        assert "Activity is full" in response.json()["detail"]


class TestUnregisterFromActivity:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self, client, reset_activities):
        """Test successful unregistration from an activity"""
        response = client.post(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "message" in result
        assert "michael@mergington.edu" in result["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_activity(self, client, reset_activities):
        """Test unregister from activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Club/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_not_registered(self, client, reset_activities):
        """Test that unregistering a non-registered student is rejected"""
        response = client.post(
            "/activities/Chess Club/unregister?email=notstudent@mergington.edu"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]
    
    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister actually removes the participant"""
        # First verify the participant exists
        response = client.get("/activities")
        initial_activities = response.json()
        initial_count = len(initial_activities["Chess Club"]["participants"])
        
        # Unregister
        client.post(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        
        # Verify count decreased
        response = client.get("/activities")
        updated_activities = response.json()
        assert len(updated_activities["Chess Club"]["participants"]) == initial_count - 1


class TestIntegration:
    """Integration tests combining multiple endpoints"""
    
    def test_signup_and_unregister_flow(self, client, reset_activities):
        """Test the full flow of signing up and then unregistering"""
        email = "testuser@mergington.edu"
        activity = "Math Club"
        
        # Signup
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Verify signup
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity]["participants"]
        
        # Unregister
        unregister_response = client.post(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert unregister_response.status_code == 200
        
        # Verify unregister
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities[activity]["participants"]
    
    def test_multiple_signups(self, client, reset_activities):
        """Test signing up multiple users for the same activity"""
        activity = "Programming Class"
        emails = ["user1@mergington.edu", "user2@mergington.edu", "user3@mergington.edu"]
        
        # Sign up all users
        for email in emails:
            response = client.post(
                f"/activities/{activity}/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Verify all are registered
        activities_response = client.get("/activities")
        activities = activities_response.json()
        participants = activities[activity]["participants"]
        
        for email in emails:
            assert email in participants
