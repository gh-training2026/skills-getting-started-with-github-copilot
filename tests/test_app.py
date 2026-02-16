import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    from app import activities
    
    initial_activities = {
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
    
    activities.clear()
    activities.update(initial_activities)
    yield
    # Cleanup
    activities.clear()
    activities.update(initial_activities)


class TestGetActivities:
    def test_get_activities_returns_all_activities(self, reset_activities):
        """Test that /activities endpoint returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_get_activities_returns_activity_details(self, reset_activities):
        """Test that activity details are complete"""
        response = client.get("/activities")
        data = response.json()
        chess_club = data["Chess Club"]
        
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club


class TestSignupForActivity:
    def test_signup_for_activity_success(self, reset_activities):
        """Test successful activity signup"""
        response = client.post(
            "/activities/Chess Club/signup?email=john@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up john@mergington.edu for Chess Club" in data["message"]

    def test_signup_for_nonexistent_activity(self, reset_activities):
        """Test signup for activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=john@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_duplicate_student_prevented(self, reset_activities):
        """Test that duplicate signups are prevented"""
        # First signup should succeed
        response1 = client.post(
            "/activities/Chess Club/signup?email=test@mergington.edu"
        )
        assert response1.status_code == 200

        # Second signup with same email should fail
        response2 = client.post(
            "/activities/Chess Club/signup?email=test@mergington.edu"
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"]

    def test_signup_student_already_enrolled(self, reset_activities):
        """Test that already enrolled students can't signup again"""
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_updates_participant_list(self, reset_activities):
        """Test that participant list is updated after signup"""
        email = "newstudent@mergington.edu"
        
        # Check initial state
        response = client.get("/activities")
        initial_count = len(response.json()["Chess Club"]["participants"])

        # Sign up new student
        client.post(f"/activities/Chess Club/signup?email={email}")

        # Check updated state
        response = client.get("/activities")
        updated_count = len(response.json()["Chess Club"]["participants"])
        
        assert updated_count == initial_count + 1
        assert email in response.json()["Chess Club"]["participants"]


class TestRoot:
    def test_root_redirects_to_index(self):
        """Test that root path redirects to index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
