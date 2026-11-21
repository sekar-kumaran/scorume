# Scorume (evaluation engine) — 10-Minute Technical Video Presentation Script
**Project:** Scorume (evaluation engine) • Technical Evaluation & Precision Resume Matching Engine  
**Purpose:** Technical Recruitment Portfolio Showcase / System Design & Architecture Presentation  
**Target Audience:** Senior Technical Interviewers, Engineering Directors, and Hiring Managers  
**Total Target Duration:** 10:00 Minutes (~1,450 spoken words, ~145 wpm)

---

## Video Production & Presentation Guidelines
- **Visual Split:** 60% Screen Recording (Live UI & Code Architecture), 30% System Architecture Diagrams, 10% Presenter Camera.
- **Audio Tone:** Confident, structured, articulate, engineering-led, and impact-focused.
- **Visual Cues Legend:**
  - `[ON SCREEN]`: What the viewers see on screen (UI, diagrams, IDE).
  - `[ACTION]`: Presenter actions (clicks, code scrolling, hovering).
  - `[SPOKEN]`: The exact narration to deliver.

---

```
========================================================================================
TIMELINE OVERVIEW
========================================================================================
[00:00 - 01:10] Scene 1: The Problem, Hook & System Overview (1:10)
[01:10 - 02:40] Scene 2: High-Level System Architecture & Privacy-First Philosophy (1:30)
[02:40 - 05:00] Scene 3: Deep Dive into the Backend Services & NLP Pipeline (2:20)
[05:00 - 06:45] Scene 4: Database Architecture & Pydantic Schemas (1:45)
[06:45 - 08:15] Scene 5: How Google Stitch & AI Were Used in Design and Development (1:30)
[08:15 - 09:25] Scene 6: Live Product Walkthrough & End-to-End Workflow (1:10)
[09:25 - 10:00] Scene 7: Performance Benchmarks, Impact & Engineering Conclusion (0:35)
========================================================================================
```

---

## [00:00 - 01:10] Scene 1: The Problem, Hook & System Overview
**Visual:** Presenter on camera with a split screen showing traditional keyword screening failure modes vs. Scorume (evaluation engine)'s sleek dashboard.  
`[ON SCREEN]`: Title Slide: *Scorume (evaluation engine): Precision Technical Recruitment Engine*. Transition to live browser showing the Bengaluru Hub dashboard at `http://localhost:5173`.

`[SPOKEN]`:
> "Hello everyone. Today, I am excited to walk you through **Scorume (evaluation engine)**, a production-ready, privacy-first technical evaluation and resume ranking engine that I designed and engineered from the ground up.
>
> In technical hiring today, traditional recruitment screening tools are fundamentally broken. First, they rely on rigid lexical string matching—meaning an exceptional engineer with 6 years of deep *Flask* or *Django* experience gets automatically rejected if a job description lists *FastAPI*, simply because the keyword isn't identical. Second, legacy tools are notoriously vulnerable to adversarial manipulation, such as candidates hiding white-on-white text or microscopic font keywords to game the parser. Third, they act as unexplainable black boxes that offer recruiters zero defensible rationale for why someone was ranked first or last.
>
> To solve this, I built Scorume (evaluation engine): a 100% on-premise, enterprise-grade platform that combines layout-level document security inspection, semantic section segmentation, hybrid spaCy entity extraction, and multi-vector Sentence-Transformer embeddings—delivering sub-35-millisecond deterministic evaluations, complete explainability, and total data compliance under India's Digital Personal Data Protection Act."

---

## [01:10 - 02:40] Scene 2: High-Level System Architecture & Privacy-First Philosophy
**Visual:** High-resolution architectural flowchart illustrating the 5-stage pipeline from document ingestion to the React frontend.  
`[ON SCREEN]`: Mermaid Architecture Diagram highlighting Container boundaries (`scorume_postgres`, `scorume_backend`, `scorume_frontend`), FastAPI Backend, PyTorch/SentenceTransformers, spaCy pipeline, PostgreSQL 16 with JSONB, and Vite React frontend.

`[SPOKEN]`:
> "Let’s start with the high-level architecture. Scorume (evaluation engine) is containerized via Docker Compose into three clean tiers: a PostgreSQL 16 relational data store, a high-performance FastAPI asynchronous backend, and a reactive Vite React 18 user interface.
>
> When designing this engine, I made a strict architectural commitment: **Zero External Cloud LLM API Calls**.
>
> Sending sensitive candidate resumes and proprietary job descriptions to external cloud endpoints introduces severe data sovereignty risks, recurring operational costs, and non-deterministic latency spikes.
>
> Instead, Scorume (evaluation engine) executes 100% of its NLP, vector math, and scoring locally on CPU. We pre-cache lightweight, highly optimized neural models during Docker build time, allowing our complete 5-stage processing pipeline to run securely within corporate firewalls at zero incremental cost per resume."

---

