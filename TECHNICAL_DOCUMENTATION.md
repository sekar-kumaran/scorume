# Scorume (evaluation engine) — Comprehensive Technical Documentation & Video Presentation Master Guide

> **System Name:** Scorume (evaluation engine) (Technical Evaluation & Candidate Ranking Engine)  
> **Target Market:** Indian Tech Ecosystem (Bengaluru, Hyderabad, Mumbai, Pune, Gurugram)  
> **Compliance:** 100% Private, On-Premise Execution — DPDP Act (Digital Personal Data Protection) Ready  
> **Inference Infrastructure:** Zero External Cloud/LLM API Keys Required (Local Hugging Face MiniLM + spaCy + PyMuPDF)  
> **Version:** 1.0.0 Production  

---

## Table of Contents
1. [Executive Summary & High-Level Architecture](#1-executive-summary--high-level-architecture)
2. [Google Stitch & AI-Assisted Modernization Workflow](#2-google-stitch--ai-assisted-modernization-workflow)
3. [Frontend Walkthrough, Screenshots & Video Presentation Script](#3-frontend-walkthrough-screenshots--video-presentation-script)
   - [Screen 1: Job Benchmark & Resume Ingestion](#screen-1-job-benchmark--resume-ingestion)
   - [Screen 2: Candidate Rankings Leaderboard & Real-Time Weight Calibration](#screen-2-candidate-rankings-leaderboard--real-time-weight-calibration)
   - [Screen 3: Candidate Deep-Dive & Deterministic Explainable AI (XAI) Drawer](#screen-3-candidate-deep-dive--deterministic-explainable-ai-xai-drawer)
   - [Screen 4: Scorume (evaluation engine) & Cross-Drive Candidate Search](#screen-4-scorume-evaluation-engine--cross-drive-candidate-search)
   - [Screen 5: Hiring History, Audit Records & Recruitment Analytics](#screen-5-hiring-history-audit-records--recruitment-analytics)
4. [Backend Deep Dive: Workflows, Schemas, Classes & Functions](#4-backend-deep-dive-workflows-schemas-classes--functions)
   - [System Configuration (`app/config.py`)](#system-configuration-appconfigpy)
   - [Database Layer & ORM Entities (`app/database.py` & `app/models.py`)](#database-layer--orm-entities-appdatabasepy--appmodelspy)
   - [Validation & Serialization Schemas (`app/schemas.py`)](#validation--serialization-schemas-appschemaspy)
   - [Service 1: Document Parser & Adversarial Keyword-Stuffing Detector (`app/services/document_parser.py`)](#service-1-document-parser--adversarial-keyword-stuffing-detector-appservicesdocument_parserpy)
   - [Service 2: Section-Aware Segmenter (`app/services/section_segmenter.py`)](#service-2-section-aware-segmenter-appservicessection_segmenterpy)
   - [Service 3: Entity Extractor & Non-Overlapping Experience Math (`app/services/entity_extractor.py`)](#service-3-entity-extractor--non-overlapping-experience-math-appservicesentity_extractorpy)
   - [Service 4: Multi-Vector Semantic Engine (`app/services/semantic_engine.py`)](#service-4-multi-vector-semantic-engine-appservicessemantic_enginepy)
   - [Service 5: Mathematical Scoring Engine & XAI Reasoning Generator (`app/services/scoring_engine.py`)](#service-5-mathematical-scoring-engine--xai-reasoning-generator-appservicesscoring_enginepy)
   - [API Routers: Endpoint Specifications & Handlers (`app/routers/`)](#api-routers-endpoint-specifications--handlers-approuters)
5. [Production Deployment & Verification Guide](#5-production-deployment--verification-guide)

---

# 1. Executive Summary & High-Level Architecture

### The Problem
Traditional Applicant Tracking Systems (ATS) rely on crude lexical keyword matching. This creates two acute failure modes in technical recruitment:
1. **Keyword Stuffing & Gaming:** Candidates paste hidden white text, microscopic font, or laundry lists of buzzwords to trick regex scanners.
2. **False Negatives via Lexical Brittleness:** A qualified engineer writing *"built asynchronous REST APIs in FastAPI"* is rejected if the ATS exclusively searches for *"Python backend engineer"*, even though the semantic match is near-perfect.
3. **Data Privacy & Egress Violations:** Sending confidential resumes to external LLM APIs violates the Indian **Digital Personal Data Protection (DPDP) Act** and enterprise confidentiality.

### The Solution: Scorume (evaluation engine)
Scorume (evaluation engine) is a high-precision, on-premise technical candidate ranking platform. It processes batches of 10 to 50+ PDF/DOCX resumes locally in under 1.5 seconds with:
- **Zero External API Costs:** Runs `sentence-transformers/all-MiniLM-L6-v2` locally on CPU with ONNX / NumPy acceleration.
- **Adversarial Keyword-Stuffing Immunity:** Inspects PDF/DOCX layout spans at byte level; flags microscopic font (<2.0 pt) and `#FFFFFF` white-on-white text.
- **Three-Tier Multi-Vector Matching:** Exact canonical match (1.0), Semantic Adjacent match ($0.72 \le \cos < 0.95$, $0.6 \times \cos$ soft credit), and Implicit Context extraction from project sentences.
- **Non-Overlapping Tenure Calculation:** Merges concurrent internships and parallel roles into disjoint calendar intervals, preventing inflated experience figures.
- **Deterministic Explainable AI (XAI):** Generates exact point attribution bullets (`[+33.5 pts] Skill Match`, `[+20.0 pts] Experience Alignment`) removing black-box hallucination.
- **Indian Recruitment Localization:** Native ₹ LPA salary structures, Indian tech hub taxonomy (Bengaluru, Hyderabad, Mumbai, Pune, Gurugram), and IST shift benchmarks.

```mermaid
flowchart TD
    subgraph UI ["Frontend Layer (React 18 + Vite + Tailwind CSS)"]
        S1["1. Job & Resumes Ingestion"]
        S2["2. Rankings Leaderboard (Real-Time Weight Sliders)"]
        S3["3. Candidate Deep-Dive Drawer (XAI Insights)"]
        S4["4. Scorume (evaluation engine) (Cross-Pool Search)"]
        S5["5. Hiring History & Audit Analytics"]
    end

    subgraph API ["FastAPI Gateway (Uvicorn / Python 3.10+)"]
        JDR["/api/jd (Job Description Router)"]
        EVR["/api/evaluations (Evaluation & XAI Router)"]
    end

    subgraph NLP ["Local NLP & Extraction Core (Zero Cloud API)"]
        DP["document_parser.py (PyMuPDF / docx / White-Text Detection)"]
        SS["section_segmenter.py (Regex Anchoring & Top 15% Header Cutoff)"]
        EE["entity_extractor.py (spaCy EntityRuler + Date Interval Math)"]
        SE["semantic_engine.py (MiniLM-L6-v2 + 384d Cosine Similarity)"]
        SC["scoring_engine.py (Composite Formula + Deterministic XAI)"]
    end

    subgraph DB ["Data Persistence Layer"]
        PG[("PostgreSQL 16 + JSONB Columns\n(or Local SQLite Fallback)")]
    end

    S1 -->|POST /api/jd/parse| JDR
    S1 -->|POST /api/evaluations/batch| EVR
    S2 -->|GET /api/evaluations/{jd_id}| EVR
    S3 -->|GET /api/evaluations/candidate/{id}| EVR
    S4 -->|POST /api/evaluations/role-matcher/find-candidates| EVR
    S5 -->|GET /api/evaluations/history| EVR

    JDR --> DP
    JDR --> SS
    JDR --> EE
    EVR --> DP
    EVR --> SS
    EVR --> EE
    EVR --> SE
    EVR --> SC

    JDR --> PG
    EVR --> PG
```

---

# 2. Google Stitch & AI-Assisted Modernization Workflow

Scorume (evaluation engine)’s user interface and operational workflows were designed using **Google Stitch**, an advanced UI prototyping engine. 

### How Google Stitch Was Integrated
1. **Design Tokens & Screen Blueprints:** The baseline prototypes in `stitch_Scorume_technical_evaluation_engine/` provided production-grade wireframes:
   - `campaign_setup_ingestion/code.html` $\rightarrow$ Converted into modular `CampaignSetupView.jsx`, `JDInputPanel.jsx`, and `ResumeUploadZone.jsx`.
   - `candidate_rankings_leaderboard/code.html` $\rightarrow$ Converted into `CandidateRankingsView.jsx`, `RankingTable.jsx`, and `WeightSlidersBar.jsx`.
   - `candidate_deep_dive_drawer/code.html` $\rightarrow$ Converted into `CandidateDrawer.jsx`.
   - `role_matcher_finder/code.html` $\rightarrow$ Converted into `RoleMatcherFinderView.jsx`.
   - `evaluation_history/code.html` $\rightarrow$ Converted into `EvaluationHistoryView.jsx`.
2. **Indian Localization Adaptation:** Google Stitch prototypes originally featured US currency ($) and San Francisco hubs. We customized the design system for the Indian tech recruitment landscape:
   - Compensation tiers converted to **₹ LPA** (e.g., Target Budget: ₹28 - ₹42 LPA).
   - Regional deployment badges configured for **Asia-South (Mumbai & Bengaluru)** with Indian Data Protection Act compliance indicators.
   - Hub selections tailored to **Bengaluru, Hyderabad, Pune, Mumbai, and Gurugram**.
3. **AI-Assisted Engineering:** Modern AI development tools were leveraged to:
   - Generate diverse, production-representative synthetic technical resumes (covering full-stack AI, backend systems, QA engineering, data analytics, and adversarial keyword-stuffing cases).
   - Calibrate the linear cosine rescaling bounds ($[0.30, 0.80] \rightarrow [0.0, 100.0]$) against real-world tech candidate resumes.
   - Construct the curated 303-canonical skill taxonomy and 1,600+ alias map in `skills_taxonomy.json`.

---

# 3. Frontend Walkthrough, Screenshots & Video Presentation Script

Each section below presents the **captured screenshot**, **exact visible elements**, **recruitment workflow explanation**, and a **verbatim script** for a presenter/narrator.

---

### Screen 1: Job Benchmark & Resume Ingestion

![Screen 1: Job Setup and Resume Ingestion](screenshots/screen1_job_setup.png)

#### 1. Visible Features & Layout Breakdown
- **Global Header Navbar:**
  - Scorume (evaluation engine) India branding with smart badge `"Smart Technical Recruitment Engine"`.
  - Four top-level navigation pill tabs: `1. Job & Resumes`, `2. Candidate Rankings`, `3. Scorume (evaluation engine)`, `4. Hiring History`.
  - Operational indicators: `"Bengaluru Hub • Local AI Ready"`, `"HR Recruiter • Talent Acquisition"`.
- **Workflow Step Indicator:** `RECRUITMENT WORKFLOW / STEP 01: JOB & CANDIDATE SETUP`.
- **Active Drive Summary Bar:** `Senior Full-Stack AI Engineer • Bengaluru Hub (IST)` with quick action `"Load 12 Sample Resumes"`.
- **Left Panel (Job Description & Role Requirements):**
  - Toggle tabs: `Paste Text` vs `Upload JD File`.
  - Character & token counters (603 chars • ~77 tokens).
  - Pre-populated Indian tech job description (Bengaluru, ₹28-₹42 LPA, 4+ years minimum YoE, Python/FastAPI/React/PostgreSQL/Docker).
  - Extracted benchmark cards: `Required Experience (4.0 Years Minimum)` and `12 Core Technical Skills Detected` (interactive removable chips with `+ Add Skill`).
- **Right Panel (Upload Candidate Resumes):**
  - Drag-and-drop dropzone supporting PDF, DOCX, and TXT files.
  - Staging status counter (`0 Candidates Staged • 0.00 MB`).
  - Action button: `"Evaluate & Rank Candidates"`.
  - Privacy and compliance footer: `"Data Privacy: 100% On-Premise (DPDP India Compliant)"`, `"Avg Screening Time: 1.2s"`.

#### 2. Recruiter Workflow Implementation
1. The recruiter pastes a Job Description or uploads a JD document (`.pdf`, `.docx`).
2. The frontend triggers `POST /api/jd/parse`. The backend parses the text, extracts the role title, calculates minimum required years of experience, and tags 12 core technical skills using spaCy's `EntityRuler`.
3. The recruiter can fine-tune requirements by clicking `×` on any skill chip or adding new required competencies.
4. The recruiter drags a cohort of candidate resumes (or clicks `"Load 12 Sample Resumes"` for instant demonstration).
5. Clicking `"Evaluate & Rank Candidates"` dispatches `POST /api/evaluations/{jd_id}/batch`, processing all resumes in parallel.

#### 3. What to Speak (Video Presentation Script)
> *"Welcome to Scorume (evaluation engine), the on-premise intelligent technical evaluation platform built specifically for Indian talent acquisition teams. What you see right now is Screen 1: the Job Benchmark and Resume Ingestion workspace.*
> 
> *Notice how cleanly the recruitment drive is initialized. On the left, we define our target benchmark: a Senior Full-Stack AI Engineer based in our Bengaluru Hub with a target package of ₹28 to ₹42 LPA and a minimum of 4 years of experience. As soon as this JD is pasted or uploaded, our local NLP pipeline automatically extracts and normalizes 12 core competencies—including Python, FastAPI, React, PostgreSQL, Docker, and Natural Language Processing. As an HR manager, I can easily add or remove any skill chip with a single click.*
> 
> *On the right, we have our multi-file resume dropzone. What makes Scorume (evaluation engine) unique is that it operates 100% locally on-device. No candidate CV ever leaves your infrastructure—making it fully compliant with India's DPDP Act. Now, let's click 'Load 12 Sample Resumes' and witness our local NLP engine process the entire cohort in under 1.5 seconds."*

---

### Screen 2: Candidate Rankings Leaderboard & Real-Time Weight Calibration

![Screen 2: Candidate Rankings Leaderboard](screenshots/screen2_rankings.png)

#### 1. Visible Features & Layout Breakdown
- **Campaign Meta Header:** `Senior Full-Stack AI Engineer • 12 Candidates Screened • Req: 4+ Years YoE • 12 Core Technical Skills • Bengaluru (Hybrid) • Target Budget: ₹28 - ₹42 LPA`.
- **Top Utility Actions:** `"Job Setup / Upload More"`, `"Download Excel / CSV"`.
- **Interactive Scoring Weightage Calibration Bar:**
  - Three real-time weight sliders:
    - `Technical Skills Match (50%)`
    - `Project & Role Relevance (30%)`
    - `Tenure / YoE Match (20%)`
  - `"Reset Defaults"` button.
- **Cohort Filter Tabs:** `All Candidates (12)`, `⭐ Top Tier (≥80%)`, `👍 Moderate (65–79%)`, `⚠️ Low Match (<65%)`.
- **Leaderboard Table Columns:**
  - **Rank:** Numeric rank with tier badges (`#01`, `#02` ... `#12`).
  - **Candidate:** Candidate full name and direct email address.
  - **Experience (YoE):** Verified tenure with delta vs requirement (e.g., `5.6 yrs YoE (+1.6 yrs vs req)`).
  - **Match Score:** Composite percentage with visual status indicator (`80% TOP`, `75% FIT`, `26% LOW`).
  - **Matched Skills:** Visual skill pills showing direct canonical matches with overflow count (`+3 more`).
  - **Skill Gaps:** Warning badges highlighting missing mandatory requirements (`warning Machine Learning`, `warning JavaScript`).
  - **Action Button:** `"Inspect"` with forward arrow triggering the deep-dive drawer.

#### 2. Candidate Evaluation Results
| Rank | Candidate | Experience | Match Score | Key Matched Skills | Critical Gaps |
|:---:|:---|:---:|:---:|:---|:---|
| **#01** | **Omkar Chittar** | 5.6 yrs (+1.6 vs req) | **80% (TOP)** | Python, FastAPI, React, TypeScript, PostgreSQL, Docker (+3) | ML, JavaScript |
| **#02** | **Sergio Sabater Ruiz** | 4.5 yrs (+0.5 vs req) | **75% (FIT)** | Python, FastAPI, React, PostgreSQL, Docker (+1) | ML, JavaScript |
| **#03** | **Sean Chang** | 6.4 yrs (+2.4 vs req) | **75% (FIT)** | Python, FastAPI, React, TypeScript, PostgreSQL (+2) | ML, JavaScript |
| **#04** | **Abdoali Mazhar Zakir** | 1.2 yrs (-2.8 vs req) | **71% (FIT)** | Machine Learning, Python, FastAPI, React, JavaScript (+4) | TypeScript, pgvector |
| **#05** | **Ryan Morshead** | 5.3 yrs (+0.3 vs req) | **69% (FIT)** | Machine Learning, Python, JavaScript, Docker | TypeScript, pgvector |
| **#10** | **Anand Bhagwat** | 3.8 yrs (-0.2 vs req) | **26% (LOW)** | No exact matches | ML, Python |
| **#11** | **Cristina Attfield** | 2.9 yrs (-1.1 vs req) | **20% (LOW)** | No exact matches | ML, Python |
| **#12** | **Bharti Rajoriya** | 2.4 yrs (-1.6 vs req) | **15% (LOW)** | No exact matches | ML, Python |

#### 3. What to Speak (Video Presentation Script)
> *"Here on Screen 2 is our Candidate Rankings Leaderboard. In less than two seconds, all 12 candidate resumes were parsed, segmented, vectorized, and scored.*
> 
> *Notice our top-ranked candidate: Omkar Chittar with an 80% composite match score. Omkar brings 5.6 verified years of professional experience—exceeding our 4-year requirement by 1.6 years—and matches 8 out of 12 core competencies including Python, FastAPI, React, TypeScript, and Docker.*
> 
> *Now, look at the top calibration bar. Every organization has different hiring priorities. If your hiring manager says: 'We care primarily about senior tenure for this role', I can instantly drag the Tenure slider from 20% to 40%. The entire leaderboard re-ranks immediately in real-time in the browser without any lag or server re-computation.*
> 
> *Notice how candidates #10, #11, and #12—who have QA, data analytics, and graphic design backgrounds—are properly classified in the 15% to 26% Low Match tier. The algorithm objectively separates genuine full-stack AI engineers from unrelated disciplines. Now, let's click 'Inspect' on Omkar to see why he received an 80% score."*

---

### Screen 3: Candidate Deep-Dive & Deterministic Explainable AI (XAI) Drawer

![Screen 3: Candidate Deep Dive Drawer](screenshots/screen3_deepdive.png)

#### 1. Visible Features & Layout Breakdown
- **Candidate Header:**
  - Name: `Omkar Chittar`, Rank `#01`.
  - Contact Details: `omkar.chittar@omkarchittar.com • +1 (415) 890-4412`.
  - Education Summary: `M.S. in Computer Science & Engineering — Class of 2021 | B.E. in Computer Engineering`.
  - Document badge: `01_omkar_chittar.pdf • ✓ Smart Engine Verified`.
- **Score Header Card:**
  - Large Score Display: `80 / 100 • ⭐ Strong Match (Top Tier)`.
  - Three Sub-score Metric Cards:
    - **Skill Match:** `67%` (8 Required Skills Matched).
    - **Experience (YoE):** `100%` (`+1.6y`, 5.6y vs 4.0y Req).
    - **Project Depth:** `89%` (High Architectural Overlap).
- **Candidate Score Breakdown & HR Insights (Deterministic XAI):**
  - `[+33.5 pts] Direct Technical Skill Match:` Verified hands-on competency in 8 of 12 skills (Python, FastAPI, React, TypeScript, PostgreSQL, Docker).
  - `[+20.0 pts] Experience Tenure Alignment:` Verified career tenure of 5.6 Years exceeds 4.0-year minimum threshold by 1.6 years.
  - `[+26.7 pts] Project & Role Relevance:` Documented past engineering duties show consistent architectural overlap with this role.
- **Skill Compliance Matrix:**
  - *Direct Skills Matched (8):* Python, FastAPI, React, TypeScript, PostgreSQL, Docker, CI/CD, Natural Language Processing.
  - *Skill Gaps for this Role (4):* Machine Learning, JavaScript, pgvector, Large Language Models.
- **Verified Career History & Project Evidence:**
  - Comparison Banner: `Job Requirement 4.0+ Years YoE` vs `Candidate Verified Record 5.6 Years YoE`.
  - Tabbed Evidence Viewer: `Work Experience`, `Key Projects Portfolio`, `Education & Certifications`.
  - Raw extracted role history showing company names, dates (`Universal Creative & UDX (Jan 2023 - Present)`), and bullet points.
- **Footer Actions:** Candidate audit reference (`Ref: TR-IN-383D7A`), `"Download CV"`, `"Shortlist Candidate"`. Note: Per strict architectural standards, candidate records are immutable—no "Edit Resume" button is present.

#### 2. What to Speak (Video Presentation Script)
> *"This is Screen 3: the Candidate Deep-Dive Drawer. In traditional AI recruitment systems, recruiters are handed an arbitrary score with zero justification. Scorume (evaluation engine) changes this entirely through Deterministic Explainable AI.*
> 
> *Look at the Candidate Score Breakdown card. We don't just say Omkar scored 80%. We explain the exact mathematical point attributions: +33.5 points derived from matching 8 core skills, +20.0 points from fulfilling 100% of the required 4-year tenure, and +26.7 points from the 89% semantic overlap between his past project achievements and the JD responsibilities.*
> 
> *Below that, the Skill Compliance Matrix provides immediate transparency: green checkmarks show his verified skills—like FastAPI, React, and PostgreSQL—while amber warning tags clearly highlight his skill gaps, such as pgvector and Large Language Models.*
> 
> *Further down, under Verified Career History, we present the exact extracted work history from his CV, verifying his 5.6 years of tenure without double-counting overlapping roles. An HR recruiter can immediately verify qualifications, download the CV, or click 'Shortlist Candidate'."*

---

### Screen 4: Scorume (evaluation engine) & Cross-Drive Candidate Search

![Screen 4: Scorume (evaluation engine)](screenshots/screen4_talent_matcher.png)
![Screen 4: Reverse Matcher](screenshots/screen4_reverse_matcher.png)

#### 1. Visible Features & Layout Breakdown
- **Module Header:** `Scorume (evaluation engine) & Candidate Finder • Evaluation Matcher Ready`.
- **Dual Mode Switcher Tabs:** `Search Candidates by Role` vs `Reverse Match Resume to Jobs`.
- **Search Criteria Configuration:**
  - Requisition Code: `REQ-BLR-2026-088`.
  - Target Role Title & Indian Hub selector: `Core Platform & AI (Bengaluru)`, `Distributed Infra (Hyderabad)`, `Data Engineering (Pune)`, `Fintech Engineering (Mumbai)`.
  - Minimum Experience input: `5.0 YoE`.
  - Candidate Scope: `All Evaluated Resumes Active (13 candidates across past hiring drives)`.
  - Mandatory Skills: `Kubernetes`, `PyTorch / Ray`, `C++`, `Go`, `Distributed Training`.
  - Scoring Presets: `Balanced (40/30/30)`, `Tech Heavy (60/20/20)`, `Tenure Heavy (30/20/50)`.
- **Search Results Feed:**
  - Status indicator: `Search completed in 180ms • 13 Qualified Candidates Ranked across past hiring drives`.
  - Results Table columns: Rank & Score, Candidate & Sourced Campaign (`01_omkar_chittar.pdf`, `02_sean_chang.docx`), Experience with tenure delta, Skill Match Analysis, Recruiter Rationale string, Action button.
- **Reverse Resume Matcher Sub-view:**
  - Text area for pasting an unassigned candidate CV.
  - Action button: `"Match Against Active Job Openings"`, which evaluates the candidate against all open JD benchmarks in the database and returns fit tiers (`Strong`, `Moderate`, `Low`).

#### 2. What to Speak (Video Presentation Script)
> *"On Screen 4, we showcase Scorume (evaluation engine)'s cross-drive candidate search and role matcher. Too often in enterprise hiring, once a campaign ends, qualified resumes sit in an ATS graveyard.*
> 
> *With Scorume (evaluation engine), recruiters can instantly search across all previously vetted candidates from past hiring drives across India. Here, we're opening a new requisition for a Senior ML Infrastructure Engineer requiring Kubernetes, PyTorch, C++, and Go.*
> 
> *In just 180 milliseconds, Scorume (evaluation engine) scans our candidate database, evaluates skill overlap and career tenure against the new criteria, and provides custom recruiter rationales for each match.*
> 
> *Even more powerful is the 'Reverse Match Resume to Jobs' tab. When a star candidate submits a general application, you simply paste their CV here, and Scorume (evaluation engine) reverse-matches them across all open company requisitions in Bengaluru, Mumbai, and Hyderabad, highlighting where they have the strongest potential fit."*

---

### Screen 5: Hiring History, Audit Records & Recruitment Analytics

![Screen 5: Hiring History](screenshots/screen5_history.png)

#### 1. Visible Features & Layout Breakdown
- **Module Header:** `RECRUITMENT ARCHIVE / AUDIT RECORDS • Hiring Drives & Evaluation History (India Edition)`.
- **Top Action Bar:** `"Export Audit Log"`, `"New Hiring Drive"`.
- **Four High-Level KPI Cards:**
  1. **Total Hiring Drives:** `5 Job Openings` (`check_circle Active in local storage`).
  2. **Resumes Screened:** `48 Candidates` (`verified Smart ATS Parsed`).
  3. **Top-Tier Shortlist Yield:** `6.2% High Match` (`Threshold score ≥ 80%`).
  4. **Avg Screening Speed:** `1.4s per cohort` (`bolt Local On-Device AI`).
- **Department Filter Tabs:** `All Roles (5)`, `Engineering`, `Product & Design`, `Data & AI`.
- **Historical Hiring Cohorts Table:**
  - **Drive Code & Date:** `RUN-6533 (Nov 18, 2026)`, `RUN-CC5B (Nov 17, 2026)`, etc.
  - **Role & Benchmark Spec:** e.g., `Senior Full-Stack AI Engineer • Req: 4+ yrs • 12 skills evaluated`.
  - **Location / Dept:** `Core AI Infrastructure`.
  - **Resumes Processed:** `12 Resumes (100% processed)`.
  - **Top Ranked Candidates:** Mini-chips showing top candidate names and their scores (`Bharti 15%`, `Anand 26%`, `Cristina 20%`).
  - **Calibrated Weights:** `50/30/20`.
  - **Status:** `COMPLETED`.
  - **Action Button:** `"View Results"` with arrow to jump back to that cohort's leaderboard.

#### 2. What to Speak (Video Presentation Script)
> *"Finally, Screen 5 provides the executive view: Hiring History and Audit Analytics. Every hiring drive executed in Scorume (evaluation engine) is permanently versioned with full audit trails.*
> 
> *At the top, our aggregate recruitment metrics show 48 candidates screened across 5 hiring drives with an average screening latency of 1.4 seconds per cohort, yielding a 6.2% top-tier shortlist rate.*
> 
> *Below, every historical drive is logged with its unique Run ID, the exact benchmark criteria used, the department, candidate cohort size, top scorers, and calibrated scoring weights. With the 'Export Audit Log' feature, compliance teams can export complete evaluation trails for regulatory reporting.*
> 
> *This completes the end-to-end recruitment journey in Scorume (evaluation engine). Now, let's explore the backend engineering, data schemas, and mathematical algorithms that power this entire system."*

---

# 4. Backend Deep Dive: Workflows, Schemas, Classes & Functions

The backend is built with **FastAPI**, **SQLAlchemy ORM** (targeting PostgreSQL with JSONB columns, with an automatic SQLite3 fallback), and five dedicated local NLP service modules.

All service functions have been systematically documented in the codebase using `# Role:` and `# Workflow:` comments.

---

### System Configuration (`app/config.py`)

The `Settings` class (`app/config.py`) defines all environmental variables, model identifiers, adversarial detection thresholds, and scoring parameters:

```python
class Settings(BaseModel):
    APP_NAME: str = "Scorume (evaluation engine)"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database URLs
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@postgres:5432/scorume"
    SQLITE_FALLBACK_URL: str = "sqlite:///./scorume_local.db"
    USE_SQLITE_FALLBACK: bool = False

    # Local NLP Models (Zero Cloud API Keys)
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    SPACY_MODEL_NAME: str = "en_core_web_sm"
    SKILLS_TAXONOMY_PATH: Path = BASE_DIR / "data" / "skills_taxonomy.json"

    # Adversarial Keyword-Stuffing & White-Text Thresholds
    MIN_VISIBLE_FONT_SIZE: float = 2.0        # Font sizes < 2.0pt are flagged as microscopic
    WHITE_COLOR_INT_THRESHOLD: int = 16777215 # 24-bit sRGB int for #FFFFFF
    NEAR_WHITE_RGB_MIN: int = 248             # R, G, B >= 248 flagged as near-white
    HIDDEN_TEXT_INTEGRITY_PENALTY: float = 35.0

    # Multi-Vector Semantic Matching Thresholds
    EXACT_MATCH_THRESHOLD: float = 0.95       # Cosine >= 0.95 treated as exact/synonym match
    SEMANTIC_ADJACENT_THRESHOLD: float = 0.72 # 0.72 <= Cosine < 0.95 awarded soft credit
    IMPLICIT_CONTEXT_THRESHOLD: float = 0.68  # Sentence-chunk context threshold
    PARTIAL_CREDIT_MULTIPLIER: float = 0.60   # Awards 60% of cosine similarity value

    # MiniLM Cosine Rescaling Bounds
    SEMANTIC_MIN_BASELINE: float = 0.30       # Unrelated technical text floor
    SEMANTIC_MAX_CEILING: float = 0.80        # Exceptional domain alignment ceiling

    # Default Scoring Weights
    DEFAULT_WEIGHT_SKILLS: float = 0.50
    DEFAULT_WEIGHT_SEMANTIC: float = 0.30
    DEFAULT_WEIGHT_EXPERIENCE: float = 0.20
```

---

### Database Layer & ORM Entities (`app/database.py` & `app/models.py`)

The persistence layer uses a cross-dialect `JSONBType` pattern that uses native PostgreSQL `JSONB` in production and gracefully adapts to SQLite `JSON` in local development environments.

#### Relational Schema Architecture

```mermaid
erDiagram
    job_descriptions ||--o{ candidate_evaluations : "evaluates (1:N)"
    
    job_descriptions {
        string id PK "UUID"
        string title "Role Title"
        text raw_text "Full JD Text"
        jsonb required_skills "List of canonical skills"
        float min_experience_years "Tenure benchmark"
        jsonb education_reqs "Degree requirements"
        datetime created_at "Timestamp (UTC)"
    }

    candidate_evaluations {
        string id PK "UUID"
        string jd_id FK "References job_descriptions.id"
        string candidate_name "Candidate Name"
        string email "Contact Email"
        string phone "Contact Phone"
        string filename "Source File Name"
        float experience_years "Calculated non-overlapping tenure"
        string education_summary "Degree & Institution"
        float overall_score "Composite (0-100)"
        float skill_score "Skill Alignment Sub-score"
        float semantic_score "Domain Relevance Sub-score"
        float experience_score "Tenure Fulfillment Sub-score"
        jsonb matched_skills "Directly matched skills"
        jsonb partial_skills "Soft credit matches with similarity"
        jsonb missing_skills "Missing mandatory skills"
        jsonb explanations "Deterministic XAI bullet points"
        jsonb segmented_sections "Parsed resume sections"
        jsonb integrity_flags "Detected adversarial spans"
        datetime created_at "Timestamp (UTC)"
    }
```

#### Core Repository Query Helpers in `app/models.py`
- `db_get_jd_by_id(db, jd_id)`: Fetches a single JD record by UUID.
- `db_list_jds(db, limit=20)`: Lists recent JDs ordered by `created_at` descending.
- `db_update_jd_benchmark(db, jd, required_skills, min_experience_years, title)`: Commits updated recruiter benchmark chips to the database.
- `db_get_evaluations_for_jd(db, jd_id)`: Returns all candidate evaluations for a JD ordered by `overall_score` descending.
- `db_delete_evaluations_for_jd(db, jd_id, filenames)`: Removes prior evaluation rows for specific filenames upon re-upload to prevent duplicate ranking entries.
- `db_get_candidate_evaluation_by_id(db, evaluation_id)`: Retrieves a candidate evaluation record for the Module 5 deep-dive drawer.
- `db_get_all_evaluations(db, limit=500)`: Fetches candidate records across all historical campaigns for cross-pool matching.

---

### Validation & Serialization Schemas (`app/schemas.py`)

All API payloads inherit from `CompatibleBaseModel`, providing seamless dual compatibility across Pydantic v1 and Pydantic v2.

#### 1. Job Description Schemas
- `JDParseRequest`: Validates `raw_text` (min 10 chars), optional `title`, and optional `min_experience_years`.
- `JDSkillsUpdateRequest`: Validates recruiter modifications to `required_skills`, `min_experience_years`, and `recalculate_candidates` flag.
- `JobDescriptionResponse`: Serializes the persisted JD benchmark back to the UI.

#### 2. Evaluation & Ranking Schemas
- `PartialSkillSchema`: Represents semantic adjacent matches:
  - `required`: Name of the required skill (e.g., `"Docker"`).
  - `candidate_has`: Skill demonstrated by the candidate (e.g., `"Kubernetes"`).
  - `similarity`: Cosine similarity float in $[0.0, 1.0]$.
  - `credit_awarded`: Partial credit awarded ($0.6 \times \text{similarity}$).
  - `match_type`: `"semantic_adjacent"` or `"implicit_context"`.
- `IntegrityFlagSchema`: Serializes layout anomalies (`location`, `reason`, `font_size`, `color_hex`, `snippet`).
- `CandidateRankingItemSchema`: Complete leaderboard row schema containing `rank`, `candidate_name`, `email`, `experience_years`, `overall_score`, `skill_score`, `semantic_score`, `experience_score`, `matched_skills`, `partial_skills`, and `missing_skills`.
- `CandidateDetailResponse`: Extends `CandidateRankingItemSchema` with `segmented_sections`, `jd_title`, and `jd_required_skills` for the Module 5 drawer.
- `BatchEvaluationResponse`: Envelopes the list of candidates for a campaign with campaign metadata.

#### 3. Cross-Pool Matcher & History Schemas
- `RoleMatcherRequest`: Input parameters for cross-drive searches (`role_title`, `department`, `min_experience_years`, `required_skills`, `weight_skills`, `weight_semantic`, `weight_experience`).
- `RoleMatcherCandidateItem`: Ranked candidate returned by cross-drive search with custom `rationale` and `verified_years_diff`.
- `ReverseRoleMatchItem`: Evaluates a single candidate against all active JDs, returning fit scores and tiers (`Strong`, `Moderate`, `Low`).
- `EvaluationHistoryResponse`: Serializes aggregated campaign KPIs (`total_evaluations`, `resumes_screened`, `avg_match_yield`, `avg_batch_latency`) and historical `HistoryRunItem` records.

---

### Service 1: Document Parser & Adversarial Keyword-Stuffing Detector (`app/services/document_parser.py`)

Handles document ingestion from PDF, DOCX, and plain text formats while inspecting layout elements to detect adversarial evasion tactics.

#### Functions and Technical Workflows:
1. `_srgb_int_to_rgb(color_int: int) -> tuple[int, int, int]`
   - **Role:** Converts a PyMuPDF 24-bit sRGB integer into RGB components.
   - **Workflow:** Bitwise right-shifts: `(color >> 16) & 255` (Red), `(color >> 8) & 255` (Green), `color & 255` (Blue).
2. `_srgb_int_to_hex(color_int: int) -> str`
   - **Role:** Converts integer color codes into standard `#RRGGBB` hex strings.
3. `_is_white_or_near_white(color_val: Any) -> tuple[bool, str]`
   - **Role:** Evaluates whether a text span color is white (`#FFFFFF`) or near-white (`R, G, B \ge 248`).
   - **Workflow:** Inspects integers, normalized RGB float tuples ($0.0-1.0$), 8-bit integer tuples, or hex strings. Returns `(True, hex_code)` if the span represents camouflaged text.
4. `_normalize_whitespace(text: str) -> str`
   - **Role:** Normalizes inconsistent whitespace characters within extracted text.
   - **Workflow:** Cleans `\r\n` line endings, collapses consecutive tab and space characters, and bounds multiple blank lines to a maximum of 2.
5. `_extract_pdf_with_fitz(file_bytes: bytes, filename: str) -> ParsedDocument`
   - **Role:** Primary PDF extractor using PyMuPDF (`fitz`).
   - **Workflow:** Opens the document via `fitz.open(stream=file_bytes)`. Iterates through text blocks and line spans via `page.get_text("dict")`. Inspects `span["size"]` for microscopic text ($< 2.0\text{ pt}$) and `span["color"]` for white font ($16777215$). Excludes suspicious spans from `clean_visible_text`, records `integrity_flags`, calculates an integrity penalty, and returns `ParsedDocument`.
6. `_extract_pdf_with_pdfplumber(file_bytes: bytes, filename: str) -> ParsedDocument`
   - **Role:** Fallback PDF extractor when running in minimal container environments.
   - **Workflow:** Opens byte stream with `pdfplumber.open()`. Inspects `page.chars` for `non_stroking_color` and `size` to detect white text and micro-fonts.
7. `_extract_docx_table_recursive(...) -> tuple[int, int]`
   - **Role:** Recursively extracts text from DOCX tables and nested sub-tables.
   - **Workflow:** Traverses table rows and cells, tracks visited `_tc` IDs to prevent duplicate text from merged cells, and inspects nested paragraphs.
8. `_inspect_docx_paragraph(para, location_label, flags) -> tuple[str, str, int, int]`
   - **Role:** Inspects individual runs inside Word paragraphs for hidden text.
   - **Workflow:** Checks `run.font.size.pt < 2.0`, `run.font.color.rgb == "FFFFFF"`, and Word XML vanishing tags (`<w:vanish/>`).
9. `_extract_docx(file_bytes: bytes, filename: str) -> ParsedDocument`
   - **Role:** Extracts text and structural metadata from Microsoft Word DOCX files.
   - **Workflow:** Ingests document body, headers, footers, and tables in visual reading order while running layout integrity checks.
10. `extract_document(file_bytes: bytes, filename: str) -> ParsedDocument`
    - **Role:** Main entrypoint dispatcher for extracting and validating resume files.
    - **Workflow:** Inspects filename extension and file magic bytes (`%PDF` vs `PK`), routes to PDF or DOCX handlers, and falls back to UTF-8 text decoding.

---

### Service 2: Section-Aware Segmenter (`app/services/section_segmenter.py`)

Splits raw text into structured semantic blocks using case-insensitive regex anchors, preventing the common ATS bug where degree titles or project descriptions are confused with work history.

#### Functions and Technical Workflows:
1. `_match_header_line(line: str) -> tuple[str | None, str | None]`
   - **Role:** Detects if a text line represents a section heading or inline header.
   - **Workflow:** Tests standalone lines ($\le 55$ chars, no trailing period) against `SECTION_HEADER_PATTERNS` (`experience`, `projects`, `skills`, `education`, `summary`, `certifications`). Also tests inline header prefixes (e.g., `"Technical Skills: Python, FastAPI, React"`).
2. `segment_resume(raw_text: str) -> dict[str, str]`
   - **Role:** Segments raw resume text into structured section buckets.
   - **Workflow:**
     - Allocates the top 15% of document lines prior to the first section header to `header_contact`.
     - Lines under `WORK EXPERIENCE` / `EMPLOYMENT` map to `experience`.
     - Lines under `PROJECTS` map to `projects`.
     - Lines under `SKILLS` / `TECH STACK` map to `skills`.
     - Lines under `EDUCATION` / `QUALIFICATIONS` map to `education`.
     - If fewer than 1 canonical section header matches, logs a warning and falls back to full-text context.
3. `segment_job_description(jd_text: str) -> dict[str, Any]`
   - **Role:** Segments a job description into structured role components.
   - **Workflow:** Extracts the job title from opening lines, separates `responsibilities` from `requirements` using regex anchors, extracts explicit education requirement phrases (e.g., `"Bachelor's in Computer Science"`), and returns a structured dictionary.

---

### Service 3: Entity Extractor & Non-Overlapping Experience Math (`app/services/entity_extractor.py`)

Manages the 303-canonical skill taxonomy, executes boundary-aware regex and spaCy entity extraction, and performs non-overlapping date interval math.

#### Functions and Technical Workflows:
1. `_load_taxonomy(self)`
   - **Role:** Loads the curated JSON skill taxonomy and aliases into memory.
   - **Workflow:** Ingests `skills_taxonomy.json`, populates `canonical_skills`, parses the `alias_to_canonical` dictionary (1,600+ aliases), and registers the `semantic_adjacency_map`.
2. `_init_spacy_pipeline(self)`
   - **Role:** Sets up the spaCy NLP pipeline and EntityRuler.
   - **Workflow:** Loads `en_core_web_sm` (or `spacy.blank("en")`), attaches a custom `entity_ruler` component, and adds pattern dictionaries for all taxonomy aliases. Configures exact-case rules for ambiguous acronyms (`"C"`, `"R"`, `"Go"`).
3. `_compile_regex_patterns(self)`
   - **Role:** Compiles word-boundary regular expressions for technical skill aliases.
   - **Workflow:** Sorts aliases longest-first. Uses custom non-alphanumeric lookbehinds and lookaheads (`(?<![A-Za-z0-9_])...(?![A-Za-z0-9_])`) so skills containing punctuation (`C++`, `C#`, `.NET`, `Node.js`, `CI/CD`) match cleanly.
4. `extract_skills(self, text: str) -> list[str]`
   - **Role:** Extracts recognized canonical skills from text using spaCy and regexes.
   - **Workflow:** Runs the spaCy EntityRuler pipeline, scans with boundary-aware regex matchers, resolves aliases to canonical names, deduplicates, and preserves the order of first appearance.
5. `normalize_skill_name(self, raw_skill: str) -> str`
   - **Role:** Maps raw user-entered skill phrases to official canonical taxonomy names.
6. `_parse_month_year_token(...) -> int`
   - **Role:** Converts a parsed month and year token into an absolute integer month index (`year * 12 + month`). Handles `"Present"`, `"Current"`, and two-digit year representations.
7. `_extract_merged_months_from_text(text: str, reference_date=None) -> int`
   - **Role:** Parses date ranges from text and calculates total non-overlapping duration in months.
   - **Workflow:** Matches patterns like `"Jan 2021 - Present"`, `"06/2019 - 08/2022"`, `"2020 - 2024"`. Converts matches to `(start_month_idx, end_month_idx)` intervals. Filters out degree graduation lines. **Sorts intervals by start date and merges overlapping ranges:**
     $$\text{If } \text{start}_{i} \le \text{end}_{i-1} \implies \text{merged\_interval} = (\text{start}_{i-1}, \max(\text{end}_{i-1}, \text{end}_{i}))$$
     This guarantees candidates working concurrent jobs or parallel internships are never credited with duplicate tenure.
8. `calculate_experience_years(experience_section_text: str, full_text: str = "") -> float`
   - **Role:** Calculates candidate's total non-overlapping professional work experience in years.
   - **Workflow:** Analyzes the `experience` section first. If 0 months are detected, checks full text date ranges and explicit summary phrases (e.g., `"5+ years of experience"`). Converts total non-overlapping months to years: $\text{round}(\text{months} / 12.0, 1)$.
9. `extract_jd_min_experience_years(jd_text: str) -> float`
   - **Role:** Extracts minimum required experience years from a job description.
   - **Workflow:** Evaluates regexes matching phrases such as `"Minimum 4+ years of experience"` or `"Experience: 3-5 years"`, returning the lower bound (e.g., `4.0`).
10. `extract_contact_metadata(header_text: str, full_text: str, filename: str) -> dict[str, str]`
    - **Role:** Extracts candidate name, email, and phone number.
    - **Workflow:** Matches email and phone regexes. Scans the top lines of `header_contact` to extract candidate name while filtering out role titles, URLs, and numbers. Falls back to filename stem.
11. `extract_education_summary(education_section_text: str, full_text: str) -> str`
    - **Role:** Extracts degree level and academic institution into a concise 1-line summary.

---

### Service 4: Multi-Vector Semantic Engine (`app/services/semantic_engine.py`)

Implements the vector embedding and skill adjacency matrix using `sentence-transformers/all-MiniLM-L6-v2` with vectorized NumPy / scikit-learn cosine similarity matrices.

#### 1. The Three-Tier Multi-Vector Skill Alignment Algorithm
For every required skill $s_i \in \text{JD\_Skills}$:
1. **Tier 1: Exact / Canonical Match:**
   $$\text{If } s_i \in \text{Candidate\_Skills} \implies \text{Match} = 1.0$$
2. **Tier 2: Semantic Adjacent Match (Soft Credit):**
   Computes dense embeddings $E(s_i)$ and candidate skill embeddings $E(c_j)$. Computes cosine similarity matrix:
   $$\cos(E(s_i), E(c_j)) = \frac{E(s_i) \cdot E(c_j)}{\|E(s_i)\|_2 \|E(c_j)\|_2}$$
   Merges with curated domain adjacency priors from `skills_taxonomy.json`. If $0.72 \le \cos < 0.95$, awards partial credit:
   $$\text{Credit} = 0.60 \times \cos$$
   and records: `{"required": s_i, "candidate_has": c_best, "similarity": round(cos, 2)}`.
3. **Tier 3: Implicit Context Check:**
   If still unmatched, splits the candidate's experience and project sections into sentence chunks and encodes them. If any sentence exceeds the $0.68$ semantic threshold, awards implicit context credit.
4. **Missing Skill:**
   If $< 0.72$, classifies into `missing_skills` (credit = 0.0).

#### 2. Functions and Technical Workflows:
1. `vectorized_cosine_similarity(mat_a: np.ndarray, mat_b: np.ndarray) -> np.ndarray`
   - **Role:** Computes pairwise cosine similarity between two 2D embedding matrices using scikit-learn or NumPy matrix dot products.
2. `SemanticEngine._load_model(self)`
   - **Role:** Loads local `all-MiniLM-L6-v2` model weights on CPU. If running in an air-gapped container without cached weights, initializes the deterministic NumPy Sublinear TF-IDF + Concept Vectorizer fallback.
3. `SemanticEngine.encode_texts(self, texts: list[str]) -> np.ndarray`
   - **Role:** Transforms text batches into L2-normalized 384-dimensional dense vectors.
4. `SemanticEngine.compute_skill_pair_similarity_matrix(...) -> np.ndarray`
   - **Role:** Builds a pairwise cosine similarity matrix between required skills and candidate skills, combining neural MiniLM embeddings with curated domain adjacency priors.
5. `SemanticEngine.split_into_sentence_chunks(text: str) -> list[str]`
   - **Role:** Chunks continuous experience and project text into individual sentence/bullet strings ($\ge 20$ chars).
6. `SemanticEngine.evaluate_skill_alignment(...) -> SkillAlignmentResult`
   - **Role:** Executes the 3-tier matching pipeline, returning `matched_skills`, `partial_skills`, `missing_skills`, and `total_partial_credit`.
7. `SemanticEngine.compute_section_semantic_similarity(jd_text, cand_text) -> tuple[float, float]`
   - **Role:** Encodes JD responsibilities against candidate experience/projects text. Computes raw cosine similarity and linearly rescales $[0.30, 0.80] \rightarrow [0.0, 100.0]$:
     $$\text{Score}_{\text{semantic}} = \min\left(100.0, \max\left(0.0, \frac{\cos - 0.30}{0.80 - 0.30} \times 100.0\right)\right)$$

---

### Service 5: Mathematical Scoring Engine & XAI Reasoning Generator (`app/services/scoring_engine.py`)

Computes normalized sub-scores, combines them via calibrated weights, and generates deterministic explainable AI bullets detailing exact point attributions.

#### 1. Mathematical Scoring Formula

The evaluation engine computes three independent sub-scores on a 0–100 scale:

1. **Skill Alignment Sub-score ($S_{\text{skill}}$):**
   $$S_{\text{skill}} = \min\left(100.0, \left( \frac{|\text{Matched Skills}| + \sum \text{Partial Credit}}{|\text{JD Required Skills}|} \right) \times 100\right)$$

2. **Semantic Context Sub-score ($S_{\text{semantic}}$):**
   Linearly rescales MiniLM cosine similarity from $[0.30, 0.80]$ onto $[0.0, 100.0]$.

3. **Quantitative Experience Sub-score ($S_{\text{exp}}$):**
   $$S_{\text{exp}} = \begin{cases} 
   100.0 & \text{if } \text{JD\_Min\_Years} \le 0 \\
   100.0 & \text{if } \text{Candidate\_Years} \ge \text{JD\_Min\_Years} \\
   \left( \frac{\text{Candidate\_Years}}{\text{JD\_Min\_Years}} \right) \times 100 & \text{if } \text{Candidate\_Years} < \text{JD\_Min\_Years}
   \end{cases}$$

4. **Composite Overall Match Score:**
   $$\text{Overall Score} = \text{round}\Big((W_s \cdot S_{\text{skill}}) + (W_c \cdot S_{\text{semantic}}) + (W_e \cdot S_{\text{exp}}), 1\Big)$$
   *Default Weights:* $W_s = 0.50$ (Skills), $W_c = 0.30$ (Semantic), $W_e = 0.20$ (Experience). Weights are normalized if user sliders don't sum to 1.0:
   $$W'_i = \frac{W_i}{W_s + W_c + W_e}$$

#### 2. Functions and Technical Workflows:
1. `compute_skill_subscore(alignment: SkillAlignmentResult) -> float`
   - **Role:** Calculates $S_{\text{skill}}$ on a 0–100 scale from exact matches and soft credits.
2. `compute_experience_subscore(candidate_years: float, jd_min_years: float) -> float`
   - **Role:** Calculates $S_{\text{exp}}$ based on tenure fulfillment.
3. `generate_score_explanations(result: CandidateScoringResult) -> list[str]`
   - **Role:** Produces 4–5 deterministic Explainable AI (XAI) bullets with exact point attributions:
     - **Skill Strength Bullet:** Attributed points: $\text{round}\left(\frac{|\text{Matched}|}{\text{Total JD Skills}} \times 100 \times W_s, 1\right)$. Lists verified skills.
     - **Semantic Bridging Bullet:** Attributed points from soft credit: $\text{round}\left(\frac{\sum \text{Partial Credit}}{\text{Total JD Skills}} \times 100 \times W_s, 1\right)$. Cites specific substitutions (e.g., *"lacks Docker explicitly but demonstrates Kubernetes (88% semantic similarity)"*).
     - **Experience Verdict Bullet:** Attributed points: $\text{round}(S_{\text{exp}} \times W_e, 1)$. Compares candidate tenure against benchmark.
     - **Domain Context Bullet:** Attributed points: $\text{round}(S_{\text{semantic}} \times W_c, 1)$. Classifies semantic alignment as High ($\ge 75\%$), Moderate ($\ge 50\%$), or Low ($< 50\%$).
     - **Critical Gaps & Integrity Verdict Bullet:** Enumerates missing mandatory skills. Appends adversarial alert if hidden white/microscopic text was flagged.
4. `calculate_candidate_scores(...) -> CandidateScoringResult`
   - **Role:** Orchestrates the multi-vector scoring pipeline, calculates sub-scores, applies calibrated weights, generates XAI bullets, and returns `CandidateScoringResult`.

---

### API Routers: Endpoint Specifications & Handlers (`app/routers/`)

#### 1. Job Description Router (`jd_router.py`)
- `POST /api/jd/parse` (Status: `201 Created`):
  - Accepts multipart form data or JSON body containing raw JD text or uploaded `.pdf`/`.docx` file.
  - Segments the JD, extracts role title, tenure benchmark, and technical skills.
  - Persists to `job_descriptions` table and returns `JobDescriptionResponse`.
- `PUT /api/jd/{jd_id}/skills` (Status: `200 OK`):
  - Accepts `JDSkillsUpdateRequest`. Normalizes skill names against taxonomy.
  - Updates benchmark in database.
  - When `recalculate_candidates=True`, automatically re-scores all previously evaluated candidates against the updated benchmark so rankings stay synchronized.
- `GET /api/jd` (Status: `200 OK`): Lists recent JD benchmarks.
- `GET /api/jd/{jd_id}` (Status: `200 OK`): Retrieves a single JD benchmark.

#### 2. Evaluation & Ranking Router (`evaluation_router.py`)
- `POST /api/evaluations/{jd_id}/batch` (Status: `201 Created`):
  - Accepts `files: list[UploadFile]` (supports 10–50+ PDF/DOCX resumes simultaneously).
  - Iterates through files: extracts text & layout integrity $\rightarrow$ segments sections $\rightarrow$ extracts contact, skills, and tenure $\rightarrow$ executes multi-vector scoring $\rightarrow$ persists `CandidateEvaluation` records.
  - Returns `BatchEvaluationResponse` with all ranked candidates sorted by `overall_score` descending.
- `POST /api/evaluations/{jd_id}/manual` (Status: `201 Created`):
  - Accepts `ManualCandidateCreateRequest`. Evaluates a typed or pasted resume directly in the browser without requiring a file upload.
- `GET /api/evaluations/{jd_id}` (Status: `200 OK`):
  - Returns all ranked candidates for a specific JD benchmark.
- `GET /api/evaluations/candidate/{evaluation_id}` (Status: `200 OK`):
  - Returns `CandidateDetailResponse` for the Module 5 deep-dive drawer with complete XAI explanations and parsed resume sections.
- `POST /api/evaluations/role-matcher/find-candidates` (Status: `200 OK`):
  - Accepts `RoleMatcherRequest`. Evaluates candidates across all historical campaign pools against new role criteria. Returns ranked `RoleMatcherCandidateItem` list with recruiter rationales.
- `POST /api/evaluations/role-matcher/reverse-match` (Status: `200 OK`):
  - Evaluates an individual candidate or raw resume text across all open JD benchmarks, returning role fit scores and tiers (`Strong`, `Moderate`, `Low`).
- `GET /api/evaluations/history` (Status: `200 OK`):
  - Returns `EvaluationHistoryResponse` with aggregated recruitment KPIs and historical campaign run logs.
- `GET /api/evaluations/{jd_id}/export-csv` (Status: `200 OK`):
  - Streams the candidate rankings leaderboard as a downloadable CSV spreadsheet.

---

# 5. Production Deployment & Verification Guide

### Docker Multi-Container Architecture & Namespace Isolation
Scorume (evaluation engine) is packaged with project namespace `scorume` via `docker-compose.yml` into three containerized services connected by the `scorume_network` bridge network:
1. `scorume_postgres`: PostgreSQL 16 Alpine with initialized database `scorume` and persistent volume `scorume_postgres_data`.
2. `scorume_backend`: FastAPI + Uvicorn server running Python 3.10+, PyMuPDF, python-docx, spaCy `en_core_web_sm`, and `sentence-transformers/all-MiniLM-L6-v2`.
3. `scorume_frontend`: Node.js / Vite development and production preview server serving the React 18 application on port 5173.

### Startup & Verification Commands
```powershell
# 1. Start all containers in detached mode
docker compose up -d

# 2. Verify all 3 containers are healthy and running
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 3. Check backend health endpoint
curl http://localhost:8000/health
# Expected response: {"status":"healthy","embedding_backend":"sentence-transformers (all-MiniLM-L6-v2 local)","canonical_skills_count":303}

# 4. Open the application in browser
Start-Process "http://localhost:5173"
```

---
*Documentation compiled and verified on November 19, 2026. All screenshots captured directly from live application instance at `http://localhost:5173`.*

