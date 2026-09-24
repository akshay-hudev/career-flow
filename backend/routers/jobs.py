from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.models import SavedJob, Resume, User
from backend.schemas.schemas import (
    JobSearchRequest, JobSearchResponse, JobResult,
    SaveJobRequest, SavedJobOut, UpdateJobStatus,
)
from backend.services.job_search import search_jobs
from backend.services.semantic_matcher import rank_jobs

router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])


def _get_owned_saved_job(db: Session, job_id: int, user_id: int) -> SavedJob:
    """Fetch a saved job and verify the caller owns it. 404 on mismatch."""
    job = db.query(SavedJob).filter(SavedJob.id == job_id).first()
    if not job or job.user_id != user_id:
        raise HTTPException(status_code=404, detail="Saved job not found.")
    return job


@router.post("/search", response_model=JobSearchResponse)
async def search(
    request: JobSearchRequest,
    resume_id: Optional[int] = Query(None, description="Optionally rank by resume match"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search jobs via Adzuna API (cached in Redis). If resume_id is provided,
    results are ranked by semantic similarity (the resume must belong to the caller)."""
    jobs = await search_jobs(request.query, request.location, request.results)

    if resume_id and jobs:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume or resume.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Resume not found.")
        if resume.embedding_json:
            jobs = rank_jobs(resume.raw_text, resume.embedding_json, jobs)

    job_results = [JobResult(**j) for j in jobs]
    return JobSearchResponse(
        query=request.query,
        location=request.location,
        total=len(job_results),
        jobs=job_results,
    )


@router.post("/save", response_model=SavedJobOut)
):
    """Save a job to the caller's board (owner is taken from the JWT)."""
    existing = db.query(SavedJob).filter(
        SavedJob.user_id == current_user.id,
        SavedJob.job_external_id == request.job_external_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Job already saved.")

    job = SavedJob(
        user_id=current_user.id,
        resume_id=request.resume_id,
        job_external_id=request.job_external_id,
        title=request.title,
        company=request.company,
        location=request.location,
        description=request.description,
        salary_min=request.salary_min,
        salary_max=request.salary_max,
        job_url=request.job_url,
        match_score=request.match_score,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("/saved", response_model=List[SavedJobOut])
):
    """Get the caller's saved jobs, optionally filtered by status."""
    query = db.query(SavedJob).filter(SavedJob.user_id == current_user.id)
    if status:
        query = query.filter(SavedJob.status == status)
    return query.order_by(SavedJob.saved_at.desc()).all()


@router.patch("/saved/{job_id}/status", response_model=SavedJobOut)
):
    """Update a saved job's application status (auth required, owner-only)."""
    job = _get_owned_saved_job(db, job_id, current_user.id)

    job.status = update.status
    if update.notes is not None:
        job.notes = update.notes
    if update.status == "applied" and not job.applied_at:
        from datetime import datetime, timezone
        job.applied_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(job)
    return job


@router.delete("/saved/{job_id}")
):
    """Remove a saved job (auth required, owner-only)."""
    job = _get_owned_saved_job(db, job_id, current_user.id)
    db.delete(job)
    db.commit()
    return {"message": "Job removed."}