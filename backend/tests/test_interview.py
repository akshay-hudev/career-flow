import pytest
import unittest.mock as mock
import io


def _make_resume(client, user_id: int) -> int:
    fake_pdf = (
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R"
        b"/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
        b"4 0 obj<</Length 38>>stream\nBT /F1 12 Tf 100 700 Td"
        b"(Python React 3 years) Tj ET\nendstream endobj\n"
        b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
        b"xref\n0 6\n0000000000 65535 f\n"
        b"trailer<</Size 6/Root 1 0 R>>\nstartxref\n%%EOF\n"
    )
    with mock.patch("backend.services.semantic_matcher.get_model") as m:
        m.return_value = mock.MagicMock(encode=mock.MagicMock(return_value=[0.1] * 384))
        with mock.patch("backend.services.llm_service._model") as llm:
            llm.generate_content.return_value = mock.MagicMock(text="Python developer.")
            res = client.post(
                f"/api/v1/resume/upload?user_id={user_id}",
                files={"file": ("resume.pdf", io.BytesIO(fake_pdf), "application/pdf")},
            )
    return res.json()["id"]


MOCK_QUESTIONS = [
    {"question": "Tell me about a Python project.", "ideal_answer_framework": "Use STAR.", "difficulty": "medium"},
    {"question": "How do you handle deadlines?", "ideal_answer_framework": "Describe a process.", "difficulty": "easy"},
    {"question": "Explain async in Python.", "ideal_answer_framework": "asyncio, await, event loop.", "difficulty": "hard"},
]

MOCK_EVALUATION = {
    "score": 7,
    "score_out_of": 10,
    "strengths": ["Clear structure", "Relevant example"],
    "improvements": ["Add more metrics", "Expand on impact"],
    "sample_better_answer": "A stronger answer would include specific numbers.",
    "verdict": "Good answer with room for improvement.",
}


class TestGenerateQuestions:
    def test_returns_questions(self, client, test_user):
        resume_id = _make_resume(client, test_user["id"])

        with mock.patch("backend.services.interview_service._model") as m:
            m.generate_content.return_value = mock.MagicMock(
                text='[{"question":"Explain Python GIL.","ideal_answer_framework":"Threading limitations.","difficulty":"hard"},'
                     '{"question":"Tell me about yourself.","ideal_answer_framework":"Structured intro.","difficulty":"easy"},'
                     '{"question":"What is REST?","ideal_answer_framework":"HTTP, stateless.","difficulty":"medium"}]'
            )
            res = client.post("/api/v1/interview/questions", json={
                "resume_id": resume_id,
                "job_title": "Backend Engineer",
                "job_description": "Python FastAPI developer",
                "question_type": "technical",
                "count": 3,
            })

        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) == 3
        for q in data:
            assert "question" in q
            assert "ideal_answer_framework" in q
            assert "difficulty" in q
            assert q["difficulty"] in ("easy", "medium", "hard")

    def test_falls_back_when_llm_fails(self, client, test_user):
        resume_id = _make_resume(client, test_user["id"])

        with mock.patch("backend.services.interview_service._model") as m:
            m.generate_content.side_effect = Exception("LLM unavailable")
            res = client.post("/api/v1/interview/questions", json={
                "resume_id": resume_id,
                "job_title": "Backend Engineer",
                "job_description": "",
                "question_type": "behavioral",
                "count": 3,
            })

        # Should still return fallback questions
        assert res.status_code == 200
        assert len(res.json()) == 3

    def test_invalid_count_rejected(self, client, test_user):
        resume_id = _make_resume(client, test_user["id"])
        res = client.post("/api/v1/interview/questions", json={
            "resume_id": resume_id,
            "job_title": "Engineer",
            "job_description": "",
            "question_type": "technical",
            "count": 99,  # over limit
        })
        assert res.status_code == 400

    def test_resume_not_found(self, client):
        res = client.post("/api/v1/interview/questions", json={
            "resume_id": 999999,
            "job_title": "Engineer",
            "job_description": "",
            "question_type": "technical",
            "count": 3,
        })
        assert res.status_code == 404


class TestEvaluateAnswer:
    def test_returns_evaluation_fields(self, client):
        with mock.patch("backend.services.interview_service._model") as m:
            import json
            m.generate_content.return_value = mock.MagicMock(
                text=json.dumps(MOCK_EVALUATION)
            )
            res = client.post("/api/v1/interview/evaluate", json={
                "question": "Tell me about a Python project you built.",
                "user_answer": "I built a Flask REST API for resume analysis that processed over 1000 resumes using NLP techniques and integrated with a PostgreSQL database.",
                "job_title": "Backend Engineer",
                "ideal_answer_framework": "Use STAR format with specific metrics.",
            })

        assert res.status_code == 200
        data = res.json()
        assert "score" in data
        assert "score_out_of" in data
        assert "strengths" in data
        assert "improvements" in data
        assert "sample_better_answer" in data
        assert "verdict" in data
        assert 0 <= data["score"] <= data["score_out_of"]

    def test_short_answer_rejected(self, client):
        res = client.post("/api/v1/interview/evaluate", json={
            "question": "Tell me about yourself.",
            "user_answer": "I am good.",  # too short
            "job_title": "Engineer",
            "ideal_answer_framework": "Structured intro.",
        })
        assert res.status_code == 400

    def test_falls_back_on_llm_error(self, client):
        with mock.patch("backend.services.interview_service._model") as m:
            m.generate_content.side_effect = Exception("LLM down")
            res = client.post("/api/v1/interview/evaluate", json={
                "question": "Describe a challenging project.",
                "user_answer": "I worked on a distributed system that handled real-time data processing for millions of users using Kafka.",
                "job_title": "Backend Engineer",
                "ideal_answer_framework": "STAR format.",
            })
        # Fallback should still return 200
        assert res.status_code == 200
