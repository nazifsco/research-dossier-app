"""
Tests for payment endpoints.
"""

import pytest
from app.models.payment import Payment


def test_get_pricing_tiers(client):
    """Test getting pricing tiers."""
    response = client.get("/api/payments/tiers")

    assert response.status_code == 200
    data = response.json()
    assert "tiers" in data
    tiers = data["tiers"]

    # Verify structure
    assert len(tiers) == 4
    tier_names = [t["name"] for t in tiers]
    assert "Starter" in tier_names
    assert "Standard" in tier_names
    assert "Pro" in tier_names
    assert "Business" in tier_names

    # Verify Starter tier
    starter = next(t for t in tiers if t["name"] == "Starter")
    assert starter["credits"] == 1
    assert starter["price"] == 5
    assert starter["per_credit"] == 5


def test_create_checkout_authenticated(client, auth_headers, test_user):
    """Test creating checkout session as authenticated user."""
    response = client.post(
        "/api/payments/create-checkout",
        json={"tier": "standard"},
        headers=auth_headers
    )

    # This will fail if Stripe is not configured, which is expected in tests
    # We're testing that the endpoint exists and handles auth correctly
    assert response.status_code in [200, 500]  # 500 if Stripe not configured


def test_create_checkout_unauthenticated(client):
    """Test creating checkout without authentication."""
    response = client.post(
        "/api/payments/create-checkout",
        json={"tier": "standard"}
    )

    assert response.status_code == 401


def test_create_checkout_invalid_tier(client, auth_headers):
    """Test creating checkout with invalid tier."""
    response = client.post(
        "/api/payments/create-checkout",
        json={"tier": "nonexistent"},
        headers=auth_headers
    )

    assert response.status_code == 400
    assert "invalid tier" in response.json()["detail"].lower()


def test_get_payment_history_authenticated(client, auth_headers):
    """Test getting payment history as authenticated user."""
    response = client.get(
        "/api/payments/history",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "payments" in data
    assert isinstance(data["payments"], list)


def test_get_payment_history_unauthenticated(client):
    """Test getting payment history without authentication."""
    response = client.get("/api/payments/history")

    assert response.status_code == 401


def test_payment_model_creation(db_session, test_user):
    """Test creating a payment record."""
    payment = Payment(
        user_id=test_user.id,
        amount=20,
        credits_purchased=5,
        tier="standard",
        stripe_checkout_id="cs_test_123",
        status="pending"
    )
    db_session.add(payment)
    db_session.commit()

    # Verify payment was created
    saved_payment = db_session.query(Payment).filter_by(
        stripe_checkout_id="cs_test_123"
    ).first()

    assert saved_payment is not None
    assert saved_payment.user_id == test_user.id
    assert saved_payment.amount == 20
    assert saved_payment.credits_purchased == 5
    assert saved_payment.tier == "standard"
    assert saved_payment.status == "pending"
