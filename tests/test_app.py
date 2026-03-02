"""
Comprehensive FastAPI tests using the Arrange-Act-Assert (AAA) pattern.

Each test follows AAA:
- Arrange: Set up test data using fixtures
- Act: Call the endpoint
- Assert: Verify response status, data, and side effects
"""

import pytest


class TestRootEndpoint:
    """Tests for GET / endpoint"""
    
    def test_root_redirects_to_static(self, client):
        """
        Test: GET / redirects to static/index.html
        
        Arrange: Client is ready (from fixture)
        Act: Make GET request to /
        Assert: Verify 307 redirect response
        """
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_all_activities(self, client, clean_activities):
        """
        Test: GET /activities returns all activities with correct structure
        
        Arrange: Test data loaded via clean_activities fixture
        Act: Make GET request to /activities
        Assert: Verify response contains all activities with expected fields
        """
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert "Chess Club" in data
        assert "Programming" in data
        assert len(data) == 2
        
        # Verify activity structure
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)
    
    def test_get_activities_shows_current_participants(self, client, clean_activities):
        """
        Test: GET /activities includes current participants
        
        Arrange: Test data with existing participant
        Act: Make GET request to /activities
        Assert: Verify participants list contains alice@test.edu
        """
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert "alice@test.edu" in data["Chess Club"]["participants"]
        assert len(data["Chess Club"]["participants"]) == 1


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client, clean_activities):
        """
        Test: Student successfully signs up for an activity
        
        Arrange: Available activity "Programming" with no participants
        Act: Post signup for bob@test.edu
        Assert: Verify 200 response and participant added to activity
        """
        # Act
        response = client.post(
            "/activities/Programming/signup?email=bob@test.edu",
            params={"email": "bob@test.edu"}
        )
        
        # Assert
        assert response.status_code == 200
        result = response.json()
        assert "Signed up" in result["message"]
        assert "bob@test.edu" in result["message"]
        
        # Verify side effect: participant added
        activities_data = client.get("/activities").json()
        assert "bob@test.edu" in activities_data["Programming"]["participants"]
    
    def test_signup_activity_not_found(self, client, clean_activities):
        """
        Test: Signup fails when activity doesn't exist
        
        Arrange: Activity "NonExistent" doesn't exist
        Act: Post signup to non-existent activity
        Assert: Verify 404 response with appropriate error message
        """
        # Act
        response = client.post(
            "/activities/NonExistent/signup?email=bob@test.edu"
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_duplicate_registration(self, client, clean_activities):
        """
        Test: Student cannot register twice for same activity
        
        Arrange: alice@test.edu already in Chess Club participants
        Act: Attempt to signup alice@test.edu for Chess Club again
        Assert: Verify 400 response blocking duplicate signup
        """
        # Act
        response = client.post(
            "/activities/Chess Club/signup?email=alice@test.edu"
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_different_student_same_activity(self, client, clean_activities):
        """
        Test: Different students can sign up for the same activity
        
        Arrange: alice@test.edu in Chess Club, charlie@test.edu available
        Act: Sign up charlie@test.edu for Chess Club
        Assert: Verify success and both students in participants
        """
        # Act
        response = client.post(
            "/activities/Chess Club/signup?email=charlie@test.edu"
        )
        
        # Assert
        assert response.status_code == 200
        
        # Verify both participants are in the activity
        activities_data = client.get("/activities").json()
        chess_participants = activities_data["Chess Club"]["participants"]
        assert "alice@test.edu" in chess_participants
        assert "charlie@test.edu" in chess_participants
        assert len(chess_participants) == 2
    
    def test_signup_email_format(self, client, clean_activities):
        """
        Test: Signup accepts various email formats
        
        Arrange: Available activity
        Act: Sign up with valid email format
        Assert: Verify signup succeeds and email stored correctly
        """
        # Act
        from urllib.parse import quote
        email = "student.name+tag@example.edu"
        encoded_email = quote(email, safe='')
        response = client.post(
            f"/activities/Programming/signup?email={encoded_email}"
        )
        
        # Assert
        assert response.status_code == 200
        activities_data = client.get("/activities").json()
        assert email in activities_data["Programming"]["participants"]


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint"""
    
    def test_remove_participant_success(self, client, clean_activities):
        """
        Test: Successfully remove a participant from an activity
        
        Arrange: alice@test.edu in Chess Club
        Act: Delete alice@test.edu from Chess Club
        Assert: Verify 200 response and participant removed
        """
        # Arrange
        assert "alice@test.edu" in clean_activities["Chess Club"]["participants"]
        
        # Act
        response = client.delete(
            "/activities/Chess Club/participants/alice@test.edu"
        )
        
        # Assert
        assert response.status_code == 200
        result = response.json()
        assert "Removed" in result["message"]
        
        # Verify side effect: participant removed
        activities_data = client.get("/activities").json()
        assert "alice@test.edu" not in activities_data["Chess Club"]["participants"]
        assert len(activities_data["Chess Club"]["participants"]) == 0
    
    def test_remove_participant_activity_not_found(self, client, clean_activities):
        """
        Test: Remove fails when activity doesn't exist
        
        Arrange: Activity "NonExistent" doesn't exist
        Act: Delete from non-existent activity
        Assert: Verify 404 response
        """
        # Act
        response = client.delete(
            "/activities/NonExistent/participants/alice@test.edu"
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_remove_participant_not_registered(self, client, clean_activities):
        """
        Test: Remove fails when participant is not in activity
        
        Arrange: unregistered@test.edu not in Programming participants
        Act: Try to remove unregistered@test.edu from Programming
        Assert: Verify 404 response for participant not found
        """
        # Act
        response = client.delete(
            "/activities/Programming/participants/unregistered@test.edu"
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_remove_first_participant(self, client, clean_activities):
        """
        Test: Activity becomes empty after removing only participant
        
        Arrange: Chess Club has alice@test.edu as only participant
        Act: Remove alice@test.edu
        Assert: Verify Chess Club has zero participants
        """
        # Arrange
        assert len(clean_activities["Chess Club"]["participants"]) == 1
        
        # Act
        response = client.delete(
            "/activities/Chess Club/participants/alice@test.edu"
        )
        
        # Assert
        assert response.status_code == 200
        activities_data = client.get("/activities").json()
        assert len(activities_data["Chess Club"]["participants"]) == 0
    
    def test_remove_one_of_many_participants(self, client, clean_activities):
        """
        Test: Remove one participant without affecting others
        
        Arrange: Add additional participant to Chess Club
        Act: Sign up bob@test.edu, then remove alice@test.edu
        Assert: Verify bob@test.edu remains, alice@test.edu removed
        """
        # Arrange
        client.post("/activities/Chess Club/signup?email=bob@test.edu")
        activities_data = client.get("/activities").json()
        assert len(activities_data["Chess Club"]["participants"]) == 2
        
        # Act
        response = client.delete(
            "/activities/Chess Club/participants/alice@test.edu"
        )
        
        # Assert
        assert response.status_code == 200
        activities_data = client.get("/activities").json()
        assert len(activities_data["Chess Club"]["participants"]) == 1
        assert "bob@test.edu" in activities_data["Chess Club"]["participants"]
        assert "alice@test.edu" not in activities_data["Chess Club"]["participants"]


class TestIntegration:
    """Integration tests combining multiple operations"""
    
    def test_signup_and_remove_workflow(self, client, clean_activities):
        """
        Test: Complete signup and removal workflow
        
        Arrange: Fresh activities
        Act: Sign up student, verify in list, remove student, verify removed
        Assert: Data consistency throughout workflow
        """
        # Act & Assert: Signup
        signup_response = client.post(
            "/activities/Programming/signup?email=test@test.edu"
        )
        assert signup_response.status_code == 200
        
        # Act & Assert: Verify signup
        activities_data = client.get("/activities").json()
        assert "test@test.edu" in activities_data["Programming"]["participants"]
        
        # Act & Assert: Remove
        remove_response = client.delete(
            "/activities/Programming/participants/test@test.edu"
        )
        assert remove_response.status_code == 200
        
        # Act & Assert: Verify removal
        activities_data = client.get("/activities").json()
        assert "test@test.edu" not in activities_data["Programming"]["participants"]
    
    def test_multiple_signups_same_activity(self, client, clean_activities):
        """
        Test: Multiple students can sign up for same activity
        
        Arrange: Programming activity with 3 max participants
        Act: Sign up 3 different students
        Assert: All 3 students registered successfully
        """
        # Act & Assert
        emails = ["student1@test.edu", "student2@test.edu", "student3@test.edu"]
        
        for email in emails:
            response = client.post(
                f"/activities/Programming/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Verify all students are registered
        activities_data = client.get("/activities").json()
        for email in emails:
            assert email in activities_data["Programming"]["participants"]
        assert len(activities_data["Programming"]["participants"]) == 3
