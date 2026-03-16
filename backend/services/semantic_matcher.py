import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine
from typing import Optional
from backend.services.resume_parser import TECH_SKILLS
import re

_vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)

def get_embedding(text: str) -> list[float]:
    """Generate TF-IDF vector for a text string."""
    matrix = _vectorizer.fit_transform([text])
    return matrix.toarray()[0].tolist()

def cosine_similarity_score(emb1: list[float], emb2: list[float]) -> float:
    a = np.array(emb1).reshape(1, -1)
    b = np.array(emb2).reshape(1, -1)
    # Pad to same length
    max_len = max(a.shape[1], b.shape[1])
    a = np.pad(a, ((0,0),(0, max_len - a.shape[1])))
    b = np.pad(b, ((0,0),(0, max_len - b.shape[1])))
    score = sklearn_cosine(a, b)[0][0]
    return round(float(score) * 100, 2)

def get_model():
    return _vectorizer


def get_embedding(text: str) -> list[float]:
    """Generate sentence embedding for a text string."""
    model = get_model()
    embedding = model.encode(text, convert_to_tensor=False)
    return embedding.tolist()


def cosine_similarity_score(emb1: list[float], emb2: list[float]) -> float:
    """Compute cosine similarity between two embeddings. Returns 0-100."""
    a = np.array(emb1)
    b = np.array(emb2)
    score = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8)
    return round(float(score) * 100, 2)


def extract_skills_from_text(text: str) -> set[str]:
    """Extract skill keywords from any text."""
    text_lower = text.lower()
    found = set()
    for skill in TECH_SKILLS:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found.add(skill.lower())
    return found


def compute_match(
    resume_text: str,
    resume_embedding: list[float],
    job_description: str,
    job_index: int = 0,
) -> dict:
    """
    Compute full match analysis between a resume and a job description.

    Returns:
        index, score (0-100), matched_skills, skill_gaps
    """
    job_embedding = get_embedding(job_description)
    score = cosine_similarity_score(resume_embedding, job_embedding)

    resume_skills = extract_skills_from_text(resume_text)
    job_skills = extract_skills_from_text(job_description)

    matched = sorted(resume_skills & job_skills)
    gaps = sorted(job_skills - resume_skills)

    return {
        "index": job_index,
        "score": score,
        "matched_skills": [s.title() if len(s) > 3 else s.upper() for s in matched],
        "skill_gaps": [s.title() if len(s) > 3 else s.upper() for s in gaps],
    }


def rank_jobs(resume_text, resume_embedding, jobs):
    if not jobs:
        return []
    for job in jobs:
        desc = job.get("description", "")
        if desc:
            job_emb = get_embedding(desc)
            job["match_score"] = cosine_similarity_score(resume_embedding, job_emb)
        else:
            job["match_score"] = 0.0
    return sorted(jobs, key=lambda x: x["match_score"], reverse=True)