import pytest
import unittest.mock as mock
import io


def _upload_resume(client, user_id: int = None) -> int:
    """Helper: upload a fake resume and return its ID."""
    fake_pdf = (
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
    with mock.patch("backend.services.semantic_matcher.get_model") as m:
        mock_model = mock.MagicMock()
        mock_model.encode.return_value = [0.1] * 384
        m.return_value = mock_model
        with mock.patch("backend.services.llm_service._model") as llm:
            llm.generate_content.return_value = mock.MagicMock(
                text="Experienced Python developer with 3 years of backend experience."
            )
            res = client.post(
                "/api/v1/resume/upload",
                files={"file": ("resume.pdf", io.BytesIO(fake_pdf), "application/pdf")},
            )
    assert res.status_code == 200, f"Resume upload failed: {res.text}"
    return res.json()["id"]


class TestMatchScore:
    def test_score_returns_results(self, client, test_user):
        resume_id = _upload_resume(client, test_user["id"])

        with mock.patch("backend.services.semantic_matcher.get_model") as m:
            mock_model = mock.MagicMock()
            mock_model.encode.return_value = [0.1] * 384
            m.return_value = mock_model

            res = client.post("/api/v1/match/score", json={
                "resume_id": resume_id,
                "job_descriptions": [
                    "Python developer with Flask experience needed.",
                    "Java backend engineer for Spring Boot microservices.",
                ],
            })

        assert res.status_code == 200
        data = res.json()
        assert "results" in data
        assert len(data["results"]) == 2
        for result in data["results"]:
            assert "score" in result
            assert "matched_skills" in result
            assert "skill_gaps" in result
            assert 0 <= result["score"] <= 100

    def test_score_resume_not_found(self, client):
        res = client.post("/api/v1/match/score", json={
            "resume_id": 999999,
            "job_descriptions": ["Python developer needed."],
        })
        assert res.status_code == 404

    def test_score_empty_descriptions(self, client, test_user):
        resume_id = _upload_resume(client, test_user["id"])

        with mock.patch("backend.services.semantic_matcher.get_model") as m:
            m.return_value = mock.MagicMock(encode=mock.MagicMock(return_value=[0.1] * 384))
            res = client.post("/api/v1/match/score", json={
                "resume_id": resume_id,
                "job_descriptions": [],
            })

        assert res.status_code == 200
        assert res.json()["results"] == []


class TestCareerAdvice:
    def test_advice_returns_all_fields(self, client, test_user):
        resume_id = _upload_resume(client, test_user["id"])

        with mock.patch("backend.services.semantic_matcher.get_model") as m:
            m.return_value = mock.MagicMock(encode=mock.MagicMock(return_value=[0.1] * 384))
            with mock.patch("backend.services.llm_service._model") as llm:
                }''')

                res = client.post("/api/v1/match/advice", json={
                    "resume_id": resume_id,
                    "job_title": "Backend Engineer",
                    "job_description": "Looking for Python Flask developer with 3+ years experience.",
                })

        assert res.status_code == 200
        data = res.json()
        assert "ats_score" in data
        assert "skill_gaps" in data
        assert "matched_skills" in data
        assert "improvement_suggestions" in data
        assert "cover_letter_draft" in data
        assert "interview_tips" in data
        assert isinstance(data["improvement_suggestions"], list)
        assert isinstance(data["interview_tips"], list)
        assert 0 <= data["ats_score"] <= 100

    def test_advice_resume_not_found(self, client):
        res = client.post("/api/v1/match/advice", json={
            "resume_id": 999999,
            "job_title": "Engineer",
            "job_description": "Python developer needed.",
        })
        assert res.status_code == 404
