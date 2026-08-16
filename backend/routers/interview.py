from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.models import Resume
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
    difficulty: str


class EvaluationOut(BaseModel):
    score: float
    score_out_of: int
    strengths: list
    improvements: list
    sample_better_answer: str
    verdict: str


@router.post("/questions", response_model=list[QuestionOut])
async def get_questions(
    request: GenerateQuestionsRequest,
    db: Session = Depends(get_db),
):
    """
    Generate tailored interview questions based on resume + job.
    Types: technical | behavioral | situational | hr
    """
    if request.count < 1 or request.count > 10:
        raise HTTPException(status_code=400, detail="count must be between 1 and 10.")

    resume = db.query(Resume).filter(Resume.id == request.resume_id).first()
    if not resume:
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


@router.post("/evaluate", response_model=EvaluationOut)
async def evaluate(request: EvaluateAnswerRequest):
    """
    Evaluate a candidate's mock interview answer.
    Returns score, strengths, improvements, and a sample better answer.
    """
    if len(request.user_answer.strip()) < 20:
        raise HTTPException(status_code=400, detail="Answer too short to evaluate meaningfully.")

    result = await evaluate_answer(
        question=request.question,
        user_answer=request.user_answer,
        job_title=request.job_title,
        ideal_framework=request.ideal_answer_framework,
    )
    return result
