"""
Feature 2.1: Vector Embedding & Skill Adjacency Matrix (semantic_engine.py)

Loads `sentence-transformers/all-MiniLM-L6-v2` (via SentenceTransformers / ONNX Runtime)
as a singleton on startup for sub-second batch encoding. Includes a deterministic
NumPy sublinear TF-IDF + Taxonomy Concept Vectorizer fallback when running inside
air-gapped or minimal containers where external model weights have not yet been cached.

Implements:
- `evaluate_skill_alignment(jd_skills, candidate_skills, resume_chunks) -> SkillAlignmentResult`
  For every required skill $s_i \\in \\text{JD\\_Skills}$:
  1. Exact/Canonical Match: $s_i \\in \\text{Candidate\\_Skills} \\implies \\text{score} = 1.0$.
  2. Semantic Adjacent Match (Soft Credit): Computes vectorized cosine similarity matrix
     between $E(s_i)$ and all candidate skill embeddings $E(c_j)$ combined with curated
     domain adjacency priors. If $0.72 \\le m < 0.95$, awards $0.6 \\times m$ partial
     credit and records `{"required": s_i, "candidate_has": c_best, "similarity": round(m, 2)}`.
  3. Implicit Context Check: If still unmatched, checks similarity against sentence chunks
     in the candidate's experience and projects sections.
  4. Missing Skill: If $< 0.72$, classifies in `missing_skills` (score = 0.0).
"""

from __future__ import annotations

import logging
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from app.config import settings
from app.services.entity_extractor import EntityExtractionService

logger = logging.getLogger(__name__)

# Optional SentenceTransformers & scikit-learn imports with NumPy vectorized fallbacks
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None  # type: ignore[assignment]

try:
    from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine_similarity
except ImportError:
    sklearn_cosine_similarity = None  # type: ignore[assignment]


STOP_WORDS: set[str] = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have",
    "in", "is", "it", "its", "of", "on", "or", "that", "the", "to", "was", "were",
    "will", "with", "we", "you", "our", "your", "their", "this", "these", "those",
    "using", "built", "build", "design", "designed", "developed", "deploy", "deployed",
    "role", "work", "working", "team", "experience", "years", "year", "minimum",
    "required", "requirements", "responsibilities", "job", "title", "candidate",
}


# Role: Normalizes English word endings by stripping common suffixes.
# Workflow: Checks token length, strips known suffixes like ing or ed, handles plural forms, and returns the simplified root stem.
def _light_stem(token: str) -> str:
    """Lightweight morphological normalizer for technical English words."""
    if len(token) <= 4:
        return token
    for suffix in ("ingly", "edly", "ment", "tion", "sion", "ings", "ing", "able", "ible", "ies", "es", "ed", "s"):
        if token.endswith(suffix) and len(token) - len(suffix) >= 3:
            if suffix == "ies":
                return token[:-3] + "y"
            return token[: -len(suffix)]
    return token


# Role: Computes pairwise cosine similarity between two matrices of vector embeddings.
# Workflow: Validates matrix dimensions, calculates dot products and L2 norms using scikit-learn or NumPy, normalizes zero vectors, and returns the similarity matrix.
def vectorized_cosine_similarity(mat_a: np.ndarray, mat_b: np.ndarray) -> np.ndarray:
    """
    Computes the $(N \\times M)$ Cosine Similarity matrix between two 2D arrays
    using `scikit-learn` when available or pure vectorized `numpy` matrix multiplication:
    $$\\text{CosSim}(A, B) = \\frac{A B^T}{\\|A\\|_2 \\|B\\|_2}$$
    """
    if mat_a.size == 0 or mat_b.size == 0:
        return np.zeros((mat_a.shape[0], mat_b.shape[0]), dtype=np.float32)

    if sklearn_cosine_similarity is not None:
        return sklearn_cosine_similarity(mat_a, mat_b).astype(np.float32)

    norm_a = np.linalg.norm(mat_a, axis=1, keepdims=True)
    norm_b = np.linalg.norm(mat_b, axis=1, keepdims=True)
    norm_a[norm_a == 0.0] = 1.0
    norm_b[norm_b == 0.0] = 1.0
    unit_a = mat_a / norm_a
    unit_b = mat_b / norm_b
    return np.matmul(unit_a, unit_b.T).astype(np.float32)