## [02:40 - 05:00] Scene 3: Deep Dive into the Backend Services & NLP Pipeline
**Visual:** VS Code editor displaying `backend/app/services/` with clean split views between `document_parser.py`, `section_segmenter.py`, `entity_extractor.py`, `semantic_engine.py`, and `scoring_engine.py`.  
`[ACTION]`: Step through each service file, highlighting function signatures and comments explaining the workflow.

`[SPOKEN]`:
> "Now let's examine the 5 backend services that power our processing pipeline.
>
> **Service 1: Document Parser (`document_parser.py`)**  
> We ingest both PDF and DOCX formats using PyMuPDF and python-docx. But we go far beyond text extraction: we inspect the low-level layout spans. In PDFs, we examine font colors, background contrasts, and font sizes. If a candidate attempts to conceal white text against a white background or embeds 1-point font keywords, our security scanner intercepts it, calculates a stuffing score, and flags an adversarial security alert.
>
> **Service 2: Section-Aware Segmenter (`section_segmenter.py`)**  
> Resumes aren't flat text; they have clear semantic boundaries. Using regex anchor dictionaries and spatial boundary analysis, we segment the raw document into distinct semantic blocks: Work Experience, Technical Skills, Education, Projects, and Certifications. This guarantees that skills listed in an academic course 5 years ago aren't conflated with active production work experience.
>
> **Service 3: Entity Extractor & Experience Math (`entity_extractor.py`)**  
> This is our hybrid extraction pipeline. We load a comprehensive taxonomy of over 300 technical skills across 1,600 aliases into spaCy's `EntityRuler`. We also parse date ranges using regex and dateutil. Crucially, when calculating Years of Experience, we don't just sum date ranges—we merge overlapping employment intervals using an interval arithmetic algorithm to avoid double-counting moonlighting or simultaneous contract roles.
>
> **Service 4: Multi-Vector Semantic Engine (`semantic_engine.py`)**  
> Rather than relying on simple keyword overlap, we run the `sentence-transformers/all-MiniLM-L6-v2` neural model locally. We compute separate dense 384-dimensional embeddings for: the overall profile, the technical skills block, and the work experience history. We compute cosine similarity matrices between the candidate and the job description, granting partial credit for conceptually adjacent skills—for example, awarding 75% credit to an engineer with deep PostgreSQL experience when the job description specifies CockroachDB.
>
> **Service 5: Mathematical Scoring Engine (`scoring_engine.py`)**  
> Finally, our scoring engine synthesizes everything into a composite score between 0 and 100 using a deterministic formula:
> - 40% Technical Skill Overlap
> - 30% Multi-Vector Semantic Similarity
> - 30% Verified Experience & Career Trajectory
>
> Most importantly, the engine outputs human-readable Explainable AI bullets detailing exactly why points were awarded or deducted."

---

## [05:00 - 06:45] Scene 4: Database Architecture & Pydantic Schemas
**Visual:** VS Code displaying `backend/app/models.py` and `backend/app/schemas.py`.  
`[ACTION]`: Scroll through the SQLAlchemy ORM models (`JobBenchmark`, `CandidateEvaluation`, `AuditLog`) and highlight the JSONB structure in PostgreSQL.

`[SPOKEN]`:
> "Let’s look at the data architecture.
>
> In `backend/app/models.py`, we define three primary entities:
> 1. `JobBenchmark`: Stores the normalized job requirements, benchmark embeddings, target years of experience, and location hubs like Bengaluru, Mumbai, or Hyderabad.
> 2. `CandidateEvaluation`: Stores the candidate profile, extracted metadata, and detailed sub-scores. Notice that complex data—like matched skills, missing competencies, and XAI reasoning bullets—are stored in PostgreSQL `JSONB` columns, indexed with GIN for fast querying.
> 3. `AuditLog`: An immutable record tracking candidate evaluations and recruiter interactions, complete with millisecond latencies and timestamp auditing.
>
> We support zero-configuration fallback: if PostgreSQL isn't detected, the backend seamlessly switches to SQLite with an in-memory JSON serialization layer.
>
> Moving to `backend/app/schemas.py`, we enforce strict Pydantic V2 data contracts:
> - `JDCreate` and `JDResponse` for benchmark validation.
> - `CandidateEvaluationResponse` and `ScoreWeights` for real-time recalculations.
> - `RoleMatcherRequest` and `ReverseRoleMatchItem` power our cross-pool discovery engine, enabling bidirectional matching between candidates and active benchmarks.
>
> Every endpoint is typed, self-documenting via OpenAPI, and fully validated."

---

## [06:45 - 08:15] Scene 5: How Google Stitch & AI Were Used in Design and Development
**Visual:** Side-by-side comparison of Google Stitch HTML/design mockups in `stitch_talentrank_technical_evaluation_engine` next to the React implementation in `frontend/src/`.  
`[ACTION]`: Show the Stitch screen captures, then show the clean JSX React components with Tailwind CSS tokens.

