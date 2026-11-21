# Scorume (evaluation engine) — Local AI-Based Resume Matching & Candidate Ranking Engine

A complete, production-grade full-stack prototype of **Scorume (evaluation engine)**: an Explainable AI (XAI) Candidate Evaluation & Resume Ranking System that runs **100% locally** without paid external LLM API keys (zero OpenAI/Anthropic dependencies).

The engine ingests Job Descriptions (JD) and batches of 10–50+ candidate resumes (`PDF` and `DOCX`), inspects layout spans to detect adversarial white-text keyword stuffing, segments documents into structured semantic blocks, extracts canonical technical skills via a 303-skill taxonomy (`1,688` aliases) and spaCy `EntityRuler`, computes non-overlapping work experience tenure, evaluates multi-vector semantic similarity using `sentence-transformers/all-MiniLM-L6-v2` and vectorized cosine matrices, persists evaluations in PostgreSQL `JSONB` tables, and serves an interactive React 18 + Tailwind CSS analytics dashboard with real-time weight sliders.

## 1. System Architecture & Monorepo Structure

```text
resume-matcher-ai/
├── docker-compose.yml                 # Orchestrates PostgreSQL 15, FastAPI Backend, and React Vite Frontend
├── README.md                          # Architecture, Mathematical Scoring Formulas, and Setup Guide
├── sample_data/
│   ├── sample_jd_fullstack_ai.txt     # Real Job Description sourced from Wellfound (VisibilityStack.ai)
│   ├── public_profiles_manifest.json  # Provenance manifest for the 12 public developer CVs
│   └── resumes/
│       ├── generate_synthetic_resumes.py  # Dataset builder for 12 real public profiles + LinkedIn/JSON importer
│       ├── 01_omkar_chittar.pdf ... 12_bharti_rajoriya.docx
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py                    # FastAPI lifespan pre-warming, CORS, and /api/demo/load-sample
│       ├── config.py                  # Thresholds, weights, and environment configuration
│       ├── database.py                # SQLAlchemy 2.0 PostgreSQL engine + zero-config SQLite fallback
│       ├── models.py                  # JobDescription & CandidateEvaluation ORM models (JSONB)
│       ├── schemas.py                 # Pydantic request/response contracts
│       ├── data/
│       │   └── skills_taxonomy.json   # 303 canonical skills, 1,688 aliases, 12 categories, adjacency priors
│       ├── services/
│       │   ├── document_parser.py     # PyMuPDF (fitz) & python-docx table parser + white-text detector
│       │   ├── section_segmenter.py   # Case-insensitive regex Resume/JD section splitter
│       │   ├── entity_extractor.py    # spaCy EntityRuler + interval-merging experience date calculator
│       │   ├── semantic_engine.py     # all-MiniLM-L6-v2 embeddings + Cosine Similarity adjacency matrix
│       │   └── scoring_engine.py      # Deterministic 0-100 math + Explainable AI (XAI) reasoning generator
│       └── routers/
│           ├── jd_router.py           # Module 1 endpoints (POST /api/jd/parse, PUT /api/jd/{jd_id}/skills)
│           └── evaluation_router.py   # Modules 2-5 endpoints (Batch upload, leaderboard, deep-dive drawer)
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    └── src/
        ├── App.jsx                    # Main dashboard + live client-side slider re-ranking
        ├── api/
        │   └── client.js              # Axios API client
        └── components/
            ├── Navbar.jsx             # Slate-900 header with engine telemetry & 1-click Demo loader
            ├── JDInputPanel.jsx       # Module 1 UI + Editable Skill Chips & Min Experience control
            ├── BatchUploadDropzone.jsx# Module 2 UI (10+ PDF/DOCX multi-file drag-and-drop uploader)
            ├── WeightSlidersBar.jsx   # Real-time dynamic re-ranking sliders (Skills / Semantic / Experience)
            ├── RankingTable.jsx       # Module 4 UI (Sortable leaderboard with progress rings & match pills)
            └── CandidateDrawer.jsx    # Module 5 UI (Slide-over XAI reasoning & Tri-State Skills Matrix)
```

## 2. Mathematical Scoring Formulation & Explainable AI (XAI) Pipeline

### 2.1 Multi-Tier Skill Alignment & Soft Semantic Credit (`semantic_engine.py`)

Let $R = \{s_1, s_2, \dots, s_N\}$ be the canonical required skills extracted from the Job Description, and $C = \{c_1, c_2, \dots, c_M\}$ be the canonical skills extracted from the candidate's resume. For each required skill $s_i \in R$:

1. **Exact / Canonical Match ($\text{Credit} = 1.0$)**:
   If $s_i \in C$ (after alias normalization via `skills_taxonomy.json`, e.g., `reactjs` $\to$ `React`, `psql` $\to$ `PostgreSQL`, `torch` $\to$ `PyTorch`), then $s_i$ is classified in `matched_skills` and receives full credit $1.0$.