@dataclass
class PartialSkillMatch:
    """Represents a semantic adjacent or implicit context skill match (Soft Credit)."""

    required: str
    candidate_has: str
    similarity: float
    credit_awarded: float
    match_type: str = "semantic_adjacent"  # "semantic_adjacent" | "implicit_context"

    # Role: Serializes a partial skill match object into a clean dictionary.
    # Workflow: Packs required skill name, matched candidate skill, rounded similarity, credit awarded, and match type into a dictionary for API output.
    def to_dict(self) -> dict[str, Any]:
        return {
            "required": self.required,
            "candidate_has": self.candidate_has,
            "similarity": round(self.similarity, 2),
            "credit_awarded": round(self.credit_awarded, 3),
            "match_type": self.match_type,
        }


@dataclass
class SkillAlignmentResult:
    """Structured output of Feature 2.1 multi-vector skill alignment evaluation."""

    matched_skills: list[str] = field(default_factory=list)
    partial_skills: list[dict[str, Any]] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    total_partial_credit: float = 0.0
    total_required_count: int = 0

    # Role: Serializes a partial skill match object into a clean dictionary.
    # Workflow: Packs required skill name, matched candidate skill, rounded similarity, credit awarded, and match type into a dictionary for API output.
    def to_dict(self) -> dict[str, Any]:
        return {
            "matched_skills": self.matched_skills,
            "partial_skills": self.partial_skills,
            "missing_skills": self.missing_skills,
            "total_partial_credit": round(self.total_partial_credit, 3),
            "total_required_count": self.total_required_count,
        }


# Rich domain context descriptions for skills so dense embeddings capture full technical meaning
SKILL_CONTEXT_DESCRIPTIONS: dict[str, str] = {
    "Python": "Python 3 backend programming language scripting data science automation asyncio",
    "FastAPI": "FastAPI Python async REST API backend web framework Starlette Pydantic ASGI",
    "Flask": "Flask Python WSGI REST API backend web microframework Werkzeug",
    "Django": "Django Python REST framework DRF backend web framework ORM",
    "Node.js": "Node.js JavaScript TypeScript backend server runtime asynchronous API",
    "Express.js": "Express.js Node.js REST API backend web server framework",
    "NestJS": "NestJS TypeScript Node.js modular backend REST API framework",
    "Spring Boot": "Spring Boot Java enterprise backend REST API microservice framework",
    "React": "React.js React 18 frontend web UI component library JSX hooks SPA",
    "Next.js": "Next.js React frontend SSR fullstack web application framework",
    "Vue.js": "Vue.js Vue 3 frontend reactive UI component SPA web framework",
    "Angular": "Angular TypeScript frontend enterprise SPA web UI framework",
    "React Native": "React Native cross-platform mobile UI component framework JSX",
    "Tailwind CSS": "Tailwind CSS utility-first frontend styling responsive UI design system",
    "CSS3": "CSS3 cascading stylesheets flexbox grid frontend web styling UI design",
    "PostgreSQL": "PostgreSQL relational SQL database ACID RDBMS Postgres JSONB queries indexing",
    "MySQL": "MySQL relational SQL database ACID RDBMS MariaDB queries indexing",
    "SQLite": "SQLite embedded relational SQL database engine RDBMS",
    "Microsoft SQL Server": "Microsoft SQL Server T-SQL relational database RDBMS",
    "MongoDB": "MongoDB NoSQL document database JSON collection storage",
    "Redis": "Redis in-memory key-value data store cache message broker",
    "Docker": "Docker containerization Dockerfile docker-compose container runtime deployment",
    "Kubernetes": "Kubernetes K8s container orchestration cluster deployment pods Helm",
    "AWS": "Amazon Web Services AWS cloud infrastructure EC2 S3 RDS Lambda ECS cloud computing",
    "Google Cloud Platform": "Google Cloud Platform GCP cloud infrastructure GKE Cloud Run BigQuery",
    "Microsoft Azure": "Microsoft Azure cloud infrastructure AKS Azure Functions cloud computing",
    "Terraform": "Terraform Infrastructure as Code IaC cloud provisioning automation",
    "CI/CD": "CI/CD continuous integration continuous deployment GitHub Actions GitLab CI Jenkins",
    "Natural Language Processing": "Natural Language Processing NLP text analytics named entity recognition transformers embeddings semantic similarity",
    "Hugging Face Transformers": "Hugging Face Transformers BERT RoBERTa NLP neural language models embeddings",
    "Sentence Transformers": "Sentence Transformers SBERT MiniLM dense semantic text vector embeddings NLP",
    "spaCy": "spaCy Python Natural Language Processing NLP named entity recognition tokenization pipeline",
    "Large Language Models": "Large Language Models LLM Generative AI transformers NLP text generation",
    "Retrieval-Augmented Generation": "Retrieval-Augmented Generation RAG vector search semantic retrieval NLP embeddings",
    "PyTorch": "PyTorch deep learning neural networks tensor computation machine learning NLP",
    "TensorFlow": "TensorFlow Keras deep learning neural networks machine learning model training",
    "Scikit-Learn": "Scikit-Learn Python machine learning classification regression clustering cosine similarity",
    "ONNX Runtime": "ONNX Runtime high-performance cross-platform neural network model inference optimization",
}


