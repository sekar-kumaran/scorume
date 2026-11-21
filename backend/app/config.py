"""
Application Configuration & Thresholds for AI-Based Resume Matching Engine.
Manages environment variables, local NLP model identifiers, semantic thresholds,
and default multi-vector scoring weights.
"""

import os
from pathlib import Path
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseModel):
    """Global application configuration loaded from environment or defaults."""

    # --- Application Metadata ---
    APP_NAME: str = "Scorume (evaluation engine)"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")

    # --- PostgreSQL Database Configuration ---
    DATABASE_URL: str = Field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg2://postgres:postgres@postgres:5432/scorume",
        )
    )
    SQLITE_FALLBACK_URL: str = Field(
        default_factory=lambda: os.getenv(
            "SQLITE_FALLBACK_URL",
            "sqlite:///./scorume_local.db",
        )
    )
    USE_SQLITE_FALLBACK: bool = Field(
        default_factory=lambda: os.getenv("USE_SQLITE_FALLBACK", "false").lower() == "true"
    )

    # --- Local NLP & Embedding Models (Zero External API Keys) ---
    EMBEDDING_MODEL_NAME: str = os.getenv(
        "EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"
    )
    SPACY_MODEL_NAME: str = os.getenv("SPACY_MODEL_NAME", "en_core_web_sm")
    SKILLS_TAXONOMY_PATH: Path = BASE_DIR / "data" / "skills_taxonomy.json"

    # --- Document Integrity & White-Text Detection Thresholds ---
    MIN_VISIBLE_FONT_SIZE: float = 2.0
    WHITE_COLOR_INT_THRESHOLD: int = 16777215  # #FFFFFF in PyMuPDF sRGB int
    NEAR_WHITE_RGB_MIN: int = 248  # R, G, B >= 248 treated as near-white hidden text
    HIDDEN_TEXT_INTEGRITY_PENALTY: float = 35.0

    # --- Multi-Vector Semantic Similarity Thresholds ---
    EXACT_MATCH_THRESHOLD: float = 0.95
    SEMANTIC_ADJACENT_THRESHOLD: float = 0.72
    IMPLICIT_CONTEXT_THRESHOLD: float = 0.68
    PARTIAL_CREDIT_MULTIPLIER: float = 0.60

    # --- MiniLM Cosine Rescaling Bounds (Feature 2.2) ---
    SEMANTIC_MIN_BASELINE: float = 0.30
    SEMANTIC_MAX_CEILING: float = 0.80

    # --- Default Composite Scoring Weights (Must sum to 1.0) ---
    DEFAULT_WEIGHT_SKILLS: float = 0.50
    DEFAULT_WEIGHT_SEMANTIC: float = 0.30
    DEFAULT_WEIGHT_EXPERIENCE: float = 0.20


settings = Settings()
