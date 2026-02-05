"""Research job model."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class ResearchJob(Base):
    """Research job model - tracks research requests and their status."""

    __tablename__ = "research_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    # Research parameters
    target = Column(String(500), nullable=False)
    target_type = Column(String(50), nullable=False)  # 'company' | 'person'
    depth = Column(String(50), default="standard", nullable=False)  # 'quick' | 'standard' | 'deep'

    # Status tracking
    status = Column(String(50), default="pending", nullable=False, index=True)
    # Statuses: pending, processing, completed, failed

    # Results
    credits_used = Column(Integer, default=0, nullable=False)
    report_path = Column(String(500), nullable=True)
    report_url = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)

    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="research_jobs")

    def __repr__(self):
        return f"<ResearchJob {self.id} - {self.target} ({self.status})>"