class SemanticEngine:
    """
    Singleton multi-vector embedding engine powered by `sentence-transformers/all-MiniLM-L6-v2`
    with vectorized NumPy / scikit-learn cosine similarity matrices.
    """

    _instance: SemanticEngine | None = None

    # Role: Initializes the singleton semantic embedding engine.
    # Workflow: Reads embedding model configuration, connects to the entity extraction service, and loads model weights.
    def __init__(self) -> None:
        self.model_name = settings.EMBEDDING_MODEL_NAME
        self.model: Any = None
        self.backend_mode: str = "uninitialized"
        self.entity_service = EntityExtractionService.get_instance()
        self._load_model()

    # Role: Provides global singleton access to the SemanticEngine instance.
    # Workflow: Returns the existing instance if initialized, or instantiates a new one and caches it.
    @classmethod
    def get_instance(cls) -> SemanticEngine:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # Role: Loads local SentenceTransformer model weights or initializes offline vectorizer.
    # Workflow: Checks if sentence-transformers is installed, loads local all-MiniLM-L6-v2 weights, or falls back to the deterministic NumPy concept vectorizer.
    def _load_model(self) -> None:
        """
        Loads `sentence-transformers/all-MiniLM-L6-v2` locally on CPU/ONNX.
        If running inside an air-gapped environment without pre-cached HuggingFace weights,
        initializes the deterministic NumPy Sublinear TF-IDF + Taxonomy Concept Vectorizer.
        """
        if SentenceTransformer is not None:
            try:
                self.model = SentenceTransformer(
                    self.model_name,
                    device="cpu",
                    local_files_only=True,
                )
                self.backend_mode = "sentence-transformers (all-MiniLM-L6-v2 local)"
                logger.info("Loaded local SentenceTransformer model: %s", self.model_name)
                return
            except Exception:
                try:
                    self.model = SentenceTransformer(self.model_name, device="cpu")
                    self.backend_mode = "sentence-transformers (all-MiniLM-L6-v2)"
                    logger.info("Downloaded & loaded SentenceTransformer model: %s", self.model_name)
                    return
                except Exception as exc:
                    logger.warning(
                        "SentenceTransformer offline fallback activated (%s). Using local Hybrid NumPy Vectorizer.",
                        exc,
                    )

        self.model = None
        self.backend_mode = "numpy-hybrid-semantic-vectorizer"

    # Role: Tokenizes text into normalized domain concept words.
    # Workflow: Extracts lowercase alphanumeric tokens, filters out common stop words, applies morphological stemming, and returns the token list.
    @staticmethod
    def _tokenize_concepts(text: str) -> list[str]:
        """Extracts stemmed unigrams and domain concept tokens excluding stop words."""
        raw_words = [
            w
            for w in re.findall(r"[a-z0-9+#.]{2,}", text.lower())
            if w not in STOP_WORDS
        ]
        stemmed = [_light_stem(w) for w in raw_words]
        return stemmed

    # Role: Encodes text batches into normalized vectors using sublinear TF-IDF and taxonomy concepts.
    # Workflow: Expands each text with domain concepts, calculates term frequency and inverse document frequency, normalizes vector magnitudes, and returns a NumPy float matrix.
    def _encode_with_numpy_tfidf(self, texts: list[str]) -> np.ndarray:
        """
        Pure NumPy sublinear TF-IDF + Taxonomy Concept encoder producing L2-normalized
        dense vectors calibrated to match MiniLM cosine similarity distributions.
        """
        expanded_docs = [
            self._tokenize_concepts(self._expand_text_with_taxonomy_concepts(t))
            for t in texts
        ]
        n_docs = len(expanded_docs)

        vocab: dict[str, int] = {}
        df: Counter[str] = Counter()
        for tokens in expanded_docs:
            for tok in set(tokens):
                df[tok] += 1
                if tok not in vocab:
                    vocab[tok] = len(vocab)

        if not vocab:
            return np.zeros((n_docs, 1), dtype=np.float32)

        mat = np.zeros((n_docs, len(vocab)), dtype=np.float32)
        for doc_idx, tokens in enumerate(expanded_docs):
            tf_counts = Counter(tokens)
            for tok, count in tf_counts.items():
                col_idx = vocab[tok]
                # Sublinear TF with damped IDF so shared domain terms contribute strong positive cosine
                tf_val = 1.0 + math.log(count)
                idf_val = 1.0 + 0.35 * math.log((1.0 + n_docs) / (1.0 + df[tok]))
                mat[doc_idx, col_idx] = tf_val * idf_val

        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms[norms == 0.0] = 1.0
        return (mat / norms).astype(np.float32)

    # Role: Transforms a batch of text strings into L2-normalized dense vector embeddings.
    # Workflow: Validates input list, uses the active neural SentenceTransformer model in batches if present, or delegates to the sublinear TF-IDF encoder.
    def encode_texts(self, texts: list[str]) -> np.ndarray:
        """
        Encodes a batch of text strings into L2-normalized dense embeddings.
        """
        if not texts:
            return np.zeros((0, 384), dtype=np.float32)

        if self.model is not None:
            embeddings = self.model.encode(
                texts,
                batch_size=32,
                show_progress_bar=False,
                normalize_embeddings=True,
                convert_to_numpy=True,
            )
            return np.asarray(embeddings, dtype=np.float32)

        return self._encode_with_numpy_tfidf(texts)

    # Role: Enriches text with domain taxonomy concepts and adjacent skill descriptors.
    # Workflow: Extracts technical skills present in the text, appends their parent categories, definitions, and high-confidence adjacent terms to produce dense concept text.
    def _expand_text_with_taxonomy_concepts(self, text: str) -> str:
        """
        Enriches text with canonical skill categories and semantic cousin descriptors
        so offline cosine similarity accurately reflects domain semantics alongside MiniLM.
        """
        extracted = self.entity_service.extract_skills(text)
        concept_tokens: list[str] = [text]

        for skill in extracted:
            # Repeat canonical skill and its category to weight core engineering concepts higher than prose filler
            concept_tokens.extend([skill, skill])
            info = self.entity_service.canonical_skills.get(skill, {})
            cat = info.get("category", "")
            if cat:
                cat_clean = cat.replace("_", " ")
                concept_tokens.extend([cat_clean, cat_clean])
            if skill in SKILL_CONTEXT_DESCRIPTIONS:
                concept_tokens.append(SKILL_CONTEXT_DESCRIPTIONS[skill])
            for adj in self.entity_service.semantic_adjacency_map.get(skill, []):
                if float(adj.get("similarity", 0.0)) >= 0.78:
                    concept_tokens.append(adj["skill"])
                    concept_tokens.append(adj.get("reason", ""))

        return " ".join(concept_tokens)

    # Role: Retrieves precomputed domain adjacency similarity between two skills.
    # Workflow: Checks for identical skill names, queries the curated taxonomy adjacency graph in both directions, and returns the similarity float.
    def _lookup_curated_skill_similarity(self, req_skill: str, cand_skill: str) -> float:
        """
        Checks the bidirectional curated `semantic_adjacency_map` in `skills_taxonomy.json`.
        """
        if req_skill.lower() == cand_skill.lower():
            return 1.0

        for entry in self.entity_service.semantic_adjacency_map.get(req_skill, []):
            if entry["skill"].lower() == cand_skill.lower():
                return float(entry["similarity"])

        for entry in self.entity_service.semantic_adjacency_map.get(cand_skill, []):
            if entry["skill"].lower() == req_skill.lower():
                return float(entry["similarity"])

        return 0.0

    # Role: Builds a pairwise cosine similarity matrix between required skills and candidate skills.
    # Workflow: Formulates descriptive text prompts for each skill, computes dense embeddings, calculates cosine similarity, layers curated taxonomy priors, and bounds scores between 0.0 and 1.0.
    def compute_skill_pair_similarity_matrix(
        self,
        jd_skills: list[str],
        candidate_skills: list[str],
    ) -> np.ndarray:
        """
        Computes an $(N_{\\text{JD}} \\times M_{\\text{Cand}})$ similarity matrix combining
        neural MiniLM cosine similarity on enriched skill definitions with curated
        domain adjacency priors.
        """
        if not jd_skills or not candidate_skills:
            return np.zeros((len(jd_skills), len(candidate_skills)), dtype=np.float32)

        jd_prompts = [
            SKILL_CONTEXT_DESCRIPTIONS.get(s, f"{s} technical engineering skill")
            for s in jd_skills
        ]
        cand_prompts = [
            SKILL_CONTEXT_DESCRIPTIONS.get(c, f"{c} technical engineering skill")
            for c in candidate_skills
        ]

        combined_embeddings = self.encode_texts(jd_prompts + cand_prompts)
        jd_emb = combined_embeddings[: len(jd_skills)]
        cand_emb = combined_embeddings[len(jd_skills) :]

        sim_matrix = vectorized_cosine_similarity(jd_emb, cand_emb)

        # In offline TF-IDF fallback mode, down-scale uncurated lexical overlap slightly
        # so unrelated skills that merely share generic words ("cloud", "platform") don't
        # exceed the 0.72 adjacency threshold unless backed by domain adjacency or strong overlap.
        if self.model is None:
            sim_matrix = sim_matrix * 0.85

        for i, req_s in enumerate(jd_skills):
            for j, cand_s in enumerate(candidate_skills):
                curated_sim = self._lookup_curated_skill_similarity(req_s, cand_s)
                if curated_sim > 0.0:
                    sim_matrix[i, j] = max(float(sim_matrix[i, j]), curated_sim)

        return np.clip(sim_matrix, 0.0, 1.0)

    # Role: Splits continuous work experience and project paragraphs into individual sentence and bullet chunks.
    # Workflow: Separates text by newlines, bullet symbols, or punctuation, cleans leading and trailing characters, filters short fragments, and returns contextual strings.
    @staticmethod
    def split_into_sentence_chunks(text: str) -> list[str]:
        """Splits experience and project sections into clean sentence/bullet chunks."""
        if not text or not text.strip():
            return []
        raw_parts = re.split(r"(?:[\n\r•\*]+|(?<=[.!?])\s+)", text)
        chunks = [
            re.sub(r"\s+", " ", p).strip(" -–—•*\t")
            for p in raw_parts
            if len(p.strip()) >= 20
        ]
        return chunks[:80]

    # Role: Evaluates candidate technical profile against required job description skills.
    # Workflow: Canonicalizes skill names, detects direct exact matches, runs semantic similarity against candidate skills for soft credit, inspects experience sentences for implicit context, and returns a structured match breakdown.
    def evaluate_skill_alignment(
        self,
        jd_skills: list[str],
        candidate_skills: list[str],
        resume_chunks: list[str] | None = None,
    ) -> SkillAlignmentResult:
        """
        Feature 2.1: Evaluates every required JD skill against the candidate's profile:
        1. Exact/Canonical Match ($s_i \\in \\text{Candidate\\_Skills}$) -> score = 1.0.
        2. Semantic Adjacent Match ($0.72 \\le m < 0.95$) -> awards $0.6 \\times m$ partial credit.
        3. Implicit Context Check against `resume_chunks` (experience & project sentences).
        4. Missing Skill ($< 0.72$) -> score = 0.0.
        """
        if not jd_skills:
            return SkillAlignmentResult()

        norm_jd_skills: list[str] = []
        for s in jd_skills:
            canon = self.entity_service.normalize_skill_name(s)
            if canon and canon not in norm_jd_skills:
                norm_jd_skills.append(canon)

        norm_cand_skills: list[str] = []
        for c in candidate_skills:
            canon = self.entity_service.normalize_skill_name(c)
            if canon and canon not in norm_cand_skills:
                norm_cand_skills.append(canon)

        cand_lower_map = {c.lower(): c for c in norm_cand_skills}

        matched_skills: list[str] = []
        unmatched_jd_skills: list[str] = []

        # Step 1: Exact / Canonical Match
        for req_skill in norm_jd_skills:
            if req_skill.lower() in cand_lower_map:
                matched_skills.append(req_skill)
            else:
                unmatched_jd_skills.append(req_skill)

        partial_skills: list[dict[str, Any]] = []
        still_unmatched: list[str] = []
        total_partial_credit = 0.0

        # Step 2: Semantic Adjacent Match (Soft Credit against candidate_skills)
        available_adjacent_cand = [
            c for c in norm_cand_skills if c.lower() not in {m.lower() for m in matched_skills}
        ]
        if not available_adjacent_cand:
            available_adjacent_cand = norm_cand_skills

        if unmatched_jd_skills and available_adjacent_cand:
            sim_matrix = self.compute_skill_pair_similarity_matrix(
                unmatched_jd_skills, available_adjacent_cand
            )
            for idx, req_skill in enumerate(unmatched_jd_skills):
                row = sim_matrix[idx]
                best_j = int(np.argmax(row))
                max_sim = float(row[best_j])
                best_cand_skill = available_adjacent_cand[best_j]

                if max_sim >= settings.EXACT_MATCH_THRESHOLD:
                    matched_skills.append(req_skill)
                elif settings.SEMANTIC_ADJACENT_THRESHOLD <= max_sim < settings.EXACT_MATCH_THRESHOLD:
                    credit = settings.PARTIAL_CREDIT_MULTIPLIER * max_sim
                    total_partial_credit += credit
                    partial_skills.append(
                        PartialSkillMatch(
                            required=req_skill,
                            candidate_has=best_cand_skill,
                            similarity=round(max_sim, 2),
                            credit_awarded=round(credit, 3),
                            match_type="semantic_adjacent",
                        ).to_dict()
                    )
                else:
                    still_unmatched.append(req_skill)
        else:
            still_unmatched = list(unmatched_jd_skills)

        # Step 3: Implicit Context Check against sentence chunks in Experience & Projects
        missing_skills: list[str] = []
        clean_chunks = [c for c in (resume_chunks or []) if c and len(c.strip()) >= 15]

        if still_unmatched and clean_chunks:
            req_prompts = [
                SKILL_CONTEXT_DESCRIPTIONS.get(s, f"Experience building and using {s}")
                for s in still_unmatched
            ]
            combined_emb = self.encode_texts(req_prompts + clean_chunks)
            req_emb = combined_emb[: len(still_unmatched)]
            chunk_emb = combined_emb[len(still_unmatched) :]
            chunk_sim_matrix = vectorized_cosine_similarity(req_emb, chunk_emb)
            if self.model is None:
                chunk_sim_matrix = chunk_sim_matrix * 0.85

            for idx, req_skill in enumerate(still_unmatched):
                row = chunk_sim_matrix[idx]
                best_chunk_idx = int(np.argmax(row))
                max_chunk_sim = float(row[best_chunk_idx])

                if max_chunk_sim >= settings.SEMANTIC_ADJACENT_THRESHOLD:
                    credit = settings.PARTIAL_CREDIT_MULTIPLIER * max_chunk_sim
                    total_partial_credit += credit
                    snippet = clean_chunks[best_chunk_idx][:65].rstrip(".")
                    partial_skills.append(
                        PartialSkillMatch(
                            required=req_skill,
                            candidate_has=f"Implicit Context ({snippet}...)",
                            similarity=round(max_chunk_sim, 2),
                            credit_awarded=round(credit, 3),
                            match_type="implicit_context",
                        ).to_dict()
                    )
                else:
                    missing_skills.append(req_skill)
        else:
            missing_skills = list(still_unmatched)

        return SkillAlignmentResult(
            matched_skills=matched_skills,
            partial_skills=partial_skills,
            missing_skills=missing_skills,
            total_partial_credit=round(total_partial_credit, 4),
            total_required_count=len(norm_jd_skills),
        )

    # Role: Measures holistic semantic alignment between job requirements and candidate career history.
    # Workflow: Encodes job description responsibilities and candidate experience text into vectors, computes cosine similarity, rescales raw values to a 0 to 100 score, and returns both metrics.
    def compute_section_semantic_similarity(
        self,
        jd_text: str,
        candidate_experience_and_projects_text: str,
    ) -> tuple[float, float]:
        """
        Feature 2.2 Sub-score #2:
        Encodes JD core responsibilities + requirements against the candidate's
        experience + projects text blocks.
        Returns `(raw_cosine_similarity, rescaled_0_to_100_score)` where raw cosine
        in `[0.30, 0.80]` is linearly mapped onto `[0.0, 100.0]`.
        """
        if not jd_text.strip() or not candidate_experience_and_projects_text.strip():
            return 0.0, 0.0

        embeddings = self.encode_texts(
            [jd_text.strip(), candidate_experience_and_projects_text.strip()]
        )
        raw_cos = float(vectorized_cosine_similarity(embeddings[0:1], embeddings[1:2])[0, 0])

        # When using the offline sparse-concept fallback instead of dense MiniLM embeddings,
        # apply a smooth sqrt calibration so raw cosine maps onto the same [0.30, 0.80] distribution
        if self.model is None and raw_cos > 0:
            raw_cos = math.sqrt(raw_cos) * 0.85

        raw_cos = max(0.0, min(1.0, raw_cos))

        # Linearly rescale [0.30, 0.80] -> [0.0, 100.0] per Feature 2.2 specification
        low = settings.SEMANTIC_MIN_BASELINE
        high = settings.SEMANTIC_MAX_CEILING
        if raw_cos <= low:
            rescaled = max(0.0, (raw_cos / low) * 20.0)
        elif raw_cos >= high:
            rescaled = 100.0
        else:
            rescaled = ((raw_cos - low) / (high - low)) * 100.0

        return round(raw_cos, 4), round(min(100.0, max(0.0, rescaled)), 1)


# Role: Module-level wrapper for candidate skill alignment evaluation.
# Workflow: Fetches the SemanticEngine singleton instance and executes the skill alignment pipeline.
def evaluate_skill_alignment(
    jd_skills: list[str],
    candidate_skills: list[str],
    resume_chunks: list[str] | None = None,
) -> SkillAlignmentResult:
    """Module-level convenience wrapper for Feature 2.1."""
    return SemanticEngine.get_instance().evaluate_skill_alignment(
        jd_skills=jd_skills,
        candidate_skills=candidate_skills,
        resume_chunks=resume_chunks,
    )


# Role: Module-level wrapper for section semantic similarity computation.
# Workflow: Fetches the SemanticEngine singleton instance and computes semantic similarity between job requirements and candidate history.
def compute_section_semantic_similarity(
    jd_text: str,
    candidate_experience_and_projects_text: str,
) -> tuple[float, float]:
    """Module-level convenience wrapper for Feature 2.2 section semantic similarity."""
    return SemanticEngine.get_instance().compute_section_semantic_similarity(
        jd_text=jd_text,
        candidate_experience_and_projects_text=candidate_experience_and_projects_text,
    )
