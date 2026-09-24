from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.models import Resume, User
from backend.schemas.schemas import (
    MatchRequest, MatchResponse, MatchResult,
    CareerAdviceRequest, CareerAdviceResponse,
)
from backend.services.semantic_matcher import compute_match
from backend.services.llm_service import generate_career_advice

router = APIRouter(prefix="/api/v1/match", tags=["Match"])


def _get_owned_resume(db: Session, resume_id: int, user_id: int) -> Resume:
    """Fetch a resume and verify the caller owns it. 404 on mismatch."""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume or resume.user_id != user_id:
        raise HTTPException(status_code=404, detail="Resume not found.")
    return resume


@router.post("/score", response_model=MatchResponse)
):
    """Score the caller's resume against multiple job descriptions (auth required)."""
    resume = _get_owned_resume(db, request.resume_id, current_user.id)
    if not resume.embedding_json:
        raise HTTPException(status_code=422, detail="Resume has no embedding. Re-upload.")

    results = []
    for i, jd in enumerate(request.job_descriptions):
        match = compute_match(
            resume_text=resume.raw_text,
            resume_embedding=resume.embedding_json,
            job_description=jd,
            job_index=i,
        )
        results.append(MatchResult(**match))

    return MatchResponse(results=results)


@router.post("/advice", response_model=CareerAdviceResponse)
):
    """Full AI-powered career advice for the caller's resume vs a specific job."""
    resume = _get_owned_resume(db, request.resume_id, current_user.id)

    if not resume.embedding_json:
        raise HTTPException(status_code=422, detail="Resume has no embedding. Re-upload.")

    match = compute_match(
        resume_text=resume.raw_text,
        resume_embedding=resume.embedding_json,
        job_description=request.job_description,
    )

    advice = await generate_career_advice(
        resume_text=resume.raw_text,
        job_title=request.job_title,
        job_description=request.job_description,
        matched_skills=match["matched_skills"],
        skill_gaps=match["skill_gaps"],
        ats_score=match["score"],
    )

    return CareerAdviceResponse(
        ats_score=match["score"],
        skill_gaps=match["skill_gaps"],
        matched_skills=match["matched_skills"],
        improvement_suggestions=advice.get("improvement_suggestions", []),
        cover_letter_draft=advice.get("cover_letter_draft", ""),
        interview_tips=advice.get("interview_tips", []),
    )