from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
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


@router.post("/upload", response_model=ResumeOut)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a PDF resume. Returns parsed data, ATS score, and extracted skills."""
    user_id = current_user.id
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # Validate user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    file_bytes = await file.read()
    if len(file_bytes) > 5 * 1024 * 1024:  # 5MB limit
        raise HTTPException(status_code=400, detail="File too large. Max 5MB.")

    # Parse resume
    raw_text, parsed_data, ats_score = parse_resume(file_bytes, file.filename)

    if not raw_text.strip():
        raise HTTPException(status_code=422, detail="Could not extract text from PDF.")

    # Generate embedding for semantic matching
    embedding = get_embedding(raw_text[:3000])

    # Generate AI summary if no summary found
    if not parsed_data.summary:
        parsed_data.summary = await generate_resume_summary(raw_text)

    # Save to database
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


@router.get("/{user_id}/list", response_model=List[ResumeOut])
def list_resumes(user_id: int, db: Session = Depends(get_db)):
    """List all resumes for a user."""
    resumes = db.query(Resume).filter(Resume.user_id == user_id).order_by(Resume.uploaded_at.desc()).all()
    return resumes


@router.get("/{resume_id}", response_model=ResumeOut)
def get_resume(resume_id: int, db: Session = Depends(get_db)):
    """Get a single resume by ID."""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")
    return resume


@router.delete("/{resume_id}")
def delete_resume(resume_id: int, db: Session = Depends(get_db)):
    """Delete a resume."""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")
    db.delete(resume)
    db.commit()
    return {"message": "Resume deleted successfully."}
