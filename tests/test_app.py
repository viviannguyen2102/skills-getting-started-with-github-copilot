from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


ACTIVITY_NAME = "Chess Club"
ACTIVITY_PATH = "/activities/Chess%20Club/signup"


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_activities)


def test_get_activities_returns_activity_details(client):
    response = client.get("/activities")

    assert response.status_code == 200
    activity = response.json()[ACTIVITY_NAME]
    assert activity["description"]
    assert activity["schedule"]
    assert activity["max_participants"] == 12
    assert activity["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_adds_participant(client):
    email = "new-student@mergington.edu"

    response = client.post(ACTIVITY_PATH, params={"email": email})

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {ACTIVITY_NAME}"
    }
    assert email in client.get("/activities").json()[ACTIVITY_NAME]["participants"]


def test_signup_rejects_duplicate_participant(client):
    email = "michael@mergington.edu"

    response = client.post(ACTIVITY_PATH, params={"email": email})

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown%20Activity/signup",
        params={"email": "new-student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
    email = "michael@mergington.edu"

    response = client.delete(ACTIVITY_PATH, params={"email": email})

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {ACTIVITY_NAME}"
    }
    assert email not in client.get("/activities").json()[ACTIVITY_NAME]["participants"]


def test_unregister_rejects_nonparticipant(client):
    response = client.delete(
        ACTIVITY_PATH,
        params={"email": "not-signed-up@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown%20Activity/signup",
        params={"email": "michael@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
