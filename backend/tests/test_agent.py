import pytest
import unittest.mock as mock
import asyncio
from backend.services.career_agent import run_career_agent


FAKE_PDF = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R"
    b"/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
    b"4 0 obj<</Length 50>>stream\nBT /F1 12 Tf 100 700 Td"
    b"(Python Java React Flask PostgreSQL 3 years) Tj ET\nendstream endobj\n"
    b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
    b"xref\n0 6\n0000000000 65535 f\n"
    b"trailer<</Size 6/Root 1 0 R>>\nstartxref\n%%EOF\n"
)

MOCK_JOBS = [
    {"external_id": "j1", "title": "Python Backend Engineer", "company": "Razorpay",
     "location": "Bengaluru", "description": "Python Flask FastAPI PostgreSQL", "match_score": None,
     "salary_min": 1200000, "salary_max": 1800000, "job_url": "https://example.com/1"},
    {"external_id": "j2", "title": "Java Developer", "company": "Infosys",
     "location": "Mumbai", "description": "Java Spring Boot microservices", "match_score": None,
     "salary_min": 800000, "salary_max": 1200000, "job_url": "https://example.com/2"},
]

MOCK_ADVICE = {
    "improvement_suggestions": ["Quantify impact.", "Add more Python keywords."],
    "cover_letter_draft": "Dear Hiring Manager,\n\nI am a strong fit.\n\nSincerely,\nTest",
    "interview_tips": ["Research Razorpay products.", "Prepare system design."],
}


class TestCareerAgent:
    @pytest.mark.asyncio
    async def test_full_pipeline_completes(self):
        """Agent should complete all 4 steps successfully."""
        with mock.patch("backend.services.career_agent.parse_resume") as mock_parse, \
             mock.patch("backend.services.career_agent.get_embedding") as mock_emb, \
             mock.patch("backend.services.career_agent.search_jobs") as mock_search, \
             mock.patch("backend.services.career_agent.rank_jobs") as mock_rank, \
             mock.patch("backend.services.career_agent.compute_match") as mock_match, \
             mock.patch("backend.services.career_agent.generate_career_advice") as mock_advice:

            from backend.schemas.schemas import ParsedResume
            mock_parse.return_value = (
                "Python developer 3 years Flask",
                ParsedResume(skills=["Python", "Flask"], experience_years=3.0),
                72.5,
            )
            mock_emb.return_value = [0.1] * 384
            mock_search.return_value = MOCK_JOBS
            ranked = [{**j, "match_score": 80.0 if "Python" in j["title"] else 45.0} for j in MOCK_JOBS]
            mock_rank.return_value = sorted(ranked, key=lambda x: x["match_score"], reverse=True)
            mock_match.return_value = {
                "score": 80.0, "matched_skills": ["Python", "Flask"], "skill_gaps": ["Docker"],
            }
            mock_advice.return_value = MOCK_ADVICE

            state = await run_career_agent(
                file_bytes=FAKE_PDF,
                filename="test_resume.pdf",
                job_query="Python Backend Engineer",
                location="Bengaluru",
            )

        assert state["error"] is None
        assert "parse_resume" in state["steps_completed"]
        assert "search_jobs" in state["steps_completed"]
        assert "rank_matches" in state["steps_completed"]
        assert "generate_advice" in state["steps_completed"]
        assert len(state["steps_completed"]) == 4

    @pytest.mark.asyncio
    async def test_parse_failure_sets_error(self):
        """If resume parsing fails, error is set and subsequent nodes are skipped."""
        with mock.patch("backend.services.career_agent.parse_resume") as mock_parse:
            state = await run_career_agent(
                file_bytes=b"not a pdf",
                filename="bad.pdf",
                job_query="Engineer",
                location="India",
            )

        assert state["error"] is not None
        assert "parse_resume" not in state["steps_completed"]

    @pytest.mark.asyncio
    async def test_jobs_are_ranked_by_score(self):
        """ranked_jobs should be sorted descending by match_score."""
        with mock.patch("backend.services.career_agent.parse_resume") as mock_parse, \
             mock.patch("backend.services.career_agent.get_embedding") as mock_emb, \
             mock.patch("backend.services.career_agent.search_jobs") as mock_search, \
             mock.patch("backend.services.career_agent.rank_jobs") as mock_rank, \
             mock.patch("backend.services.career_agent.compute_match") as mock_match, \
             mock.patch("backend.services.career_agent.generate_career_advice") as mock_advice:

            from backend.schemas.schemas import ParsedResume
            mock_parse.return_value = ("text", ParsedResume(skills=["Python"]), 60.0)
            mock_emb.return_value = [0.1] * 384
            mock_search.return_value = MOCK_JOBS
            mock_rank.return_value = [
                {**MOCK_JOBS[0], "match_score": 85.0},
                {**MOCK_JOBS[1], "match_score": 42.0},
            ]
            mock_match.return_value = {"score": 85.0, "matched_skills": ["Python"], "skill_gaps": []}
            mock_advice.return_value = MOCK_ADVICE

            state = await run_career_agent(FAKE_PDF, "resume.pdf", "Python Engineer", "India")

        scores = [j["match_score"] for j in state["ranked_jobs"]]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_no_jobs_skips_advice(self):
        """If no jobs found, generate_advice node is skipped."""
        with mock.patch("backend.services.career_agent.parse_resume") as mock_parse, \
             mock.patch("backend.services.career_agent.get_embedding") as mock_emb, \
             mock.patch("backend.services.career_agent.search_jobs") as mock_search, \
             mock.patch("backend.services.career_agent.rank_jobs") as mock_rank:

            from backend.schemas.schemas import ParsedResume
            mock_parse.return_value = ("text", ParsedResume(), 40.0)
            mock_emb.return_value = [0.1] * 384
            mock_search.return_value = []
            state = await run_career_agent(FAKE_PDF, "resume.pdf", "Rare Job Title", "Antarctica")

        assert "generate_advice" not in state["steps_completed"]
        assert state["advice"] is None
