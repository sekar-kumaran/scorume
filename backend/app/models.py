"""
PHASE 3: PostgreSQL ORM Models (backend/app/models.py)

Defines the two core relational tables with PostgreSQL `JSONB` columns (and automatic
`JSON` adaptation when running on SQLite in local dev):
1. `JobDescription`:
   - `id` (UUID String PK)
   - `title` (String)
   - `raw_text` (Text)
   - `required_skills` (JSONB)
   - `min_experience_years` (Float)
   - `education_reqs` (JSONB)
   - `created_at` (DateTime)
2. `CandidateEvaluation`:
   - `id` (UUID String PK)
   - `jd_id` (FK -> `job_descriptions.id`)
   - `candidate_name` (String)
   - `email` (String)
   - `phone` (String)
   - `filename` (String)
   - `experience_years` (Float)
   - `education_summary` (String)
   - `overall_score` (Float)
   - `skill_score` (Float)
   - `semantic_score` (Float)
   - `experience_score` (Float)
   - `matched_skills` (JSONB)
   - `partial_skills` (JSONB)
   - `missing_skills` (JSONB)
   - `explanations` (JSONB)
   - `segmented_sections` (JSONB)
   - `integrity_flags` (JSONB)
   - `created_at` (DateTime)
"""

from __future__ import annotations

import datetime
import json
import uuid
from typing import Any

from app.database import Base, SQLALCHEMY_AVAILABLE