2. **Semantic Adjacent Match — Soft Credit ($\text{Credit} = 0.60 \times m_i$)**:
   If $s_i \notin C$, the engine computes the maximum cosine similarity $m_i$ between the embedding $E(s_i)$ and all candidate skill embeddings $E(c_j)$:
   $$m_i = \max_{c_j \in C} \frac{E(s_i) \cdot E(c_j)}{\|E(s_i)\|_2 \|E(c_j)\|_2}$$
   If $0.72 \le m_i < 0.95$, the skill is classified as a **Semantic Adjacent Match** in `partial_skills` (e.g., JD requires `FastAPI` and candidate has `Flask` with $m_i = 0.88$; JD requires `PostgreSQL` and candidate has `MySQL` with $m_i = 0.86$) and awards partial credit:
   $$\text{Partial Credit}(s_i) = 0.60 \times m_i$$
3. **Implicit Context Check**:
   If still unmatched, $E(s_i)$ is compared against sentence chunks in the candidate's `experience` and `projects` sections. If $\max \cos \ge 0.72$, partial credit $0.60 \times m_i$ is awarded.
4. **Missing Skill ($\text{Credit} = 0.0$)**:
   If $m_i < 0.72$, $s_i$ is classified in `missing_skills`.

### 2.2 Normalized Sub-Scores ($0 - 100$ Scale)

1. **Skill Alignment Score ($S_{\text{skill}}$)**:
   $$S_{\text{skill}} = \min\left(100, \left( \frac{|\text{Matched Skills}| + \sum_{k} (0.60 \times m_k)}{|R|} \right) \times 100\right)$$

2. **Semantic Experience & Project Relevance ($S_{\text{semantic}}$)**:
   Let $\cos_{\text{raw}}$ be the cosine similarity between the dense MiniLM embedding of the JD core responsibilities/requirements and the candidate's segmented `experience + projects` text. Raw MiniLM cosine similarity in $[0.30, 0.80]$ is linearly mapped onto $[0, 100]$:
   $$S_{\text{semantic}} = \text{clip}\left(\frac{\cos_{\text{raw}} - 0.30}{0.80 - 0.30} \times 100, \; 0, \; 100\right)$$

3. **Quantitative Experience Score ($S_{\text{exp}}$)**:
   Date ranges in the candidate's `experience` section are parsed into $(t_{\text{start}}, t_{\text{end}})$ month intervals and merged via interval union so concurrent jobs or internships are never double-counted:
   $$S_{\text{exp}} = \begin{cases} 100.0 & \text{if } Y_{\text{JD}} = 0 \text{ or } Y_{\text{cand}} \ge Y_{\text{JD}} \\ \left(\frac{Y_{\text{cand}}}{Y_{\text{JD}}}\right) \times 100.0 & \text{if } Y_{\text{cand}} < Y_{\text{JD}} \end{cases}$$

### 2.3 Composite Overall Score & Real-Time Client Re-Ranking

$$\text{Overall Score} = \text{round}\Big( (W_s \cdot S_{\text{skill}}) + (W_c \cdot S_{\text{semantic}}) + (W_e \cdot S_{\text{exp}}), \; 1 \Big)$$

- **Default Weights**: $W_s = 0.50$ (Skills), $W_c = 0.30$ (Semantic Context), $W_e = 0.20$ (Experience Tenure).
- Moving any slider in `WeightSlidersBar.jsx` immediately normalizes $(W_s, W_c, W_e)$ so $W_s + W_c + W_e = 1.0$, recalculates `overall_score` on the client in $O(N \log N)$, and smoothly re-orders the leaderboard.

### 2.4 Adversarial White-Text & Microscopic Font Detection (`document_parser.py`)

During PDF (`fitz` / `page.get_text("dict")`) and DOCX (`python-docx` runs & tables) ingestion, every text span is inspected for:
- **Microscopic font size**: $\text{size} < 2.0\text{ pt}$
- **White or near-white font color**: `#FFFFFF` (`16777215` in sRGB integer representation) or $R, G, B \ge 248$, or Word `<w:vanish/>` hidden run tags.

When detected:
1. `hidden_text_detected = True` is flagged and `integrity_score` is penalized.
2. Hidden spans are stripped from `clean_visible_text` before skill extraction and semantic scoring so keyword stuffing cannot inflate a candidate's rank.

## 3. Real Public Developer & Job Platform Dataset (12 Resumes + JD)

