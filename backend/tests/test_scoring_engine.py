import pytest
from app.services.scoring_engine import (
    calculate_candidate_scores,
    compute_skill_subscore,
    compute_experience_subscore,
    generate_score_explanations,
    CandidateScoringResult,
)
from app.services.semantic_engine import SkillAlignmentResult


class TestScoringEngine:
    """Tests for normalized sub-scores, mathematical composite formula, and deterministic XAI."""

    def test_compute_skill_subscore(self):
        # 4 required, 2 exact matches, 0 partial credit
        align1 = SkillAlignmentResult(
            matched_skills=["Python", "FastAPI"],
            partial_skills=[],
            missing_skills=["Docker", "React"],
            total_partial_credit=0.0,
            total_required_count=4,
        )
        assert compute_skill_subscore(align1) == 50.0

        # 4 required, 2 exact + 1.0 partial credit = 3.0 / 4.0 = 75.0%
        align2 = SkillAlignmentResult(
            matched_skills=["Python", "FastAPI"],
            partial_skills=[{"required": "Docker", "candidate_has": "Kubernetes", "similarity": 0.85}],
            missing_skills=["React"],
            total_partial_credit=1.0,
            total_required_count=4,
        )
        assert compute_skill_subscore(align2) == 75.0

    def test_compute_experience_subscore(self):
        # Required: 4.0 years
        # Candidate 5.0 years -> 100.0%
        assert compute_experience_subscore(candidate_years=5.0, jd_min_years=4.0) == 100.0
        # Candidate 4.0 years -> 100.0%
        assert compute_experience_subscore(candidate_years=4.0, jd_min_years=4.0) == 100.0
        # Candidate 2.0 years -> (2.0 / 4.0) * 100 = 50.0%
        assert compute_experience_subscore(candidate_years=2.0, jd_min_years=4.0) == 50.0
        # If JD has 0 required years -> 100.0%
        assert compute_experience_subscore(candidate_years=1.0, jd_min_years=0.0) == 100.0

    def test_calculate_candidate_scores_formula(self):
        jd_skills = ["Python", "FastAPI", "React", "PostgreSQL"]
        cand_skills = ["Python", "FastAPI", "React", "PostgreSQL"]

        result = calculate_candidate_scores(
            jd_required_skills=jd_skills,
            jd_min_experience_years=4.0,
            jd_context_text="Build async web backend applications in Python and FastAPI.",
            candidate_skills=cand_skills,
            candidate_experience_years=5.0,
            candidate_experience_and_projects_text="Developed Python and FastAPI backend services with high concurrency.",
            weights={"skills": 0.50, "semantic": 0.30, "experience": 0.20},
        )

        assert isinstance(result, CandidateScoringResult)
        assert result.skill_score == 100.0
        assert result.experience_score == 100.0
        assert result.overall_score >= 80.0
        assert len(result.explanations) >= 4

    def test_deterministic_xai_explanations(self):
        result = CandidateScoringResult(
            overall_score=78.5,
            skill_score=80.0,
            semantic_score=70.0,
            experience_score=100.0,
            raw_semantic_cosine=0.65,
            candidate_experience_years=5.0,
            jd_min_experience_years=4.0,
            matched_skills=["Python", "FastAPI", "React"],
            partial_skills=[{"required": "Docker", "candidate_has": "Kubernetes", "similarity": 0.82}],
            missing_skills=["PostgreSQL"],
            explanations=[],
            weights_used={"skills": 0.50, "semantic": 0.30, "experience": 0.20},
        )

        explanations = generate_score_explanations(result)
        assert len(explanations) >= 4

        # Verify point attribution formatting
        assert any("Skill Strength:" in b and "pts" in b for b in explanations)
        assert any("Experience Verdict:" in b and "pts" in b for b in explanations)
        assert any("Domain Context:" in b and "pts" in b for b in explanations)
        assert any("Critical Gaps:" in b for b in explanations)

    def test_hidden_text_integrity_penalty(self):
        result = calculate_candidate_scores(
            jd_required_skills=["Python"],
            jd_min_experience_years=2.0,
            jd_context_text="Python programming",
            candidate_skills=["Python"],
            candidate_experience_years=3.0,
            candidate_experience_and_projects_text="Python",
            hidden_text_detected=True,
            integrity_score=65.0,
        )

        assert result.hidden_text_detected is True
        assert result.integrity_score == 65.0
        assert any("INTEGRITY ALERT" in b for b in result.explanations)
