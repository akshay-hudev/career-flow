from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from backend.database import Base


class JobStatus(str, enum.Enum):
    saved = "saved"
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=True)
    saved_jobs = relationship("SavedJob", back_populates="user", cascade="all, delete-orphan")
class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    raw_text = Column(Text, nullable=False)
    parsed_data = Column(JSON)          # structured: skills, experience, education
    embedding_json = Column(JSON)       # stored as list of floats
    ats_score = Column(Float)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="resumes")
class SavedJob(Base):
    __tablename__ = "saved_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=True)

    # Job data (denormalized from API response)
    job_external_id = Column(String(255), index=True)
    title = Column(String(255), nullable=False)
    company = Column(String(255))
    location = Column(String(255))
    description = Column(Text)
    salary_min = Column(Float)
    salary_max = Column(Float)
    job_url = Column(String(512))

    match_score = Column(Float)         # 0-100 cosine similarity score
    status = Column(Enum(JobStatus), default=JobStatus.saved)
    notes = Column(Text)
    saved_at = Column(DateTime(timezone=True), server_default=func.now())
    applied_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="saved_jobs")
    resume = relationship("Resume", back_populates="saved_jobs")
