"""
PHASE 3: Module 1 Job Description Router (backend/app/routers/jd_router.py)

Implements:
1. `POST /api/jd/parse`:
   Accepts either raw JD text (via form field or JSON body) or an uploaded PDF/DOCX/TXT
   Job Description file. Extracts job title, canonical `required_skills`,
   `min_experience_years`, and `education_reqs`. Persists to PostgreSQL and returns
   the structured `JobDescriptionResponse`.
2. `PUT /api/jd/{jd_id}/skills`:
   Allows the recruiter on the frontend (`JDInputPanel.jsx`) to add/remove extracted
   JD skill chips or adjust minimum required experience years. Automatically re-evaluates
   any candidates already uploaded against this JD so the ranking table stays synchronized.
3. `GET /api/jd` & `GET /api/jd/{jd_id}`:
   Lists recent JDs or fetches a specific JD benchmark.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Request, UploadFile, status

from app.database import get_db
from app.models import (
    JobDescription,
    db_delete_jd,
    db_get_evaluations_for_jd,
    db_get_jd_by_id,
    db_list_jds,
    db_update_jd_benchmark,
)
from app.schemas import JDSkillsUpdateRequest, JobDescriptionResponse
from app.services.document_parser import extract_document
from app.services.entity_extractor import (
    EntityExtractionService,
    extract_jd_min_experience_years,
    extract_skills,
)
from app.services.scoring_engine import calculate_candidate_scores
from app.services.section_segmenter import segment_job_description

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/jd", tags=["Module 1: Job Description Ingestion"])


@router.post(
    "/parse",
    response_model=JobDescriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Parse and persist a Job Description from raw text or uploaded PDF/DOCX file",
)
async def parse_job_description(
    request: Request,
    file: UploadFile | None = File(default=None),
    raw_text: str | None = Form(default=None),
    title: str | None = Form(default=None),
    min_experience_years: float | None = Form(default=None),
    skills: str | None = Form(default=None),
    db: Any = Depends(get_db),
) -> JobDescriptionResponse:
    """
    Module 1 Endpoint (`POST /api/jd/parse`):
    Supports both `multipart/form-data` (file upload or `raw_text` form field)
    and `application/json` (`{"raw_text": "...", "title": "...", "min_experience_years": 4.0}`).
    """
    extracted_text = ""
    explicit_title = title
    explicit_min_years = min_experience_years
    explicit_skills: list[str] = []

    if skills:
        try:
            import json
            parsed_sk = json.loads(skills)
            if isinstance(parsed_sk, list):
                explicit_skills = [str(s).strip() for s in parsed_sk if str(s).strip()]
        except Exception:
            explicit_skills = [s.strip() for s in skills.split(",") if s.strip()]

    # 1. Check if a file (PDF/DOCX/TXT) was uploaded via multipart/form-data
    if file is not None and file.filename:
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded Job Description file is empty.",
            )
        parsed_doc = extract_document(file_bytes=file_bytes, filename=file.filename)
        extracted_text = parsed_doc.clean_visible_text or parsed_doc.raw_text
    elif raw_text and raw_text.strip():
        extracted_text = raw_text.strip()
    else:
        # Check if client sent an application/json body instead of multipart form
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                body = await request.json()
                extracted_text = str(body.get("raw_text", "")).strip()
                if body.get("title"):
                    explicit_title = str(body["title"]).strip()
                if body.get("min_experience_years") is not None:
                    explicit_min_years = float(body["min_experience_years"])
                if body.get("skills"):
                    b_skills = body["skills"]
                    if isinstance(b_skills, list):
                        explicit_skills = [str(s).strip() for s in b_skills if str(s).strip()]
            except Exception as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid JSON payload: {exc}",
                ) from exc

    if not extracted_text or len(extracted_text.strip()) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid Job Description text (at least 10 characters) or upload a PDF/DOCX file.",
        )

    # 2. Segment JD & extract structured benchmark attributes
    jd_segments = segment_job_description(extracted_text)
    resolved_title = (
        explicit_title.strip()
        if (explicit_title and explicit_title.strip() and explicit_title.strip() != "Untitled Role")
        else jd_segments["title"]
    )
    
    if explicit_skills:
        extracted_skills = explicit_skills
    else:
        extracted_skills = extract_skills(extracted_text)

    resolved_min_years = (
        round(float(explicit_min_years), 1)
        if explicit_min_years is not None
        else extract_jd_min_experience_years(extracted_text)
    )
    education_reqs = jd_segments.get("education_reqs", [])

    jd_record = JobDescription(
        title=resolved_title,
        raw_text=extracted_text,
        required_skills=extracted_skills,
        min_experience_years=resolved_min_years,
        education_reqs=education_reqs,
    )
    db.add(jd_record)
    db.commit()
    db.refresh(jd_record)

    return JobDescriptionResponse.from_entity(jd_record)


@router.post(
    "/extract-preview",
    summary="Preview title, skills, and minimum experience extracted from raw JD text in real time",
)
async def extract_preview(request: Request) -> dict[str, Any]:
    """Provides instant auto-extraction preview for CampaignSetupView without saving to database."""
    try:
        body = await request.json()
        raw_text = str(body.get("raw_text", "")).strip()
    except Exception:
        raw_text = ""

    if not raw_text or len(raw_text) < 10:
        return {"title": "", "required_skills": [], "min_experience_years": 3.0}

    segments = segment_job_description(raw_text)
    skills = extract_skills(raw_text)
    min_years = extract_jd_min_experience_years(raw_text)

    return {
        "title": segments.get("title", ""),
        "required_skills": skills,
        "min_experience_years": min_years,
    }


@router.delete(
    "/{jd_id}",
    summary="Delete a Job Description and all associated candidate evaluation records",
)
def delete_job_description(jd_id: str, db: Any = Depends(get_db)) -> dict[str, Any]:
    success = db_delete_jd(db, jd_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job Description with id '{jd_id}' not found.",
        )
    return {"deleted": True, "jd_id": jd_id}



@router.put(
    "/{jd_id}/skills",
    response_model=JobDescriptionResponse,
    summary="Update extracted JD skill chips or minimum experience benchmark",
)
def update_jd_skills_and_benchmark(
    jd_id: str,
    payload: JDSkillsUpdateRequest = Body(...),
    db: Any = Depends(get_db),
) -> JobDescriptionResponse:
    """
    Module 1 Benchmark Customization (`PUT /api/jd/{jd_id}/skills`):
    Normalizes and deduplicates skill chips modified by the recruiter in `JDInputPanel.jsx`,
    updates `min_experience_years`, and optionally re-evaluates existing candidates for this JD.
    """
    jd = db_get_jd_by_id(db, jd_id)
    if jd is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job Description with id '{jd_id}' not found.",
        )

    entity_service = EntityExtractionService.get_instance()
    normalized_skills: list[str] = []
    for raw_skill in payload.required_skills:
        cleaned = raw_skill.strip()
        if not cleaned:
            continue
        canon = entity_service.normalize_skill_name(cleaned)
        if canon and canon not in normalized_skills:
            normalized_skills.append(canon)

    updated_jd = db_update_jd_benchmark(
        db=db,
        jd=jd,
        required_skills=normalized_skills,
        min_experience_years=payload.min_experience_years,
        title=payload.title,
    )

    # Re-score any candidates already evaluated against this JD so rankings reflect the updated benchmark
    if payload.recalculate_candidates:
        existing_evals = db_get_evaluations_for_jd(db, jd_id)
        if existing_evals:
            jd_segments = segment_job_description(updated_jd.raw_text)
            jd_context_text = f"{jd_segments['responsibilities']}\n{jd_segments['requirements']}"

            for cand in existing_evals:
                sections = cand.segmented_sections or {}
                exp_proj_text = f"{sections.get('experience', '')}\n{sections.get('projects', '')}".strip()
                if not exp_proj_text:
                    exp_proj_text = "\n".join(str(v) for v in sections.values())

                # Re-extract candidate skills from stored sections
                all_cand_text = "\n".join(str(v) for v in sections.values())
                cand_skills = extract_skills(all_cand_text)

                hidden_flag = len(cand.integrity_flags or []) > 0
                integrity_val = 60.0 if hidden_flag else 100.0

                scoring = calculate_candidate_scores(
                    jd_required_skills=updated_jd.required_skills,
                    jd_min_experience_years=updated_jd.min_experience_years,
                    jd_context_text=jd_context_text,
                    candidate_skills=cand_skills,
                    candidate_experience_years=cand.experience_years,
                    candidate_experience_and_projects_text=exp_proj_text,
                    hidden_text_detected=hidden_flag,
                    integrity_score=integrity_val,
                )

                cand.overall_score = scoring.overall_score
                cand.skill_score = scoring.skill_score
                cand.semantic_score = scoring.semantic_score
                cand.experience_score = scoring.experience_score
                cand.matched_skills = scoring.matched_skills
                cand.partial_skills = scoring.partial_skills
                cand.missing_skills = scoring.missing_skills
                cand.explanations = scoring.explanations
                db.add(cand)
            db.commit()

    return JobDescriptionResponse.from_entity(updated_jd)


@router.get(
    "",
    response_model=list[JobDescriptionResponse],
    summary="List recent Job Descriptions",
)
def list_job_descriptions(db: Any = Depends(get_db)) -> list[JobDescriptionResponse]:
    jds = db_list_jds(db, limit=25)
    return [JobDescriptionResponse.from_entity(j) for j in jds]


@router.get(
    "/{jd_id}",
    response_model=JobDescriptionResponse,
    summary="Get a specific Job Description by ID",
)
def get_job_description(jd_id: str, db: Any = Depends(get_db)) -> JobDescriptionResponse:
    jd = db_get_jd_by_id(db, jd_id)
    if jd is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job Description with id '{jd_id}' not found.",
        )
    return JobDescriptionResponse.from_entity(jd)
