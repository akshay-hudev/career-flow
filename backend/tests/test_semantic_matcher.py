import pytest
from backend.services.semantic_matcher import (
    cosine_similarity_score,
    extract_skills_from_text,
    compute_match,
    rank_jobs,
)


class TestCosineSimilarity:
    def test_identical_vectors_score_100(self):
        v = [1.0, 0.0, 0.0, 0.5]
        score = cosine_similarity_score(v, v)
        assert abs(score - 100.0) < 0.01

    def test_orthogonal_vectors_score_zero(self):
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        score = cosine_similarity_score(a, b)
        assert score < 1.0

    def test_score_in_range(self):
        import random
        random.seed(42)
        a = [random.random() for _ in range(384)]
        b = [random.random() for _ in range(384)]
        score = cosine_similarity_score(a, b)
        assert 0.0 <= score <= 100.0


class TestExtractSkillsFromText:
    def test_finds_tech_skills(self):
        text = "Experience with Python, Flask, and PostgreSQL required."
        skills = extract_skills_from_text(text)
        assert "python" in skills
        assert "flask" in skills
        assert "postgresql" in skills

    def test_returns_set(self):
        text = "python python python"
        result = extract_skills_from_text(text)
        assert isinstance(result, set)
        assert len(result) == 1


class TestComputeMatch:
    def test_returns_required_keys(self):
        # Use short texts to avoid loading the full model in tests
        # Mock the embedding
        import unittest.mock as mock
        fake_emb = [0.1] * 384

        with mock.patch("backend.services.semantic_matcher.get_model") as mock_model:
            mock_instance = mock.MagicMock()
            mock_instance.encode.return_value = fake_emb
            mock_model.return_value = mock_instance

            result = compute_match(
                resume_text="Python developer with Flask experience",
                resume_embedding=fake_emb,
                job_description="Looking for Python Flask developer",
                job_index=0,
            )

        assert "index" in result
        assert "score" in result
        assert "matched_skills" in result
        assert "skill_gaps" in result
        assert result["index"] == 0
        assert 0 <= result["score"] <= 100


class TestRankJobs:
    def test_returns_sorted_by_score(self):
        import unittest.mock as mock

        fake_emb = [0.1] * 384
        jobs = [
            {"title": "Job A", "description": "python developer"},
            {"title": "Job B", "description": "java developer"},
            {"title": "Job C", "description": "python flask react developer"},
        ]

        with mock.patch("backend.services.semantic_matcher.get_model") as mock_model:
            mock_instance = mock.MagicMock()
            # Return slightly different embeddings to get different scores
            ]
            ranked = rank_jobs(
                resume_text="Python developer",
                resume_embedding=fake_emb,
                jobs=jobs,
            )

        assert len(ranked) == 3
        scores = [j["match_score"] for j in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_empty_jobs_returns_empty(self):
        result = rank_jobs("some text", [0.1] * 384, [])
        assert result == []
