"""
PHASE 3: FastAPI Application Entry Point (backend/app/main.py)

Configures:
- Lifespan startup initialization for PostgreSQL / SQLite schema creation and singleton
  pre-warming of the local `EntityExtractionService` (spaCy + 303-skill taxonomy) and
  `SemanticEngine` (`all-MiniLM-L6-v2` / vectorized cosine engine).
- Permissive CORS middleware for the Vite React 18 frontend (`http://localhost:5173`, `http://localhost:3000`).
- Module 1 (`jd_router`) and Modules 2-5 (`evaluation_router`) REST API routers.
- One-click Demo Seed endpoint (`POST /api/demo/load-sample`) and health check endpoint (`GET /api/health`).
"""

from __future__ import annotations

from contextlib import asynccontextmanager
import logging
from pathlib import Path
from typing import Any, AsyncGenerator

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import SQLALCHEMY_AVAILABLE, get_db, init_db
from app.models import (
    JobDescription,
    db_delete_evaluations_for_jd,
    db_get_evaluations_for_jd,
    db_list_jds,
)
from app.routers.evaluation_router import (
    _serialize_ranking_item,
    evaluate_single_resume_bytes,
    router as evaluation_router,
)
from app.routers.jd_router import router as jd_router
from app.schemas import BatchEvaluationResponse
from app.services.entity_extractor import (
    EntityExtractionService,
    extract_jd_min_experience_years,
    extract_skills,
)
from app.services.section_segmenter import segment_job_description
from app.services.semantic_engine import SemanticEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI lifespan hook:
    1. Creates database tables (`job_descriptions`, `candidate_evaluations`).
    2. Pre-warms `EntityExtractionService` and `SemanticEngine` singletons in a background
       thread so the server binds and begins accepting requests immediately.
    """
    logger.info("Initializing database tables...")
    init_db()
    
    import threading
    def _prewarm() -> None:
        try:
            logger.info("Pre-warming NLP singletons in background thread...")
            svc = EntityExtractionService.get_instance()
            sem = SemanticEngine.get_instance()
            logger.info(
                "Background pre-warm complete | Taxonomy: %d skills (%d aliases) | Backend: %s",
                len(svc.canonical_skills),
                len(svc.alias_to_canonical),
                sem.backend_mode,
            )
        except Exception as exc:
            logger.warning("Background NLP pre-warming notice: %s", exc)

    thread = threading.Thread(target=_prewarm, daemon=True)
    thread.start()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "100% Local AI-Based Resume Matching & Candidate Ranking Engine powered by "
        "PyMuPDF, python-docx, spaCy EntityRuler, Sentence-Transformers (all-MiniLM-L6-v2), "
        "and Explainable AI (XAI) multi-vector scoring."
    ),
    lifespan=lifespan,
)

# Enable CORS for local React (Vite) development and Docker Compose frontend container
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register core REST routers
app.include_router(jd_router)
app.include_router(evaluation_router)


@app.get("/health", tags=["System Health"])
@app.get("/api/health", tags=["System Health"])
def health_check() -> dict[str, Any]:
    """Returns operational status, active NLP model mode, and taxonomy statistics."""
    entity_svc = EntityExtractionService.get_instance()
    sem_engine = SemanticEngine.get_instance()
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database_driver": "sqlalchemy" if SQLALCHEMY_AVAILABLE else "sqlite3-fallback",
        "embedding_backend": sem_engine.backend_mode,
        "canonical_skills_count": len(entity_svc.canonical_skills),
        "total_aliases_count": len(entity_svc.alias_to_canonical),
        "default_weights": {
            "skills": settings.DEFAULT_WEIGHT_SKILLS,
            "semantic": settings.DEFAULT_WEIGHT_SEMANTIC,
            "experience": settings.DEFAULT_WEIGHT_EXPERIENCE,
        },
    }


@app.post(
    "/api/demo/load-sample",
    response_model=BatchEvaluationResponse,
    tags=["Demo & Synthetic Dataset"],
    summary="One-click loader: ingests the sample Full-Stack AI JD and all 12 synthetic PDF/DOCX resumes",
)
def load_sample_dataset(db: Any = Depends(get_db)) -> BatchEvaluationResponse:
    """
    Convenience endpoint for live interviews and instant dashboard testing:
    Automatically locates `sample_data/sample_jd_fullstack_ai.txt` and all generated
    PDF/DOCX resumes in `sample_data/resumes/`, parses the JD, evaluates the 12 resumes,
    and returns the complete ranked leaderboard.
    """
    possible_roots = [
        Path(__file__).resolve().parents[2],
        Path(__file__).resolve().parents[1],
        Path.cwd(),
        Path("/"),
    ]
    sample_jd_path = None
    sample_resumes_dir = None
    for r in possible_roots:
        candidate_jd = r / "sample_data" / "sample_jd_fullstack_ai.txt"
        candidate_resumes = r / "sample_data" / "resumes"
        if candidate_jd.exists() and candidate_resumes.exists():
            sample_jd_path = candidate_jd
            sample_resumes_dir = candidate_resumes
            break

    if not sample_jd_path or not sample_jd_path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Sample JD not found in candidate paths. "
                "Ensure sample_data/sample_jd_fullstack_ai.txt and sample_data/resumes/ exist."
            ),
        )

    jd_text = sample_jd_path.read_text(encoding="utf-8")
    jd_segments = segment_job_description(jd_text)
    jd_skills = extract_skills(jd_text)
    jd_min_years = extract_jd_min_experience_years(jd_text)

    # Check if sample JD already exists or create a fresh one
    existing_jds = db_list_jds(db, limit=10)
    jd_record = next(
        (j for j in existing_jds if j.title == jd_segments["title"]),
        None,
    )
    if jd_record is None:
        jd_record = JobDescription(
            title=jd_segments["title"],
            raw_text=jd_text,
            required_skills=jd_skills,
            min_experience_years=jd_min_years,
            education_reqs=jd_segments.get("education_reqs", []),
        )
        db.add(jd_record)
        db.commit()
        db.refresh(jd_record)

    resume_files = sorted(
        [
            p
            for p in sample_resumes_dir.iterdir()
            if p.is_file() and p.suffix.lower() in {".pdf", ".docx"}
        ]
    )
    if not resume_files:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No synthetic PDF/DOCX resumes found in {sample_resumes_dir}. "
                "Run `python3 sample_data/resumes/generate_synthetic_resumes.py` first."
            ),
        )

    db_delete_evaluations_for_jd(db, jd_id=str(jd_record.id))
    jd_context_text = f"{jd_segments['responsibilities']}\n{jd_segments['requirements']}".strip()

    for r_path in resume_files:
        eval_obj = evaluate_single_resume_bytes(
            file_bytes=r_path.read_bytes(),
            filename=r_path.name,
            jd=jd_record,
            jd_context_text=jd_context_text,
        )
        db.add(eval_obj)

    db.commit()

    all_evals = db_get_evaluations_for_jd(db, jd_id=str(jd_record.id))
    ranked_items = [
        _serialize_ranking_item(
            eval_obj=ev,
            rank=idx + 1,
            jd_min_years=float(jd_record.min_experience_years or 0.0),
        )
        for idx, ev in enumerate(all_evals)
    ]

    return BatchEvaluationResponse(
        jd_id=str(jd_record.id),
        jd_title=jd_record.title,
        jd_required_skills=list(jd_record.required_skills or []),
        jd_min_experience_years=round(float(jd_record.min_experience_years or 0.0), 1),
        total_candidates=len(ranked_items),
        candidates=ranked_items,
    )
