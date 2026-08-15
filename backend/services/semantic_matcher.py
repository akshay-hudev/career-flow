import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from backend.services.resume_parser import TECH_SKILLS
import re

_vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)


def get_embedding(text: str) -> list[float]:
    """Generate a TF-IDF vector for a text string."""
    try:
        matrix = _vectorizer.fit_transform([text])
        return matrix.toarray()[0].tolist()
    except ValueError:
        # Empty vocabulary — text was empty or only stop-words/punctuation.
        return []


def cosine_similarity_score(emb1: list[float], emb2: list[float]) -> float:
    a = np.array(emb1, dtype=float)
    b = np.array(emb2, dtype=float)
    if a.size == 0 or b.size == 0:
        return 0.0
    # Pad to the same length so vectors of different vocab sizes are comparable.
    max_len = max(len(a), len(b))
    a = np.pad(a, (0, max_len - len(a)))
    b = np.pad(b, (0, max_len - len(b)))
    score = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8)
    return round(float(score) * 100, 2)


def get_model():
    return _vectorizer


def extract_skills_from_text(text: str) -> set[str]:
    """Extract skill keywords from any text."""
    text_lower = text.lower()
    found = set()
    for skill in TECH_SKILLS:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found.add(skill.lower())
    return found


def compute_match(resume_text, resume_embedding, job_description, job_index=0):
    combined = _vectorizer.fit_transform([resume_text[:3000], job_description])
    resume_emb = combined[0].toarray()[0].tolist()
    job_emb = combined[1].toarray()[0].tolist()
    score = cosine_similarity_score(resume_emb, job_emb)
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
