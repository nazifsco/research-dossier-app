"""
Payment endpoints: create checkout, webhook handler, payment history.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
import stripe

from app.database import get_db
from app.models.user import User
from app.models.payment import Payment
from app.core.deps import get_current_active_user
from app.config import get_settings
from app.services.email import send_credit_purchase_email

router = APIRouter()
settings = get_settings()

# Initialize Stripe
if settings.stripe_secret_key:
    stripe.api_key = settings.stripe_secret_key


# Pricing tiers (Option A - Growth-focused)
PRICING_TIERS = {
    "starter": {"credits": 1, "amount_cents": 500, "name": "Starter"},
    "standard": {"credits": 5, "amount_cents": 2000, "name": "Standard Pack"},
    "pro": {"credits": 20, "amount_cents": 6000, "name": "Pro Pack"},
    "business": {"credits": 50, "amount_cents": 10000, "name": "Business Pack"},
}


# Request/Response schemas
class CreateCheckoutRequest(BaseModel):
    tier: str  # 'single', 'starter', 'pro'


class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str


class PaymentHistoryResponse(BaseModel):
    id: str
    amount_cents: int
    credits_purchased: int
    status: str
    created_at: str

    class Config:
        from_attributes = True


@router.post("/create-checkout", response_model=CheckoutResponse)
async def create_checkout(
    request: CreateCheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a Stripe checkout session for purchasing credits.
    """
    if not settings.stripe_secret_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment processing not configured"
        )

    tier = PRICING_TIERS.get(request.tier)
    if not tier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tier. Choose from: {', '.join(PRICING_TIERS.keys())}"
        )

    try:
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": tier["name"],
                        "description": f"{tier['credits']} research credit{'s' if tier['credits'] > 1 else ''}"
                    },
                    "unit_amount": tier["amount_cents"]
                },
                "quantity": 1
            }],
            mode="payment",
            success_url=f"{settings.frontend_url}/credits/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.frontend_url}/credits?canceled=true",
            client_reference_id=current_user.id,
            metadata={
                "user_id": current_user.id,
                "tier": request.tier,
                "credits": str(tier["credits"])
            }
        )

        # Create pending payment record
        payment = Payment(
            user_id=current_user.id,
            stripe_checkout_id=checkout_session.id,
            amount_cents=tier["amount_cents"],
            credits_purchased=tier["credits"],
            status="pending"
        )
        db.add(payment)
        db.commit()

        return CheckoutResponse(
            checkout_url=checkout_session.url,
            session_id=checkout_session.id
        )

    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment error: {str(e)}"
        )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"),
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhooks for payment completion.
    """
    if not settings.stripe_secret_key or not settings.stripe_webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook not configured"
        )

    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload,
            stripe_signature,
            settings.stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle checkout.session.completed
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        # Find payment record
        payment = db.query(Payment).filter(
            Payment.stripe_checkout_id == session["id"]
        ).first()

        if payment and payment.status == "pending":
            # Update payment
            payment.status = "completed"
            payment.stripe_payment_id = session.get("payment_intent")
            payment.completed_at = datetime.utcnow()

            # Add credits to user
            user = db.query(User).filter(User.id == payment.user_id).first()
            if user:
                user.credits += payment.credits_purchased

                # Set Stripe customer ID if not set
                if not user.stripe_customer_id and session.get("customer"):
                    user.stripe_customer_id = session["customer"]

            db.commit()

            # Send purchase confirmation email (fire and forget)
            if user:
                try:
                    await send_credit_purchase_email(
                        to=user.email,
                        name=user.name,
                        credits_purchased=payment.credits_purchased,
                        amount_dollars=payment.amount_cents / 100,
                        new_balance=user.credits
                    )
                except Exception as e:
                    print(f"Failed to send purchase confirmation email: {e}")

    return {"status": "success"}


@router.get("/history")
async def get_payment_history(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get user's payment history.
    """
    payments = db.query(Payment).filter(
        Payment.user_id == current_user.id
    ).order_by(Payment.created_at.desc()).limit(limit).all()

    return {
        "payments": [
            {
                "id": p.id,
                "amount_cents": p.amount_cents,
                "credits_purchased": p.credits_purchased,
                "status": p.status,
                "created_at": p.created_at.isoformat()
            }
            for p in payments
        ]
    }


@router.get("/tiers")
async def get_pricing_tiers():
    """Get available pricing tiers."""
    return {
        "tiers": [
            {
                "id": tier_id,
                "name": tier["name"],
                "credits": tier["credits"],
                "price_cents": tier["amount_cents"],
                "price_dollars": tier["amount_cents"] / 100,
                "price_per_credit": tier["amount_cents"] / 100 / tier["credits"]
            }
            for tier_id, tier in PRICING_TIERS.items()
        ]
    }
