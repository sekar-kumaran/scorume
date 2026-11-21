"""
Phase 1 & Phase 2 NLP and Explainable Scoring Services Package.
"""

from .document_parser import ParsedDocument, HiddenSpanFlag, extract_document
from .section_segmenter import segment_resume, segment_job_description
from .entity_extractor import (
    EntityExtractionService,
    extract_skills,
    calculate_experience_years,
    extract_jd_min_experience_years,
    extract_contact_metadata,
    extract_education_summary,
)
from .semantic_engine import (
    SemanticEngine,
    SkillAlignmentResult,
    PartialSkillMatch,
    evaluate_skill_alignment,
    compute_section_semantic_similarity,
)
from .scoring_engine import (
    CandidateScoringResult,
    calculate_candidate_scores,
    generate_score_explanations,
)

__all__ = [
    "ParsedDocument",
    "HiddenSpanFlag",
    "extract_document",
    "segment_resume",
    "segment_job_description",
    "EntityExtractionService",
    "extract_skills",
    "calculate_experience_years",
    "extract_jd_min_experience_years",
    "extract_contact_metadata",
    "extract_education_summary",
    "SemanticEngine",
    "SkillAlignmentResult",
    "PartialSkillMatch",
    "evaluate_skill_alignment",
    "compute_section_semantic_similarity",
    "CandidateScoringResult",
    "calculate_candidate_scores",
    "generate_score_explanations",
]