`[SPOKEN]`:
> "One of the most unique aspects of this project is how modern AI tooling and design systems were integrated into the development lifecycle.
>
> **Leveraging Google Stitch for Enterprise UI/UX**  
> Rather than building a generic developer UI, I started with **Google Stitch** design prototypes located in the `stitch_talentrank_technical_evaluation_engine` directory. Stitch provided high-fidelity visual foundations for our core views: Campaign Setup, the Rankings Leaderboard, the Deep-Dive Drawer, Evaluation History, and the Scorume (evaluation engine).
>
> I analyzed the Stitch HTML and CSS specifications, extracted key design tokens—such as high-density typography, layered elevation shadows, and status indicators—and re-architected them into modular, maintainable **React 18** components using **Tailwind CSS**.
>
> **Localizing for Indian Technical Recruitment**  
> I then evolved the design specifically for Indian tech hiring:
> - Replaced all generic dollar notations with Indian compensation brackets—for example, *Target CTC: ₹28 - ₹42 LPA*.
> - Configured hub locations across Bengaluru, Hyderabad, Pune, Gurugram, and Mumbai.
> - Built smooth micro-interactions: card-lift hover physics (`.card-hover`), tactile button press scaling (`.btn-press`), and glowing status indicators.
>
> **AI as an Engineering Accelerator**  
> Throughout the build, I leveraged generative AI as an engineering collaborator:
> 1. To synthesize realistic, diverse candidate test corpora across PDF and DOCX formats with varying career lengths and technical stacks.
> 2. To calibrate semantic embedding cosine boundaries and verify soft-credit thresholds against domain heuristics.
> 3. To rigorously refactor codebase services while strictly maintaining schema compliance and deterministic evaluation behavior."

---

## [08:15 - 09:25] Scene 6: Live Product Walkthrough & End-to-End Workflow
**Visual:** Full-screen browser recording of `http://localhost:5173`.  
`[ACTION]`: Live demo: click 'Load 12 Sample Resumes', adjust scoring sliders, click 'Inspect' to open the drawer, view explainability bullets, click 'Shortlist', then switch to 'Scorume (evaluation engine)'.

`[SPOKEN]`:
> "Let’s see the entire system in action.
>
> Here in **Screen 1 (Job Setup & Ingestion)**, we have our job description for a *Senior Full-Stack AI Engineer in Bengaluru*. Our parser automatically identifies the 4-year tenure requirement and detects 12 core competencies like *FastAPI, PyTorch, React, and pgvector*.
>
> Clicking *'Load 12 Sample Resumes'* simulates batch ingestion. In just 1.2 seconds, all 12 resumes are parsed, checked for hidden text, segmented, vectorized, and scored.
>
> This brings us to **Screen 2 (The Candidate Leaderboard)**. Candidates are ranked objectively. Notice our top candidate, *Omkar Chittar*, leading at 80% with 5.6 years of verified experience. If our engineering team decides tenure is more critical than raw skill match, we can adjust the **Scoring Weightage Calibration** sliders in real time. Notice how the entire leaderboard re-ranks instantly without needing a slow backend round-trip.
>
> Clicking *'Inspect'* slides open **Screen 3: The Deep-Dive Drawer**. Here, there are no black-box scores. Recruiters see exact point attributions: +43.5 points for direct technical matches, +4.2 points for recognized adjacent skills, and clear verification of tenure. We can inspect the candidate's actual projects, education, and toggle the candidate to *'Shortlisted'* with a single click.
>
> Finally, **Screen 4 (Scorume (evaluation engine))** allows recruiters to search candidates across past hiring drives or reverse-match an incoming resume against all active company requisitions."

---

## [09:25 - 10:00] Scene 7: Performance Benchmarks, Impact & Engineering Conclusion
**Visual:** Presenter on camera with summary metrics slide displayed.  
`[ON SCREEN]`: Metrics summary:
- *Latency:* < 35ms per candidate evaluation
- *Cost:* ₹0.00 cloud API fees (100% on-device AI)
- *Privacy:* DPDP Act (India) compliant on-premise execution
- *Integrity:* Automated adversarial keyword-stuffing defense

`[SPOKEN]`:
> "To summarize, Scorume (evaluation engine) bridges the gap between state-of-the-art NLP and practical enterprise recruitment software. It eliminates keyword cheating, offers true semantic intelligence for adjacent technical skills, and provides hiring teams with 100% explainable, mathematically defensible evaluations.
>
> Architecturally, it demonstrates that you don’t need expensive external LLM APIs to build intelligent applications. With modern sentence transformers, custom spaCy pipelines, and a robust PostgreSQL JSONB data model, we achieved sub-35-millisecond latency, complete data privacy, and a seamless recruiter experience.
>
> Thank you for your time, and I would be thrilled to answer any questions about the system architecture or implementation details."

---

## Production Checklist for Recording
- [ ] Ensure Docker containers are running (`docker compose up -d`) with names `scorume_postgres`, `scorume_backend`, `scorume_frontend`, verified at `http://localhost:5173`.
- [ ] Screen resolution set to 1920x1080 (1080p) at 60 FPS.
- [ ] Microphone input level tested with background noise cancellation enabled.
- [ ] Browser zoom level set to 100% with DevTools closed.
- [ ] VS Code open with `backend/app/services/` and `backend/app/models.py` pre-opened in editor tabs.
