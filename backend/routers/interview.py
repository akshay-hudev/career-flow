from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.models import Resume, User
from backend.services.interview_service import generate_interview_questions, evaluate_answer

router = APIRouter(prefix="/api/v1/interview", tags=["Interview"])


class GenerateQuestionsRequest(BaseModel):
    resume_id: int
    job_title: str
    job_description: Optional[str] = ""
    question_type: str = "technical"   # behavioral | technical | situational | hr
    count: int = 5


class EvaluateAnswerRequest(BaseModel):
    question: str
    user_answer: str
    job_title: str
    ideal_answer_framework: str


class QuestionOut(BaseModel):
    question: str
    ideal_answer_framework: str
class EvaluationOut(BaseModel):
    score: float
@router.post("/questions", response_model=list[QuestionOut])
):
    """Generate tailored interview questions (auth required; resume must be owned by caller)."""
    if request.count < 1 or request.count > 10:
        raise HTTPException(status_code=400, detail="count must be between 1 and 10.")

    resume = db.query(Resume).filter(Resume.id == request.resume_id).first()
    if not resume or resume.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Resume not found.")

    skills = (resume.parsed_data or {}).get("skills", [])

    questions = await generate_interview_questions(
        job_title=request.job_title,
        job_description=request.job_description,
        skills=skills,
        question_type=request.question_type,
        count=request.count,
    )
    return questions


async def evaluate(
    request: EvaluateAnswerRequest,
    current_user: User = Depends(get_current_user),
):
    """Evaluate a candidate's mock interview answer (auth required to prevent
    anonymous abuse of the Gemini quota)."""
    if len(request.user_answer.strip()) < 20:
        raise HTTPException(status_code=400, detail="Answer too short to evaluate meaningfully.")

    result = await evaluate_answer(
        question=request.question,
        user_answer=request.user_answer,
        job_title=request.job_title,
        ideal_framework=request.ideal_answer_framework,
    )
    return result