Instead of generic placeholder personas, `sample_data/resumes/generate_synthetic_resumes.py` builds 12 resumes (6 PDFs, 6 DOCX) from **real public developer portfolios, GitHub Pages CVs, and a live Wellfound Senior Full-Stack AI Engineer JD** ([VisibilityStack.ai on Wellfound](https://wellfound.com/jobs/4410736-senior-full-stack-ai-engineer)):

| Rank | Candidate Name | File | Public Profile Source | Persona Tier | Experience | Match Score |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **#1** | **Omkar Chittar** | `01_omkar_chittar.pdf` | [omkarchittar.com/cv](https://omkarchittar.com/cv/) | Top Tier Exact Match | 5.6 yrs | **98.2%** |
| **#2** | **Sean Chang** | `02_sean_chang.docx` | [r05323028.github.io](https://r05323028.github.io/) | Top Tier Exact Match | 6.4 yrs | **98.0%** |
| **#3** | **Sergio Sabater Ruiz** | `03_sergio_sabater_ruiz.pdf` | [sergiosaba12.github.io/portfolio](https://sergiosaba12.github.io/portfolio/) | Top Tier Exact Match | 4.5 yrs | **97.8%** |
| **#4** | **Hemang Negandhi** | `06_hemang_negandhi.docx` | [hemangnegandhi.github.io](https://hemangnegandhi.github.io/img/Hemang%20Negandhi%20Resume.pdf) | Semantic Cousin (`Flask`, `MySQL`, `GCP`, `NLTK`) | 5.1 yrs | **79.1%** |
| **#5** | **Ryan Morshead** | `05_ryan_morshead.pdf` | [ryanmorshead.com/resume](https://ryanmorshead.com/resume/) | Semantic Cousin (`Flask`, `Vue.js`, `MySQL`, `SBERT`) | 5.3 yrs | **74.7%** |
| **#6** | **Adarsh Chate** | `04_adarsh_chate.docx` | [adarshchate.github.io](https://adarshchate.github.io/) | Semantic Cousin (`Django`/`Flask`, `MySQL`, `Vue.js`, `GCP`) | 4.6 yrs | **74.6%** |
| **#7** | **Abdoali Mazhar Zakir** | `07_abdoali_mazhar_zakir.pdf` | [abdoali-zakir.github.io](https://abdoali-zakir.github.io/) | Junior High-Skill (High Skill Overlap, Junior Tenure) | 1.2 yrs | **74.6%** |
| **#8** | **Chirag Jain** | `08_chirag_jain.docx` | [cjchirag7.github.io](https://cjchirag7.github.io/) | Junior High-Skill (Strong Full-Stack & PyTorch) | 1.3 yrs | **70.2%** |
| **#9** | **Florian Lotz** | `09_florian_lotz.pdf` | [lightgaming.github.io/portfolio-website](https://lightgaming.github.io/portfolio-website/) | Junior High-Skill (React + FastAPI + Docker) | 1.4 yrs | **65.3%** |
| **#10** | **Anand Bhagwat** | `11_anand_bhagwat.pdf` | [anandbhagwat.github.io](https://anandbhagwat.github.io/) | Low Match / Pivot (QA Automation — Selenium/Jira) | 3.8 yrs | **24.9%** |
| **#11** | **Cristina Attfield** | `10_cristina_attfield.docx` | [nss-full-time-data-analytics-1.github.io](https://nss-full-time-data-analytics-1.github.io/assets/resume/cristina.pdf) | Low Match / Pivot (BI Data Analyst — Tableau/Power BI) | 2.9 yrs | **18.5%** |
| **#12** | **Bharti Rajoriya** | `12_bharti_rajoriya.docx` | [bhartirajoriya.github.io](https://bhartirajoriya.github.io/) | Low Match + **White-Text Keyword Stuffing Flagged** | 2.4 yrs | **15.2%** |

> **Importing Your Own LinkedIn / JSON Resume Exports**:
> Run `python3 sample_data/resumes/generate_synthetic_resumes.py --import-json /path/to/profiles.json` to convert any custom array of LinkedIn or JSON Resume profiles into formatted PDF and DOCX files.

## 4. Quickstart Instructions

### Option A: One-Command Docker Compose (PostgreSQL 15 + FastAPI + React Vite)

```bash
docker compose up --build
```

- **React 18 Analytics Dashboard**: `http://localhost:5173`
- **FastAPI Interactive OpenAPI Docs**: `http://localhost:8000/docs`
- **PostgreSQL 16 Database**: `localhost:5432` (`scorume`)
- **Docker Containers**: `scorume_postgres`, `scorume_backend`, `scorume_frontend`
- **Docker Namespace / Network**: `scorume` / `scorume_network`

### Option B: Local Bare-Metal Execution (With Automatic SQLite Fallback)

```bash
# 1. Generate the 12 real-profile PDF/DOCX resumes and sample JD
python3 sample_data/resumes/generate_synthetic_resumes.py

# 2. Start the FastAPI backend (automatically falls back to SQLite if Postgres is not running)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 3. Start the React 18 Vite frontend in a second terminal
cd frontend
npm install
npm run dev
```

Once the dashboard opens at `http://localhost:5173`, click **"Load 12-Resume Demo"** in the top navigation bar (or upload the generated PDF/DOCX files from `sample_data/resumes/`) to inspect the ranked leaderboard, drag the real-time weight sliders, and open the slide-over Explainable AI drawer.

 #   s c o r u m e  
 