import numpy as np
import pytest
from app.services.semantic_engine import (
    SemanticEngine,
    vectorized_cosine_similarity,
    evaluate_skill_alignment,
    compute_section_semantic_similarity,
)


class TestSemanticEngine:
    """Tests for vector embeddings, cosine similarity, and 3-tier skill alignment."""

    def test_singleton_engine(self):
        eng1 = SemanticEngine.get_instance()
        eng2 = SemanticEngine.get_instance()
        assert eng1 is eng2
        assert eng1.backend_mode != "uninitialized"

    def test_vectorized_cosine_similarity(self):
        # Two identical normalized vectors -> cosine = 1.0
        v1 = np.array([[1.0, 0.0, 0.0]], dtype=np.float32)
        v2 = np.array([[1.0, 0.0, 0.0]], dtype=np.float32)
        sim = vectorized_cosine_similarity(v1, v2)
        assert pytest.approx(float(sim[0, 0]), 0.001) == 1.0

        # Orthogonal vectors -> cosine = 0.0
        v3 = np.array([[0.0, 1.0, 0.0]], dtype=np.float32)
        sim_ortho = vectorized_cosine_similarity(v1, v3)
        assert pytest.approx(float(sim_ortho[0, 0]), 0.001) == 0.0

    def test_encode_texts_shape(self):
        eng = SemanticEngine.get_instance()
        texts = ["Python backend developer", "React frontend user interface"]
        embeddings = eng.encode_texts(texts)

        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape[0] == 2
        # Check L2 normalization
        norms = np.linalg.norm(embeddings, axis=1)
        for n in norms:
            assert pytest.approx(float(n), 0.01) == 1.0

    def test_evaluate_skill_alignment_tiers(self):
        eng = SemanticEngine.get_instance()

        jd_skills = ["Python", "FastAPI", "React", "Docker", "Rust"]
        # Candidate has Python and React (exact), Containerization/Kubernetes (adjacent to Docker)
        cand_skills = ["Python", "React", "Kubernetes", "Django"]

        result = eng.evaluate_skill_alignment(
            jd_skills=jd_skills,
            candidate_skills=cand_skills,
            resume_chunks=["Built and deployed containerized services using Kubernetes on cloud."],
        )

        # Exact matches
        assert "Python" in result.matched_skills
        assert "React" in result.matched_skills

        # Missing skill
        assert "Rust" in result.missing_skills

        # Docker should either be matched via adjacency or recorded in partial skills
        docker_handled = ("Docker" in result.matched_skills) or any(
            p["required"] == "Docker" for p in result.partial_skills
        )
        assert docker_handled is True

    def test_compute_section_semantic_similarity_rescaling(self):
        eng = SemanticEngine.get_instance()

        jd_text = "Develop high-throughput REST APIs and machine learning inference services in Python."
        relevant_cand = "Architected Python microservices with high concurrent throughput and ML pipelines."
        unrelated_cand = "Managed retail inventory operations and warehouse product logistics."

        raw_rel, score_rel = eng.compute_section_semantic_similarity(jd_text, relevant_cand)
        raw_unrel, score_unrel = eng.compute_section_semantic_similarity(jd_text, unrelated_cand)

        # Relevant resume should have higher similarity and score than unrelated resume
        assert raw_rel > raw_unrel
        assert score_rel > score_unrel
        assert 0.0 <= score_rel <= 100.0
        assert 0.0 <= score_unrel <= 100.0