if SQLALCHEMY_AVAILABLE:
    from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text
    from sqlalchemy.dialects.postgresql import JSONB
    from sqlalchemy.orm import relationship
    from sqlalchemy.types import JSON

    # Cross-dialect JSONB type: uses native PostgreSQL JSONB on Postgres and JSON on SQLite
    JSONBType = JSON().with_variant(JSONB(), "postgresql")

    class JobDescription(Base):
        """ORM model representing a parsed Job Description benchmark."""

        __tablename__ = "job_descriptions"

        id = Column(
            String(36),
            primary_key=True,
            default=lambda: str(uuid.uuid4()),
            index=True,
        )
        title = Column(String(255), nullable=False, default="Software / AI Engineer")
        raw_text = Column(Text, nullable=False)
        required_skills = Column(JSONBType, nullable=False, default=list)
        min_experience_years = Column(Float, nullable=False, default=0.0)
        education_reqs = Column(JSONBType, nullable=False, default=list)
        created_at = Column(
            DateTime(timezone=True),
            nullable=False,
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        )

        evaluations = relationship(
            "CandidateEvaluation",
            back_populates="job_description",
            cascade="all, delete-orphan",
        )

    class CandidateEvaluation(Base):
        """ORM model representing an evaluated and ranked candidate resume."""

        __tablename__ = "candidate_evaluations"

        id = Column(
            String(36),
            primary_key=True,
            default=lambda: str(uuid.uuid4()),
            index=True,
        )
        jd_id = Column(
            String(36),
            ForeignKey("job_descriptions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
        candidate_name = Column(String(255), nullable=False)
        email = Column(String(255), nullable=False, default="not_provided@candidate.local")
        phone = Column(String(100), nullable=False, default="Not Provided")
        filename = Column(String(255), nullable=False)
        experience_years = Column(Float, nullable=False, default=0.0)
        education_summary = Column(String(500), nullable=False, default="Not Specified")

        overall_score = Column(Float, nullable=False, default=0.0, index=True)
        skill_score = Column(Float, nullable=False, default=0.0)
        semantic_score = Column(Float, nullable=False, default=0.0)
        experience_score = Column(Float, nullable=False, default=0.0)

        matched_skills = Column(JSONBType, nullable=False, default=list)
        partial_skills = Column(JSONBType, nullable=False, default=list)
        missing_skills = Column(JSONBType, nullable=False, default=list)
        explanations = Column(JSONBType, nullable=False, default=list)
        segmented_sections = Column(JSONBType, nullable=False, default=dict)
        integrity_flags = Column(JSONBType, nullable=False, default=list)

        created_at = Column(
            DateTime(timezone=True),
            nullable=False,
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        )

        job_description = relationship("JobDescription", back_populates="evaluations")

else:
    # ==========================================================================
    # Dataclass-style ORM Entities for Zero-Dependency SQLite3 Fallback
    # ==========================================================================
    class JobDescription(Base):  # type: ignore[no-redef]
        """Fallback ORM model representing a parsed Job Description benchmark."""

        __tablename__ = "job_descriptions"

        def __init__(
            self,
            id: str | None = None,
            title: str = "Software / AI Engineer",
            raw_text: str = "",
            required_skills: list[str] | None = None,
            min_experience_years: float = 0.0,
            education_reqs: list[str] | None = None,
            created_at: datetime.datetime | None = None,
        ) -> None:
            self.id = id or str(uuid.uuid4())
            self.title = title
            self.raw_text = raw_text
            self.required_skills = required_skills if required_skills is not None else []
            self.min_experience_years = float(min_experience_years)
            self.education_reqs = education_reqs if education_reqs is not None else []
            self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc)

        @classmethod
        def from_row(cls, row: Any) -> JobDescription:
            created = row["created_at"]
            if isinstance(created, str):
                try:
                    created = datetime.datetime.fromisoformat(created)
                except ValueError:
                    created = datetime.datetime.now(datetime.timezone.utc)
            return cls(
                id=row["id"],
                title=row["title"],
                raw_text=row["raw_text"],
                required_skills=json.loads(row["required_skills"] or "[]"),
                min_experience_years=float(row["min_experience_years"] or 0.0),
                education_reqs=json.loads(row["education_reqs"] or "[]"),
                created_at=created,
            )

    class CandidateEvaluation(Base):  # type: ignore[no-redef]
        """Fallback ORM model representing an evaluated and ranked candidate resume."""

        __tablename__ = "candidate_evaluations"

        def __init__(
            self,
            id: str | None = None,
            jd_id: str = "",
            candidate_name: str = "Candidate",
            email: str = "not_provided@candidate.local",
            phone: str = "Not Provided",
            filename: str = "",
            experience_years: float = 0.0,
            education_summary: str = "Not Specified",
            overall_score: float = 0.0,
            skill_score: float = 0.0,
            semantic_score: float = 0.0,
            experience_score: float = 0.0,
            matched_skills: list[str] | None = None,
            partial_skills: list[dict[str, Any]] | None = None,
            missing_skills: list[str] | None = None,
            explanations: list[str] | None = None,
            segmented_sections: dict[str, str] | None = None,
            integrity_flags: list[dict[str, Any]] | None = None,
            created_at: datetime.datetime | None = None,
        ) -> None:
            self.id = id or str(uuid.uuid4())
            self.jd_id = jd_id
            self.candidate_name = candidate_name
            self.email = email
            self.phone = phone
            self.filename = filename
            self.experience_years = float(experience_years)
            self.education_summary = education_summary
            self.overall_score = float(overall_score)
            self.skill_score = float(skill_score)
            self.semantic_score = float(semantic_score)
            self.experience_score = float(experience_score)
            self.matched_skills = matched_skills if matched_skills is not None else []
            self.partial_skills = partial_skills if partial_skills is not None else []
            self.missing_skills = missing_skills if missing_skills is not None else []
            self.explanations = explanations if explanations is not None else []
            self.segmented_sections = (
                segmented_sections if segmented_sections is not None else {}
            )
            self.integrity_flags = integrity_flags if integrity_flags is not None else []
            self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc)

        @classmethod
        def from_row(cls, row: Any) -> CandidateEvaluation:
            created = row["created_at"]
            if isinstance(created, str):
                try:
                    created = datetime.datetime.fromisoformat(created)
                except ValueError:
                    created = datetime.datetime.now(datetime.timezone.utc)
            return cls(
                id=row["id"],
                jd_id=row["jd_id"],
                candidate_name=row["candidate_name"],
                email=row["email"],
                phone=row["phone"],
                filename=row["filename"],
                experience_years=float(row["experience_years"] or 0.0),
                education_summary=row["education_summary"],
                overall_score=float(row["overall_score"] or 0.0),
                skill_score=float(row["skill_score"] or 0.0),
                semantic_score=float(row["semantic_score"] or 0.0),
                experience_score=float(row["experience_score"] or 0.0),
                matched_skills=json.loads(row["matched_skills"] or "[]"),
                partial_skills=json.loads(row["partial_skills"] or "[]"),
                missing_skills=json.loads(row["missing_skills"] or "[]"),
                explanations=json.loads(row["explanations"] or "[]"),
                segmented_sections=json.loads(row["segmented_sections"] or "{}"),
                integrity_flags=json.loads(row["integrity_flags"] or "[]"),
                created_at=created,
            )


# ==============================================================================
# Unified Repository Query Helpers (work identically on SQLAlchemy & Fallback)
# ==============================================================================
def db_get_jd_by_id(db: Any, jd_id: str) -> JobDescription | None:
    if SQLALCHEMY_AVAILABLE:
        return db.query(JobDescription).filter(JobDescription.id == jd_id).first()
    cur = db.conn.execute("SELECT * FROM job_descriptions WHERE id = ?", (str(jd_id),))
    row = cur.fetchone()
    return JobDescription.from_row(row) if row else None


def db_list_jds(db: Any, limit: int = 20) -> list[JobDescription]:
    if SQLALCHEMY_AVAILABLE:
        return (
            db.query(JobDescription)
            .order_by(JobDescription.created_at.desc())
            .limit(limit)
            .all()
        )
    cur = db.conn.execute(
        "SELECT * FROM job_descriptions ORDER BY created_at DESC LIMIT ?", (limit,)
    )
    return [JobDescription.from_row(r) for r in cur.fetchall()]


