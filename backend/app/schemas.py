"""
PHASE 3: Pydantic Request & Response Schemas (backend/app/schemas.py)

Strict validation and serialization schemas for:
- Module 1: Job Description Ingestion (`JDParseRequest`, `JDSkillsUpdateRequest`, `JobDescriptionResponse`)
- Modules 2, 3, 4: Batch Resume Evaluation & Leaderboard Ranking (`PartialSkillSchema`, `IntegrityFlagSchema`, `CandidateRankingItemSchema`, `BatchEvaluationResponse`)
- Module 5: Candidate Deep-Dive XAI Drawer (`CandidateDetailResponse`, `ManualCandidateCreateRequest`)

Supports both Pydantic v2 (`model_validate` / `model_dump` / `from_attributes=True`)
and Pydantic v1 (`from_orm` / `dict` / `orm_mode=True`).
"""

from __future__ import annotations

import datetime
from typing import Any
from pydantic import BaseModel, Field


class CompatibleBaseModel(BaseModel):
    """Base schema providing seamless compatibility across Pydantic v2 and v1."""

    class Config:
        from_attributes = True
        extra = "ignore"

    @classmethod
    def from_entity(cls, obj: Any) -> Any:
        if hasattr(cls, "model_validate"):
            return cls.model_validate(obj)
        return cls.from_orm(obj)

    def to_dict(self) -> dict[str, Any]:
        if hasattr(self, "model_dump"):
            return self.model_dump()
        return self.dict()


# ==============================================================================
# Module 1: Job Description Schemas
# ==============================================================================
class JDParseRequest(CompatibleBaseModel):
    """Optional JSON body for parsing a Job Description from raw text."""

    title: str | None = Field(
        default=None,
        description="Optional explicit job title override.",
    )
    raw_text: str = Field(
        ...,
        min_length=10,
        description="Full text of the Job Description.",
    )
    min_experience_years: float | None = Field(
        default=None,
        ge=0.0,
        le=30.0,
        description="Optional explicit minimum required experience in years.",
    )


class JDSkillsUpdateRequest(CompatibleBaseModel):
    """Payload for PUT /api/jd/{jd_id}/skills allowing recruiters to edit benchmark chips."""

    required_skills: list[str] = Field(
        ...,
        description="Updated list of required skills for the JD benchmark.",
    )
    min_experience_years: float | None = Field(
        default=None,
        ge=0.0,
        le=30.0,
        description="Optional updated minimum experience years threshold.",
    )
    title: str | None = Field(
        default=None,
        description="Optional updated job title.",
    )
    recalculate_candidates: bool = Field(
        default=True,
        description="Whether to immediately re-score any existing candidates evaluated against this JD.",
    )


class JobDescriptionResponse(CompatibleBaseModel):
    """Structured Job Description response returned by Module 1 endpoints."""

    id: str
    title: str
    raw_text: str
    required_skills: list[str] = Field(default_factory=list)
    min_experience_years: float = 0.0
    education_reqs: list[str] = Field(default_factory=list)
    created_at: datetime.datetime


# ==============================================================================
# Modules 2, 3, 4 & 5: Candidate Evaluation, Live Resume Editing & XAI Schemas
# ==============================================================================
class PartialSkillSchema(CompatibleBaseModel):
    """Represents a semantic adjacent or implicit context partial skill match."""

    required: str
    candidate_has: str
    similarity: float = Field(..., ge=0.0, le=1.0)
    credit_awarded: float | None = None
    match_type: str = "semantic_adjacent"


class IntegrityFlagSchema(CompatibleBaseModel):
    """Represents a white-text or microscopic-font adversarial stuffing flag."""

    location: str
    reason: str
    font_size: float
    color_hex: str
    snippet: str


