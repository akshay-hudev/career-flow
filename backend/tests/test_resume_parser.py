import pytest
from backend.services.resume_parser import (
    extract_skills,
    extract_experience_years,
    extract_education,
    calculate_ats_score,
)
from backend.schemas.schemas import ParsedResume


class TestExtractSkills:
    def test_extracts_known_skills(self):
        text = "I have experience with Python, React, and PostgreSQL."
        skills = extract_skills(text)
        assert "Python" in skills
        assert "React" in skills
        assert "Postgresql" in skills or "PostgreSQL" in skills

    def test_case_insensitive(self):
        text = "proficient in PYTHON and java"
        skills = extract_skills(text)
        assert "Python" in skills
        assert "Java" in skills

    def test_no_false_positives(self):
        text = "I enjoy hiking and cooking."
        skills = extract_skills(text)
        assert len(skills) == 0

    def test_returns_sorted_list(self):
        text = "Python, Java, C++, React"
        skills = extract_skills(text)
        assert skills == sorted(skills)


class TestExtractExperience:
    def test_extracts_years(self):
        text = "5 years of experience in backend development."
        assert extract_experience_years(text) == 5.0

    def test_extracts_with_plus(self):
        text = "3+ years experience with cloud platforms"
        assert extract_experience_years(text) == 3.0

    def test_returns_none_when_missing(self):
        text = "No experience mentioned here."
        assert extract_experience_years(text) is None

    def test_alternative_phrasing(self):
        text = "experience of 7 years in machine learning"
        assert extract_experience_years(text) == 7.0


class TestExtractEducation:
    def test_finds_degree(self):
        text = "B.E. in Computer Science and Engineering from RVITM"
        edu = extract_education(text)
        assert len(edu) > 0
        assert any("B.E." in e or "Computer Science" in e for e in edu)

    def test_empty_text(self):
        edu = extract_education("")
        assert edu == []


class TestATSScore:
    def test_full_resume_scores_high(self):
        parsed = ParsedResume(
            skills=["Python", "React", "Docker", "PostgreSQL", "FastAPI", "Git", "AWS", "Java", "Flask"],
            experience_years=3.0,
            education=["B.E. in Computer Science, RVITM 2023-2027"],
            companies=["Infosys", "Capabl AI"],
            summary="Experienced backend engineer with 3 years of Python development.",
        )
        score = calculate_ats_score(parsed, "3 years experience python backend")
        assert score >= 70

    def test_empty_resume_scores_low(self):
        parsed = ParsedResume()
        score = calculate_ats_score(parsed, "")
        assert score < 20

    def test_score_capped_at_100(self):
        parsed = ParsedResume(
            skills=["Python"] * 20,
            experience_years=10.0,
            education=["PhD Computer Science"],
            companies=["Google", "Meta", "Apple"],
            summary="Senior engineer with extensive experience.",
        )
        score = calculate_ats_score(parsed, "engineer experience")
        assert score <= 100