def db_update_jd_benchmark(
    db: Any,
    jd: JobDescription,
    required_skills: list[str],
    min_experience_years: float | None = None,
    title: str | None = None,
) -> JobDescription:
    jd.required_skills = required_skills
    if min_experience_years is not None:
        jd.min_experience_years = float(min_experience_years)
    if title is not None and title.strip():
        jd.title = title.strip()

    if SQLALCHEMY_AVAILABLE:
        db.add(jd)
        db.commit()
        db.refresh(jd)
        return jd

    db.add(jd)
    db.commit()
    return jd


def db_get_evaluations_for_jd(db: Any, jd_id: str) -> list[CandidateEvaluation]:
    if SQLALCHEMY_AVAILABLE:
        return (
            db.query(CandidateEvaluation)
            .filter(CandidateEvaluation.jd_id == jd_id)
            .order_by(CandidateEvaluation.overall_score.desc())
            .all()
        )
    cur = db.conn.execute(
        "SELECT * FROM candidate_evaluations WHERE jd_id = ? ORDER BY overall_score DESC",
        (str(jd_id),),
    )
    return [CandidateEvaluation.from_row(r) for r in cur.fetchall()]


def db_delete_evaluations_for_jd(db: Any, jd_id: str, filenames: list[str] | None = None) -> None:
    """Removes prior evaluation rows for the same filename(s) on re-upload to avoid duplicates."""
    if SQLALCHEMY_AVAILABLE:
        query = db.query(CandidateEvaluation).filter(CandidateEvaluation.jd_id == jd_id)
        if filenames:
            query = query.filter(CandidateEvaluation.filename.in_(filenames))
        query.delete(synchronize_session=False)
        db.commit()
        return

    with db.conn:
        if filenames:
            placeholders = ",".join("?" for _ in filenames)
            db.conn.execute(
                f"DELETE FROM candidate_evaluations WHERE jd_id = ? AND filename IN ({placeholders})",
                [str(jd_id), *filenames],
            )
        else:
            db.conn.execute(
                "DELETE FROM candidate_evaluations WHERE jd_id = ?",
                (str(jd_id),),
            )


def db_get_candidate_evaluation_by_id(
    db: Any, evaluation_id: str
) -> CandidateEvaluation | None:
    if SQLALCHEMY_AVAILABLE:
        return (
            db.query(CandidateEvaluation)
            .filter(CandidateEvaluation.id == evaluation_id)
            .first()
        )
    cur = db.conn.execute(
        "SELECT * FROM candidate_evaluations WHERE id = ?", (str(evaluation_id),)
    )
    row = cur.fetchone()
    return CandidateEvaluation.from_row(row) if row else None


def db_get_all_evaluations(db: Any, limit: int = 500) -> list[CandidateEvaluation]:
    """Fetches all candidate evaluations across all JDs, ordered by creation date descending."""
    if SQLALCHEMY_AVAILABLE:
        return (
            db.query(CandidateEvaluation)
            .order_by(CandidateEvaluation.created_at.desc())
            .limit(limit)
            .all()
        )
    cur = db.conn.execute(
        "SELECT * FROM candidate_evaluations ORDER BY created_at DESC LIMIT ?", (limit,)
    )
    return [CandidateEvaluation.from_row(r) for r in cur.fetchall()]


def db_delete_jd(db: Any, jd_id: str) -> bool:
    """Deletes a Job Description and all associated CandidateEvaluation records."""
    db_delete_evaluations_for_jd(db, jd_id=jd_id)
    if SQLALCHEMY_AVAILABLE:
        jd = db.query(JobDescription).filter(JobDescription.id == jd_id).first()
        if jd:
            db.delete(jd)
            db.commit()
            return True
        return False
    with db.conn:
        cur = db.conn.execute("DELETE FROM job_descriptions WHERE id = ?", (str(jd_id),))
        return cur.rowcount > 0


def db_purge_all_data(db: Any) -> dict[str, int]:
    """Purges all Job Descriptions and Candidate Evaluations for a completely clean slate."""
    if SQLALCHEMY_AVAILABLE:
        c_count = db.query(CandidateEvaluation).delete(synchronize_session=False)
        j_count = db.query(JobDescription).delete(synchronize_session=False)
        db.commit()
        return {"jds_deleted": j_count, "evaluations_deleted": c_count}
    with db.conn:
        c_count = db.conn.execute("DELETE FROM candidate_evaluations").rowcount
        j_count = db.conn.execute("DELETE FROM job_descriptions").rowcount
        return {"jds_deleted": j_count, "evaluations_deleted": c_count}