class CandidateRankingItemSchema(CompatibleBaseModel):
    """
    Leaderboard row schema for Module 4 (`RankingTable.jsx`) and batch upload response.
    Includes all sub-scores so `WeightSlidersBar.jsx` can dynamically recalculate
    `overall_score` in real time on the client.
    """

    id: str
    jd_id: str
    rank: int = 1
    candidate_name: str
    email: str
    phone: str
    filename: str
    experience_years: float
    jd_min_experience_years: float = 0.0
    education_summary: str

    overall_score: float
    skill_score: float
    semantic_score: float
    experience_score: float

    matched_skills: list[str] = Field(default_factory=list)
    partial_skills: list[PartialSkillSchema] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    explanations: list[str] = Field(default_factory=list)

    hidden_text_detected: bool = False
    integrity_score: float = 100.0
    integrity_flags: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime.datetime


class CandidateDetailResponse(CandidateRankingItemSchema):
    """
    Full candidate deep-dive payload for Module 5 (`CandidateDrawer.jsx`),
    extending the leaderboard schema with `segmented_sections` and JD benchmark metadata.
    """

    segmented_sections: dict[str, str] = Field(default_factory=dict)
    jd_title: str = ""
    jd_required_skills: list[str] = Field(default_factory=list)


class RoleMatcherCandidateItem(CompatibleBaseModel):
    """Candidate match item for Role Matcher & Cross-Pool Candidate Finder."""

    id: str
    rank: int = 1
    score: float
    candidate_name: str
    email: str
    phone: str = ""
    experience_years: float = 0.0
    sourced_campaign: str = ""
    matched_skills: list[str] = Field(default_factory=list)
    partial_skills: list[PartialSkillSchema] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    rationale: str = ""
    verified_years_diff: str = ""


class RoleMatcherRequest(CompatibleBaseModel):
    """Payload for POST /api/evaluations/role-matcher/find-candidates."""

    role_title: str = "Senior ML Infrastructure Engineer"
    department: str = "Core Platform & AI"
    min_experience_years: float = 5.0
    required_skills: list[str] = Field(
        default_factory=lambda: [
            "Kubernetes",
            "PyTorch / Ray",
            "C++",
            "Go",
            "Distributed Training",
        ]
    )
    weight_skills: float = 0.6
    weight_semantic: float = 0.2
    weight_experience: float = 0.2
    include_all_pools: bool = True


class ReverseRoleMatchItem(CompatibleBaseModel):
    """Role fit result when matching a candidate resume against active benchmarks."""

    jd_id: str
    role_title: str
    department: str = "Engineering"
    match_score: float
    skill_score: float
    semantic_score: float
    experience_score: float
    min_experience_years: float
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    fit_tier: str = "Strong"  # Strong, Moderate, Low


class HistoryRunCandidate(CompatibleBaseModel):
    name: str
    score: float


class HistoryRunItem(CompatibleBaseModel):
    run_id: str
    jd_id: str
    title: str
    benchmark_spec: str
    department: str
    created_at: str
    files_count: int
    processed_status: str = "100% processed"
    top_candidates: list[HistoryRunCandidate] = Field(default_factory=list)
    calibrated_weights: str = "50/30/20"
    status: str = "COMPLETED"


class HistorySummary(CompatibleBaseModel):
    total_evaluations: int
    resumes_screened: int
    avg_match_yield: float
    avg_batch_latency: str


class EvaluationHistoryResponse(CompatibleBaseModel):
    summary: HistorySummary
    runs: list[HistoryRunItem]


class ManualCandidateCreateRequest(CompatibleBaseModel):
    """
    Payload for `POST /api/evaluations/{jd_id}/manual` allowing users to paste or
    type a new candidate resume directly on the site without uploading a file.
    """

    candidate_name: str | None = Field(default=None)
    email: str | None = Field(default=None)
    phone: str | None = Field(default=None)
    raw_resume_text: str = Field(
        ...,
        min_length=15,
        description="Full pasted or typed resume text.",
    )


class BatchEvaluationResponse(CompatibleBaseModel):
    """Response returned by POST /api/evaluations/{jd_id}/batch and GET /api/evaluations/{jd_id}."""

    jd_id: str
    jd_title: str
    jd_required_skills: list[str]
    jd_min_experience_years: float
    total_candidates: int
    candidates: list[CandidateRankingItemSchema]
