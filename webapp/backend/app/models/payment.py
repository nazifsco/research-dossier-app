"""Payment model."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Payment(Base):
    """Payment model - tracks Stripe payments and credit purchases."""

    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    # Stripe details
    stripe_payment_id = Column(String(255), nullable=True)
    stripe_checkout_id = Column(String(255), nullable=True)

    # Payment details
    amount_cents = Column(Integer, nullable=False)
    credits_purchased = Column(Integer, nullable=False)
    currency = Column(String(10), default="usd", nullable=False)

    # Status
    status = Column(String(50), default="pending", nullable=False)
    # Statuses: pending, completed, failed, refunded

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="payments")

    def __repr__(self):
        return f"<Payment {self.id} - ${self.amount_cents/100:.2f} ({self.status})>"
