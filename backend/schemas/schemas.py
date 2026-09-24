from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from backend.models.models import JobStatus

# ── Auth Schemas ──────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    email: EmailStr
    name: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    user: "UserOut"

# ── User Schemas ──────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    name: str

class UserOut(BaseModel):
    id: int
    email: str
    name: str
    class Config:
        from_attributes = True


# ── Resume Schemas ────────────────────────────────────────────────────────────

class ParsedResume(BaseModel):
    skills: List[str] = []
    experience_years: Optional[float] = None
    education: List[str] = []
    companies: List[str] = []
    summary: Optional[str] = None

class ResumeOut(BaseModel):
    id: int
    filename: str
    parsed_data: Optional[ParsedResume]
    ats_score: Optional[float]
    uploaded_at: datetime

    class Config:
        from_attributes = True


# ── Job Schemas ───────────────────────────────────────────────────────────────

class JobSearchRequest(BaseModel):
    query: str
    location: str = "India"
    results: int = 20

class JobResult(BaseModel):
    title: str
    company: Optional[str]
    location: Optional[str]
    description: Optional[str]
    salary_min: Optional[float]
    salary_max: Optional[float]
    job_url: Optional[str]
    match_score: Optional[float] = None

class JobSearchResponse(BaseModel):
    query: str
    location: str
    jobs: List[JobResult]


# ── Match Schemas ─────────────────────────────────────────────────────────────

class MatchRequest(BaseModel):
    resume_id: int
    job_descriptions: List[str]

class MatchResult(BaseModel):
    score: float
    skill_gaps: List[str]
    matched_skills: List[str]

class MatchResponse(BaseModel):
    results: List[MatchResult]


# ── Saved Job Schemas ─────────────────────────────────────────────────────────

class SaveJobRequest(BaseModel):
    resume_id: Optional[int] = None
    job_external_id: str
    title: str
    company: Optional[str]
    location: Optional[str]
    description: Optional[str]
    salary_min: Optional[float]
    salary_max: Optional[float]
    job_url: Optional[str]
    match_score: Optional[float]

class UpdateJobStatus(BaseModel):
    status: JobStatus
    notes: Optional[str] = None

class SavedJobOut(BaseModel):
    id: int
    job_external_id: str
    title: str
    company: Optional[str]
    location: Optional[str]
    match_score: Optional[float]
    status: JobStatus
    notes: Optional[str]
    saved_at: datetime
    applied_at: Optional[datetime]

# ── Career Advice Schema ──────────────────────────────────────────────────────

class CareerAdviceRequest(BaseModel):
    resume_id: int
    job_title: str
    job_description: str

class CareerAdviceResponse(BaseModel):
    ats_score: float
    skill_gaps: List[str]
    matched_skills: List[str]
