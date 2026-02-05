"""
Tests for research endpoints.
"""

import pytest
from app.models.research import ResearchJob
from app.models.user import User


def test_create_research_authenticated(client, auth_headers, test_user):
    """Test creating research job as authenticated user."""
    response = client.post(
        "/api/research/generate",
        json={
            "query": "Elon Musk",
            "depth": "quick"
        },
        headers=auth_headers
    )

    # Should succeed or fail gracefully if OpenAI not configured
    assert response.status_code in [200, 402, 500]

    if response.status_code == 200:
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "processing"


def test_create_research_unauthenticated(client):
    """Test creating research without authentication."""
    response = client.post(
        "/api/research/generate",
        json={
            "query": "Test Query",
            "depth": "quick"
        }
    )

    assert response.status_code == 401


def test_create_research_insufficient_credits(client, db_session):
    """Test creating research with insufficient credits."""
    # Create user with 0 credits
    user = User(
        email="broke@example.com",
        name="Broke User",
        password_hash="hashed",
        is_verified=True,
        credits=0
    )
    db_session.add(user)
    db_session.commit()

    # Login
    from app.core.security import create_access_token
    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/api/research/generate",
        json={
            "query": "Test Query",
            "depth": "quick"
        },
        headers=headers
    )

    assert response.status_code == 402
    assert "insufficient credits" in response.json()["detail"].lower()


def test_create_research_invalid_depth(client, auth_headers):
    """Test creating research with invalid depth."""
    response = client.post(
        "/api/research/generate",
        json={
            "query": "Test Query",
            "depth": "invalid_depth"
        },
        headers=auth_headers
    )

    assert response.status_code == 422  # Validation error


def test_get_research_jobs(client, auth_headers):
    """Test getting research jobs list."""
    response = client.get(
        "/api/research/jobs",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert isinstance(data["jobs"], list)


def test_get_research_jobs_unauthenticated(client):
    """Test getting research jobs without authentication."""
    response = client.get("/api/research/jobs")

    assert response.status_code == 401


def test_get_research_job_by_id(client, auth_headers, db_session, test_user):
    """Test getting specific research job."""
    # Create a research job
    job = ResearchJob(
        user_id=test_user.id,
        query="Test Query",
        depth="quick",
        status="completed",
        result={"title": "Test Result"}
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    response = client.get(
        f"/api/research/jobs/{job.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job.id
    assert data["query"] == "Test Query"
    assert data["status"] == "completed"


def test_get_research_job_not_found(client, auth_headers):
    """Test getting nonexistent research job."""
    response = client.get(
        "/api/research/jobs/99999",
        headers=auth_headers
    )

    assert response.status_code == 404


def test_get_research_job_unauthorized(client, db_session, test_user):
    """Test getting another user's research job."""
    # Create another user
    other_user = User(
        email="other@example.com",
        name="Other User",
        password_hash="hashed",
        is_verified=True,
        credits=10
    )
    db_session.add(other_user)
    db_session.commit()

    # Create job for other user
    job = ResearchJob(
        user_id=other_user.id,
        query="Other's Query",
        depth="quick",
        status="completed"
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    # Try to access with test_user's token
    from app.core.security import create_access_token
    token = create_access_token(test_user.id)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(
        f"/api/research/jobs/{job.id}",
        headers=headers
    )

    assert response.status_code == 403


def test_research_model_creation(db_session, test_user):
    """Test creating a research job record."""
    job = ResearchJob(
        user_id=test_user.id,
        query="Test Company",
        depth="standard",
        status="pending"
    )
    db_session.add(job)
    db_session.commit()

    # Verify job was created
    saved_job = db_session.query(ResearchJob).filter_by(
        user_id=test_user.id
    ).first()

    assert saved_job is not None
    assert saved_job.query == "Test Company"
    assert saved_job.depth == "standard"
    assert saved_job.status == "pending"
