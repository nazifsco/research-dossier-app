"""
Research endpoints: create job, list jobs, get job, download report.
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import and_
import os

from app.database import get_db
from app.models.user import User
from app.models.research import ResearchJob
from app.core.deps import get_current_active_user
from app.config import get_settings
from app.services.research import run_research_pipeline
from app.services.email import send_low_credit_alert

router = APIRouter()
settings = get_settings()

# Duplicate job prevention: window in seconds
DUPLICATE_JOB_WINDOW_SECONDS = 60


# Request/Response schemas
class CreateResearchRequest(BaseModel):
    target: str = Field(min_length=1, max_length=500)
    target_type: str = Field(pattern="^(company|person)$")
    depth: str = Field(default="standard", pattern="^(quick|standard|deep)$")


class ResearchJobResponse(BaseModel):
    id: str
    target: str
    target_type: str
    depth: str
    status: str
    credits_used: int
    error_message: str | None
    created_at: str
    started_at: str | None
    completed_at: str | None

    class Config:
        from_attributes = True


class ResearchJobDetailResponse(ResearchJobResponse):
    report_url: str | None


class ResearchJobListResponse(BaseModel):
    jobs: list[ResearchJobResponse]
    total: int


def get_credit_cost(depth: str) -> int:
    """Get credit cost for research depth."""
    costs = {
        "quick": settings.credit_cost_quick,
        "standard": settings.credit_cost_standard,
        "deep": settings.credit_cost_deep
    }
    return costs.get(depth, settings.credit_cost_standard)


@router.post("", response_model=ResearchJobResponse, status_code=status.HTTP_201_CREATED)
async def create_research_job(
    request: CreateResearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new research job.
    Deducts credits and starts async processing.
    """
    # Calculate credit cost
    credit_cost = get_credit_cost(request.depth)

    # Check credits
    if current_user.credits < credit_cost:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Insufficient credits. Need {credit_cost}, have {current_user.credits}"
        )

    # Prevent duplicate jobs for the same target within time window
    cutoff_time = datetime.utcnow() - timedelta(seconds=DUPLICATE_JOB_WINDOW_SECONDS)
    existing_job = db.query(ResearchJob).filter(
        and_(
            ResearchJob.user_id == current_user.id,
            ResearchJob.target == request.target.strip(),
            ResearchJob.target_type == request.target_type,
            ResearchJob.created_at > cutoff_time
        )
    ).first()

    if existing_job:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A research job for this target was already created. Please wait before creating another."
        )

    # Deduct credits
    current_user.credits -= credit_cost
    db.add(current_user)

    # Create job
    job = ResearchJob(
        user_id=current_user.id,
        target=request.target,
        target_type=request.target_type,
        depth=request.depth,
        credits_used=credit_cost,
        status="pending"
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Start background processing
    background_tasks.add_task(
        run_research_pipeline,
        job_id=job.id,
        target=job.target,
        target_type=job.target_type,
        depth=job.depth
    )

    # Send low credit alert if credits are now 0
    if current_user.credits == 0:
        background_tasks.add_task(
            send_low_credit_alert,
            to=current_user.email,
            name=current_user.name,
            remaining_credits=0
        )

    return ResearchJobResponse(
        id=job.id,
        target=job.target,
        target_type=job.target_type,
        depth=job.depth,
        status=job.status,
        credits_used=job.credits_used,
        error_message=job.error_message,
        created_at=job.created_at.isoformat(),
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None
    )


@router.get("", response_model=ResearchJobListResponse)
async def list_research_jobs(
    status_filter: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List user's research jobs.
    Optionally filter by status.
    """
    query = db.query(ResearchJob).filter(ResearchJob.user_id == current_user.id)

    if status_filter:
        query = query.filter(ResearchJob.status == status_filter)

    # Get total count
    total = query.count()

    # Get paginated jobs
    jobs = query.order_by(ResearchJob.created_at.desc()).offset(offset).limit(limit).all()

    return ResearchJobListResponse(
        jobs=[
            ResearchJobResponse(
                id=job.id,
                target=job.target,
                target_type=job.target_type,
                depth=job.depth,
                status=job.status,
                credits_used=job.credits_used,
                error_message=job.error_message,
                created_at=job.created_at.isoformat(),
                started_at=job.started_at.isoformat() if job.started_at else None,
                completed_at=job.completed_at.isoformat() if job.completed_at else None
            )
            for job in jobs
        ],
        total=total
    )


@router.get("/{job_id}/download")
async def download_report(
    job_id: str,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Download the report HTML for a completed job.
    Accepts token as query param for direct browser downloads.
    NOTE: This route MUST be defined BEFORE /{job_id} to ensure proper matching.
    """
    from app.core.security import decode_access_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token required"
        )

    # Validate token
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    user_id = payload.get("sub")
    current_user = db.query(User).filter(User.id == user_id).first()

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    job = db.query(ResearchJob).filter(
        ResearchJob.id == job_id,
        ResearchJob.user_id == current_user.id
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research job not found"
        )

    if job.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Report not ready. Current status: {job.status}"
        )

    if not job.report_path or not os.path.exists(job.report_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file not found"
        )

    # Determine filename
    safe_target = "".join(c for c in job.target if c.isalnum() or c in " -_").strip()
    filename = f"Research_Dossier_{safe_target}.html"

    return FileResponse(
        path=job.report_path,
        filename=filename,
        media_type="text/html"
    )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_research_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a research job.
    Only allows deletion of completed or failed jobs (not pending/processing).
    NOTE: This route MUST be defined BEFORE GET /{job_id} to ensure proper matching.
    """
    job = db.query(ResearchJob).filter(
        ResearchJob.id == job_id,
        ResearchJob.user_id == current_user.id
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research job not found"
        )

    # Don't allow deleting jobs that are still processing
    if job.status in ["pending", "processing"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a job that is still processing"
        )

    # Optionally delete the report files
    if job.report_path:
        import shutil
        from pathlib import Path
        report_path = Path(job.report_path)
        if report_path.exists():
            # Delete the entire research directory
            research_dir = report_path.parent
            try:
                shutil.rmtree(research_dir)
            except Exception:
                pass  # Ignore file deletion errors

    db.delete(job)
    db.commit()

    return None


@router.get("/{job_id}", response_model=ResearchJobDetailResponse)
async def get_research_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get details of a specific research job.
    """
    job = db.query(ResearchJob).filter(
        ResearchJob.id == job_id,
        ResearchJob.user_id == current_user.id
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research job not found"
        )

    return ResearchJobDetailResponse(
        id=job.id,
        target=job.target,
        target_type=job.target_type,
        depth=job.depth,
        status=job.status,
        credits_used=job.credits_used,
        error_message=job.error_message,
        report_url=job.report_url,
        created_at=job.created_at.isoformat(),
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None
    )
