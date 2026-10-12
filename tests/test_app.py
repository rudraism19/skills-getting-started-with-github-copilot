from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


INITIAL_ACTIVITIES = deepcopy(app_module.activities)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app_module, "activities", deepcopy(INITIAL_ACTIVITIES))
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_get_activities_returns_data_without_caching(client):
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert expected_activity in response.json()
    assert response.headers["cache-control"] == "no-store"


def test_signup_adds_participant_and_updates_activities(client):
    # Arrange
    activity_name = "Basketball Team"
    email = "student@example.test"

    # Act
    signup_response = client.post(
        f"/activities/{activity_name}/signup", params={"email": email}
    )
    activities_response = client.get("/activities")

    # Assert
    assert signup_response.status_code == 200
    assert signup_response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert email in activities_response.json()[activity_name]["participants"]


def test_duplicate_signup_returns_400_without_adding_duplicate(client):
    # Arrange
    activity_name = "Art Club"
    email = "student@example.test"
    signup_url = f"/activities/{activity_name}/signup"

    # Act
    first_response = client.post(signup_url, params={"email": email})
    duplicate_response = client.post(signup_url, params={"email": email})
    activities_response = client.get("/activities")

    # Assert
    assert first_response.status_code == 200
    assert duplicate_response.status_code == 400
    assert activities_response.json()[activity_name]["participants"].count(email) == 1


def test_signup_for_unknown_activity_returns_404(client):
    # Arrange
    activity_name = "Unknown Activity"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup", params={"email": "student@example.test"}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant_from_activity(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    unregister_response = client.delete(
        f"/activities/{activity_name}/signup", params={"email": email}
    )
    activities_response = client.get("/activities")

    # Assert
    assert unregister_response.status_code == 200
    assert unregister_response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    assert email not in activities_response.json()[activity_name]["participants"]


def test_unregister_for_absent_participant_returns_404(client):
    # Arrange
    activity_name = "Basketball Team"
    email = "student@example.test"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_from_unknown_activity_returns_404(client):
    # Arrange
    activity_name = "Unknown Activity"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup", params={"email": "student@example.test"}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"