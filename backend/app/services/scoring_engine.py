"""
Feature 2.2 & Feature 2.3: Mathematical Scoring Formula & Deterministic Explainable AI (XAI)
Reasoning Generator (scoring_engine.py)

Implements the exact normalized sub-scores on a 0-100 scale:
1. Skill Alignment Score ($S_{\\text{skill}}$):
   $$S_{\\text{skill}} = \\left( \\frac{|\\text{Matched}| + \\sum (\\text{Partial Credit})}{|\\text{JD Required Skills}|} \\right) \\times 100$$
2. Semantic Experience & Project Relevance ($S_{\\text{semantic}}$):
   Linearly rescales MiniLM cosine similarity (where 0.30 is unrelated and 0.80 is exceptional)
   onto a 0-100 scale.
3. Quantitative Experience Score ($S_{\\text{exp}}$):
   - If $\\text{JD\\_Min\\_Years} == 0$: $S_{\\text{exp}} = 100$
   - Else if $\\text{Cand\\_Years} \\ge \\text{JD\\_Min\\_Years}$: $S_{\\text{exp}} = 100$
   - Else: $S_{\\text{exp}} = (\\text{Cand\\_Years} / \\text{JD\\_Min\\_Years}) \\times 100$

Composite Overall Score (0-100):
   $$\\text{Overall Score} = \\text{round}((W_s \\cdot S_{\\text{skill}}) + (W_c \\cdot S_{\\text{semantic}}) + (W_e \\cdot S_{\\text{exp}}), 1)$$
   Default weights: $W_s = 0.50, W_c = 0.30, W_e = 0.20$.

Also generates 4-5 deterministic, human-readable analytical XAI bullets quantifying exact
point contributions for the recruiter dashboard.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.config import settings
from app.services.semantic_engine import (
    SkillAlignmentResult,
    compute_section_semantic_similarity,
    evaluate_skill_alignment,
    SemanticEngine,
)


@dataclass
class CandidateScoringResult:
    """Complete deterministic scoring + XAI output for a single candidate evaluation."""

    overall_score: float
    skill_score: float
    semantic_score: float
    experience_score: float
    raw_semantic_cosine: float
    candidate_experience_years: float
    jd_min_experience_years: float
    matched_skills: list[str] = field(default_factory=list)
    partial_skills: list[dict[str, Any]] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    explanations: list[str] = field(default_factory=list)
    weights_used: dict[str, float] = field(default_factory=dict)
    hidden_text_detected: bool = False
    integrity_score: float = 100.0

    # Role: Serializes candidate scoring results into an output dictionary.
    # Workflow: Formats sub-scores, overall scores, skill lists, and explanations into a dictionary for API delivery.
    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_score": round(self.overall_score, 1),
            "skill_score": round(self.skill_score, 1),
            "semantic_score": round(self.semantic_score, 1),
            "experience_score": round(self.experience_score, 1),
            "raw_semantic_cosine": round(self.raw_semantic_cosine, 4),
            "candidate_experience_years": round(self.candidate_experience_years, 1),
            "jd_min_experience_years": round(self.jd_min_experience_years, 1),
            "matched_skills": self.matched_skills,
            "partial_skills": self.partial_skills,
            "missing_skills": self.missing_skills,
            "explanations": self.explanations,
            "weights_used": self.weights_used,
            "hidden_text_detected": self.hidden_text_detected,
            "integrity_score": round(self.integrity_score, 1),
        }


# Role: Computes the 0 to 100 skill alignment score from exact and partial matches.
# Workflow: Checks required skill count, sums exact match count and partial credits, computes the ratio against total requirements, and bounds the score between 0.0 and 100.0.
def compute_skill_subscore(alignment: SkillAlignmentResult) -> float:
    """
    Calculates $S_{\\text{skill}}$ on a 0-100 scale:
    $$S_{\\text{skill}} = \\left( \\frac{|\\text{Matched}| + \\sum (\\text{Partial Credit})}{|\\text{JD Required Skills}|} \\right) \\times 100$$
    """
    total_req = alignment.total_required_count
    if total_req <= 0:
        return 100.0

    numerator = float(len(alignment.matched_skills)) + float(alignment.total_partial_credit)
    score = (numerator / float(total_req)) * 100.0
    return round(min(100.0, max(0.0, score)), 1)


# Role: Computes the 0 to 100 quantitative experience score based on required tenure.
# Workflow: Awards full 100 points if no minimum experience is required or if candidate tenure meets or exceeds the threshold, or calculates proportional percentage otherwise.
def compute_experience_subscore(candidate_years: float, jd_min_years: float) -> float:
    """
    Calculates $S_{\\text{exp}}$ on a 0-100 scale:
    - If $\\text{JD\\_Min\\_Years} == 0$: $S_{\\text{exp}} = 100$
    - Else if $\\text{Cand\\_Years} \\ge \\text{JD\\_Min\\_Years}$: $S_{\\text{exp}} = 100$
    - Else: $S_{\\text{exp}} = (\\text{Cand\\_Years} / \\text{JD\\_Min\\_Years}) \\times 100$
    """
    if jd_min_years <= 0.0:
        return 100.0
    if candidate_years >= jd_min_years:
        return 100.0
    score = (max(0.0, candidate_years) / jd_min_years) * 100.0
    return round(min(100.0, max(0.0, score)), 1)


# Role: Produces natural language explainable AI bullets detailing point contributions.
# Workflow: Constructs human-readable explanation strings for skill strength, semantic bridging credit, tenure comparison, domain context relevance, and critical gaps.
def generate_score_explanations(result: CandidateScoringResult) -> list[str]:
    """
    Feature 2.3: Deterministic Explainable AI (XAI) Reasoning Generator.
    Outputs 4-5 concrete, human-readable analytical bullets explaining why the candidate
    received their exact score with exact point attributions.
    """
    explanations: list[str] = []

    w_s = result.weights_used.get("skills", settings.DEFAULT_WEIGHT_SKILLS)
    w_c = result.weights_used.get("semantic", settings.DEFAULT_WEIGHT_SEMANTIC)
    w_e = result.weights_used.get("experience", settings.DEFAULT_WEIGHT_EXPERIENCE)

    total_jd_skills = (
        len(result.matched_skills)
        + len(result.partial_skills)
        + len(result.missing_skills)
    )
    denom = max(total_jd_skills, 1)

    # 1. Skill Strength Bullet (Exact Matches)
    exact_count = len(result.matched_skills)
    exact_pts = round((exact_count / denom) * 100.0 * w_s, 1)
    if exact_count > 0:
        skill_list_str = ", ".join(result.matched_skills[:8])
        if exact_count > 8:
            skill_list_str += f", +{exact_count - 8} more"
        explanations.append(
            f"Skill Strength: Matched {exact_count} of {total_jd_skills} core required skills directly "
            f"({skill_list_str}), contributing +{exact_pts:.1f} pts to the total score."
        )
    else:
        explanations.append(
            f"Skill Strength: Matched 0 of {total_jd_skills} core required skills directly (+0.0 pts from exact keyword matches)."
        )

    # 2. Semantic Bridging Bullet (Partial / Soft Credit Matches)
    if result.partial_skills:
        total_partial_credit = sum(
            float(p.get("credit_awarded", 0.6 * float(p.get("similarity", 0.0))))
            for p in result.partial_skills
        )
        partial_pts = round((total_partial_credit / denom) * 100.0 * w_s, 1)
        top_partials = result.partial_skills[:3]
        bridge_phrases = [
            f"lacks '{p['required']}' explicitly but demonstrates '{p['candidate_has']}' ({int(round(float(p['similarity']) * 100))}% semantic similarity)"
            for p in top_partials
        ]
        explanations.append(
            f"Semantic Bridging: Awarded +{partial_pts:.1f} pts partial semantic credit: Candidate "
            + "; ".join(bridge_phrases)
            + "."
        )
    else:
        explanations.append(
            "Semantic Bridging: No partial/adjacent skill substitutions required (+0.0 pts soft credit; all detected skills evaluated via direct canonical matching)."
        )

    # 3. Experience Verdict Bullet
    exp_pts = round(result.experience_score * w_e, 1)
    cand_yrs = result.candidate_experience_years
    req_yrs = result.jd_min_experience_years
    if req_yrs <= 0:
        explanations.append(
            f"Experience Verdict: Candidate brings {cand_yrs:.1f} years of non-overlapping professional experience (no minimum year threshold specified by JD, contributing +{exp_pts:.1f} pts)."
        )
    elif cand_yrs >= req_yrs:
        explanations.append(
            f"Experience Verdict: Candidate has {cand_yrs:.1f} years of non-overlapping professional experience, "
            f"exceeding the {req_yrs:.1f}-year minimum requirement (+{exp_pts:.1f} pts)."
        )
    else:
        deficit = round(req_yrs - cand_yrs, 1)
        explanations.append(
            f"Experience Verdict: Candidate has {cand_yrs:.1f} years of non-overlapping professional experience, "
            f"which is {deficit:.1f} years below the {req_yrs:.1f}-year benchmark ({result.experience_score:.1f}% fulfillment, +{exp_pts:.1f} pts)."
        )

    # 4. Domain Context Bullet
    sem_pts = round(result.semantic_score * w_c, 1)
    sem_pct = int(round(result.semantic_score))
    tier_label = (
        "High"
        if sem_pct >= 75
        else ("Moderate" if sem_pct >= 50 else "Low")
    )
    explanations.append(
        f"Domain Context: {tier_label} semantic alignment ({sem_pct}%) between candidate's work history/projects and JD responsibilities (+{sem_pts:.1f} pts)."
    )

    # 5. Critical Gaps & Integrity Verdict Bullet
    if result.missing_skills:
        missing_count = len(result.missing_skills)
        quoted_missing = ", ".join(f"'{s}'" for s in result.missing_skills[:6])
        if missing_count > 6:
            quoted_missing += f" (+{missing_count - 6} more)"
        noun = "requirement" if missing_count == 1 else "requirements"
        gap_bullet = f"Critical Gaps: Missing {missing_count} mandatory {noun}: {quoted_missing}."
    else:
        gap_bullet = "Critical Gaps: Zero missing mandatory skills — candidate covers 100% of required technical competencies directly or via semantic adjacency."

    if result.hidden_text_detected:
        gap_bullet += (
            f" [INTEGRITY ALERT: Hidden white/microscopic text detected; document integrity score reduced to {result.integrity_score:.0f}%]."
        )
    explanations.append(gap_bullet)

    return explanations


# Role: Orchestrates multi-vector candidate scoring across skills, semantics, and experience.
# Workflow: Invokes skill alignment and section semantic similarity from the semantic engine, calculates normalized sub-scores, combines them via user-calibrated weights, generates explanation bullets, and returns a CandidateScoringResult.
def calculate_candidate_scores(
    jd_required_skills: list[str],
    jd_min_experience_years: float,
    jd_context_text: str,
    candidate_skills: list[str],
    candidate_experience_years: float,
    candidate_experience_and_projects_text: str,
    weights: dict[str, float] | None = None,
    hidden_text_detected: bool = False,
    integrity_score: float = 100.0,
) -> CandidateScoringResult:
    """
    End-to-end Phase 2 orchestrator computing:
    - Multi-vector skill alignment (Exact + Semantic Adjacent + Implicit Context + Missing)
    - Normalized sub-scores ($S_{\\text{skill}}, S_{\\text{semantic}}, S_{\\text{exp}}$)
    - Weighted composite score ($0-100$)
    - Deterministic XAI explanation bullets
    """
    w_s = (weights or {}).get("skills", settings.DEFAULT_WEIGHT_SKILLS)
    w_c = (weights or {}).get("semantic", settings.DEFAULT_WEIGHT_SEMANTIC)
    w_e = (weights or {}).get("experience", settings.DEFAULT_WEIGHT_EXPERIENCE)

    # Normalize weights if user sliders don't sum to 1.0
    total_w = w_s + w_c + w_e
    if total_w <= 0:
        w_s, w_c, w_e = (
            settings.DEFAULT_WEIGHT_SKILLS,
            settings.DEFAULT_WEIGHT_SEMANTIC,
            settings.DEFAULT_WEIGHT_EXPERIENCE,
        )
    else:
        w_s, w_c, w_e = w_s / total_w, w_c / total_w, w_e / total_w

    normalized_weights = {
        "skills": round(w_s, 4),
        "semantic": round(w_c, 4),
        "experience": round(w_e, 4),
    }

    resume_chunks = SemanticEngine.split_into_sentence_chunks(
        candidate_experience_and_projects_text
    )
    alignment = evaluate_skill_alignment(
        jd_skills=jd_required_skills,
        candidate_skills=candidate_skills,
        resume_chunks=resume_chunks,
    )

    skill_score = compute_skill_subscore(alignment)
    raw_cos, semantic_score = compute_section_semantic_similarity(
        jd_text=jd_context_text,
        candidate_experience_and_projects_text=candidate_experience_and_projects_text,
    )
    experience_score = compute_experience_subscore(
        candidate_years=candidate_experience_years,
        jd_min_years=jd_min_experience_years,
    )

    overall_score = round(
        (w_s * skill_score) + (w_c * semantic_score) + (w_e * experience_score),
        1,
    )

    result = CandidateScoringResult(
        overall_score=overall_score,
        skill_score=skill_score,
        semantic_score=semantic_score,
        experience_score=experience_score,
        raw_semantic_cosine=raw_cos,
        candidate_experience_years=round(candidate_experience_years, 1),
        jd_min_experience_years=round(jd_min_experience_years, 1),
        matched_skills=alignment.matched_skills,
        partial_skills=alignment.partial_skills,
        missing_skills=alignment.missing_skills,
        explanations=[],
        weights_used=normalized_weights,
        hidden_text_detected=hidden_text_detected,
        integrity_score=integrity_score,
    )
    result.explanations = generate_score_explanations(result)
    return result
