from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.models import Resume, User
from backend.schemas.schemas import ResumeOut
from backend.services.resume_parser import parse_resume
from backend.services.semantic_matcher import get_embedding
from backend.services.llm_service import generate_resume_summary

router = APIRouter(prefix="/api/v1/resume", tags=["Resume"])


def _get_owned_resume(db: Session, resume_id: int, user_id: int) -> Resume:
    """Fetch a resume and verify the caller owns it. 404 (not 403) on mismatch
    so we don't leak the existence of other users' resumes."""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume or resume.user_id != user_id:
        raise HTTPException(status_code=404, detail="Resume not found.")
    return resume


@router.post("/upload", response_model=ResumeOut)
):
    """Upload a PDF resume. Returns parsed data, ATS score, and extracted skills."""
    user_id = current_user.id
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    file_bytes = await file.read()
    if len(file_bytes) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max 5MB.")

    try:
        raw_text, parsed_data, ats_score = parse_resume(file_bytes, file.filename)
    except Exception:
        raise HTTPException(status_code=422, detail="Uploaded file is not a readable PDF.")

    if not raw_text.strip():
        raise HTTPException(status_code=422, detail="Could not extract text from PDF.")

    embedding = get_embedding(raw_text[:3000])

    if not parsed_data.summary:
        parsed_data.summary = await generate_resume_summary(raw_text)

    resume = Resume(
        user_id=user_id,
        filename=file.filename,
        raw_text=raw_text,
        parsed_data=parsed_data.model_dump(),
        embedding_json=embedding,
        ats_score=ats_score,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


@router.get("/list", response_model=List[ResumeOut])
):
    """List the caller's resumes (auth required; ignores any client-supplied user_id)."""
    return (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id)
        .order_by(Resume.uploaded_at.desc())
        .all()
    )


@router.get("/{resume_id}", response_model=ResumeOut)
):
    """Get a single resume by ID (auth required, owner-only)."""
    return _get_owned_resume(db, resume_id, current_user.id)


@router.delete("/{resume_id}")
):
    """Delete a resume (auth required, owner-only)."""
    resume = _get_owned_resume(db, resume_id, current_user.id)
    db.delete(resume)
    db.commit()
    return {"message": "Resume deleted successfully."}