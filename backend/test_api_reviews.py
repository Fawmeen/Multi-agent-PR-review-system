import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)

@pytest.fixture
def mock_review_repo():
    with patch("app.api.reviews.ReviewRepository") as mock:
        yield mock

@pytest.fixture
def mock_finding_repo():
    with patch("app.api.reviews.FindingRepository") as mock:
        yield mock

@pytest.fixture
def mock_event_repo():
    with patch("app.api.reviews.EventRepository") as mock:
        yield mock

def test_list_reviews(mock_review_repo):
    # Setup mock
    repo_instance = mock_review_repo.return_value
    repo_instance.list_reviews = AsyncMock(return_value=[{"id": "r1"}, {"id": "r2"}])
    
    response = client.get("/reviews/")
    assert response.status_code == 200
    assert "reviews" in response.json()
    assert len(response.json()["reviews"]) == 2

def test_get_review_details(mock_review_repo, mock_finding_repo, mock_event_repo):
    # Setup mocks
    review_instance = mock_review_repo.return_value
    review_instance.get_by_id = AsyncMock(return_value={"id": "r1"})
    
    finding_instance = mock_finding_repo.return_value
    finding_instance.get_findings_by_review_id = AsyncMock(return_value=[{"id": "f1"}])
    
    event_instance = mock_event_repo.return_value
    event_instance.get_events_by_review_id = AsyncMock(return_value=[{"event_type": "llm"}])
    
    response = client.get("/reviews/r1")
    assert response.status_code == 200
    data = response.json()
    assert data["review"]["id"] == "r1"
    assert data["findings"][0]["id"] == "f1"
    assert data["events"][0]["event_type"] == "llm"

def test_get_review_not_found(mock_review_repo, mock_finding_repo, mock_event_repo):
    review_instance = mock_review_repo.return_value
    review_instance.get_by_id = AsyncMock(return_value=None)
    
    response = client.get("/reviews/r1")
    assert response.status_code == 404
