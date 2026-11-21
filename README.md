# Scorume (evaluation engine)

> **Autonomous Candidate Evaluation & Precision Technical Ranking Engine**  
> **100% On-Premise, Privacy-First, Zero Cloud LLM API Dependency (Runs Fully on Local CPU)**  
> **Built for Enterprise Recruitment & Modern Engineering Hiring Teams**

---

### 📌 Project Context & Recruitment Submission
> **Notice**: This production-grade platform was engineered as an end-to-end technical evaluation submission for a **Recruitment Process** with an allocated delivery timeline of **5–7 days**.
>
> In that timeframe, the goal was to design, build, test, containerize, and cloud-deploy a complete, explainable, and adversarial-resistant alternative to legacy recruitment filters, combining:
> 1. High-throughput local NLP pipelines (PyMuPDF layout inspection, spaCy EntityRuler, and Hugging Face Sentence-Transformers).
> 2. Explainable AI (XAI) multi-variable scoring algorithms with zero black-box bias.
> 3. Modern React 18 frontend with interactive real-time weight tuning and candidate deep-dive inspection.
> 4. Production container orchestration (Docker Compose) and Infrastructure-as-Code (Terraform for AWS ap-south-1).

---

## 📖 Executive Summary

Traditional recruitment systems and keyword filters rely on naive substring matching or expensive, opaque cloud LLM API calls. This creates two critical failure modes:
1. **Vulnerability to Adversarial Exploitation**: Candidates exploit keyword scanners by inserting invisible white text, stuffing raw skill lists in tiny fonts, or repeating buzzwords.
2. **Lack of Context & Semantic Intelligence**: Keyword counters cannot distinguish between someone who *built* a distributed Kafka pipeline versus someone who merely *read* about it, nor do they recognize skill adjacency (e.g., PyTorch ↔ TensorFlow, FastAPI ↔ Flask).
3. **Data Privacy & Ongoing API Costs**: Sending private candidate resumes, contact information, and salary histories to third-party proprietary LLM APIs violates modern privacy regulations (such as India's Digital Personal Data Protection Act - DPDP) and incurs high recurring per-token costs.

**Scorume (evaluation engine)** solves this by executing a deterministic, 5-stage NLP pipeline **100% locally on CPU**:
- **Sub-35ms evaluation time** per candidate.
- **Zero external LLM API keys** required (no OpenAI, Anthropic, or external API bills).
- **Adversarial white-text & invisible keyword detection** at the PDF layout and bounding-box level.
- **Section-aware semantic segmentation** (Experience, Skills, Education, Projects).
- **Canonical 303-skill taxonomy** with 1,688 aliases via spaCy `EntityRuler`.
- **Accurate work experience tenure calculation** with date interval overlap merging.
- **Multi-vector semantic similarity** using `sentence-transformers/all-MiniLM-L6-v2`.
- **Explainable AI (XAI)** with dynamic weight sliders for real-time recruiter calibration.
- **Localized for Indian Engineering Hiring**: Native support for ₹ CTC (LPA), Indian tech hubs (Bengaluru, Hyderabad, Pune, Gurugram, Mumbai), and IST scheduling.

---

## 🏛️ System Architecture

```
                                  +---------------------------------------+
                                  |   React 18 + Vite + Tailwind CSS UI   |
                                  |  - Real-Time Weight Tuning Sliders   |
                                  |  - Candidate Rankings Leaderboard     |
                                  |  - XAI Deep-Dive Drawer               |
                                  |  - Role Matcher & Cross-Drive Search  |
                                  +-------------------+-------------------+
                                                      |
                                             REST API Calls (Axios)
                                                      |
                                                      v
                                  +---------------------------------------+
                                  |        FastAPI Backend (Python)       |
                                  |    Async Request Handling & Routes    |
                                  +-------------------+-------------------+
                                                      |
                    +---------------------------------+---------------------------------+
                    |                                 |                                 |
                    v                                 v                                 v
        [ Document Parser ]                [ Section Segmenter ]            [ Entity Extractor ]
        - PyMuPDF / python-docx            - Regex + Structural Heuristics  - spaCy en_core_web_sm
        - White-text / RGB luminance       - Contextual boundary detection  - 303 Skills Taxonomy
        - Adversarial flag generation      - Summary/Skills/Exp/Edu blocks  - 1,688 Skill Aliases
                    |                                 |                                 |
                    +---------------------------------+---------------------------------+
                                                      |
                                                      v
                                  +---------------------------------------+
                                  |      Vector & Semantic Engine         |
                                  |  - sentence-transformers/all-MiniLM   |
                                  |  - 384-dimensional dense embeddings  |
                                  |  - Vectorized Cosine Similarity       |
                                  +-------------------+-------------------+
                                                      |
                                                      v
                                  +---------------------------------------+
                                  |       Composite Scoring Engine        |
                                  |  - Weighted Multi-Component Formula   |
                                  |  - Experience Penalty Scaling         |
                                  |  - Full Explainability JSON Breakdown |
                                  +-------------------+-------------------+
                                                      |
                                                      v
                                  +---------------------------------------+
                                  |      PostgreSQL 15 Persistent DB      |
                                  |  - JSONB Flexible Candidate Records   |
                                  |  - Audit History & Requisition Runs   |
                                  +---------------------------------------+
```

---

## 📐 Mathematical Scoring Formula

Scorume uses a mathematically defensible, multi-component scoring model. Every candidate's final score ($S_{total} \in [0, 100]$) is computed transparently:

$$S_{total} = w_{sem} \cdot S_{semantic} + w_{skills} \cdot S_{skills} + w_{exp} \cdot S_{exp} - P_{adversarial}$$

Where:
- **$S_{semantic}$ (Dense Vector Similarity)**: Cosine similarity between the normalized 384-dimensional dense embeddings of the Job Description and the candidate's segmented experience/skills:
  $$S_{semantic} = \max\left(0, \frac{\vec{u}_{jd} \cdot \vec{v}_{resume}}{\|\vec{u}_{jd}\| \|\vec{v}_{resume}\|}\right) \times 100$$
- **$S_{skills}$ (Canonical Jaccard & Coverage Index)**: Matches canonical technical skills extracted against the job's mandatory and secondary requirements:
  $$S_{skills} = \left( 0.75 \cdot \frac{|K_{candidate} \cap K_{jd\_required}|}{|K_{jd\_required}|} + 0.25 \cdot \frac{|K_{candidate} \cap K_{jd\_preferred}|}{|K_{jd\_preferred}|} \right) \times 100$$
- **$S_{exp}$ (Normalized Experience Tenure)**: Evaluates candidate tenure against minimum target experience with asymptotic scaling:
  $$S_{exp} = \min\left(100, \frac{Years_{actual}}{Years_{required}} \times 100\right)$$
- **$P_{adversarial}$ (Adversarial Security Penalty)**: If the document parser detects white-text keyword stuffing, micro-fonts ($<2\text{pt}$), or text matching the background color luminance, an immediate penalty ($-25$ to $-50$ points) and security alert badge is applied.
- **Dynamic Recruiter Calibration**: Recruiters can adjust $w_{sem}$, $w_{skills}$, and $w_{exp}$ dynamically via UI sliders (defaults: $w_{sem} = 0.50$, $w_{skills} = 0.35$, $w_{exp} = 0.15$, where $\sum w = 1.0$), re-ranking the entire candidate pool in under $5\text{ms}$ in the browser without re-running NLP inference.

---

## ⚡ Key Features

| Capability | Legacy Keyword ATS | Scorume (evaluation engine) |
| :--- | :--- | :--- |
| **Parsing Method** | Unstructured plain-text dump | Structural layout & bounding box inspection |
| **Adversarial Detection** | None (easily bypassed by white text) | Automated font color luminance & contrast checking |
| **Skill Extraction** | Exact substring / regex matching | 303 canonical skills with 1,688 aliases + spaCy EntityRuler |
| **Experience Analysis** | Rough regex year guessing | Non-overlapping interval merge across career history |
| **Semantic Matching** | Non-existent | Local `all-MiniLM-L6-v2` dense vector embeddings |
| **Data Privacy** | Sends CVs to external 3rd-party APIs | 100% on-premise local inference, zero data leakage |
| **Operational Cost** | \$0.02 – \$0.10 per resume API call | \$0.00 incremental per-resume processing cost |
| **Explainability** | Black-box percentage | Complete mathematical breakdown & highlighted match signals |

---

## 🛠️ Tech Stack

### Backend
- **Framework**: Python 3.11, FastAPI (async/await, high concurrency)
- **NLP & Vectors**:
  - `sentence-transformers` (`sentence-transformers/all-MiniLM-L6-v2`)
  - `spaCy` (`en_core_web_sm`) + Custom `EntityRuler`
  - `PyMuPDF` (`fitz`) for RGB layout and bounding-box level PDF inspection
  - `python-docx` for structured Microsoft Word parsing
- **Data & Storage**: PostgreSQL 15, SQLAlchemy 2.0 ORM, Alembic migrations, Pydantic v2 schemas
- **Testing**: `pytest`, `pytest-asyncio`, `httpx`

### Frontend
- **Framework**: React 18, Vite 5
- **Styling**: Tailwind CSS 3.4, Lucide Icons, Material Symbols
- **Visual Foundation**: Google Stitch high-fidelity design system
- **State & Data**: Native React hooks, Axios client with automatic fallback

### Infrastructure & DevOps
- **Containerization**: Docker & Docker Compose (multi-stage builds)
- **Cloud Deployment**: AWS EC2 (`ap-south-1` Mumbai)
- **Infrastructure as Code (IaC)**: Terraform (declarative AWS VPC, Security Group, EC2, Swapfile)
- **Web Server / Reverse Proxy**: Nginx reverse proxy routing port 80 to frontend (5173) and backend API (8000)

---

## 📂 Repository Structure

```text
scorume/
├── .env.example                     # Environment template configuration
├── .gitignore                       # Clean Git ignore rules (no secrets/build artifacts)
├── docker-compose.yml               # Complete local stack orchestration (DB + API + Web)
├── README.md                        # Master project documentation
├── backend/
│   ├── Dockerfile                   # Pre-caches spaCy & MiniLM weights at build time
│   ├── requirements.txt             # Locked Python dependencies
│   ├── app/
│   │   ├── config.py                # Pydantic BaseSettings & environment variables
│   │   ├── database.py              # PostgreSQL connection session maker & engine
│   │   ├── models.py                # SQLAlchemy ORM models (JobDescription, CandidateEvaluation)
│   │   ├── schemas.py               # Pydantic input/output validation models
│   │   ├── main.py                  # FastAPI application entrypoint & middleware
│   │   ├── data/
│   │   │   └── skills_taxonomy.json # 303 canonical skills & 1,688 aliases
│   │   ├── routers/
│   │   │   ├── jd_router.py         # Job description creation, parsing & preview
│   │   │   └── evaluation_router.py # Batch candidate evaluation & ranking endpoints
│   │   └── services/
│   │       ├── document_parser.py   # PDF/DOCX layout parsing & white-text detector
│   │       ├── section_segmenter.py # Structural resume segmentation
│   │       ├── entity_extractor.py  # spaCy taxonomy skill & experience extractor
│   │       ├── semantic_engine.py   # Local MiniLM vector similarity calculator
│   │       └── scoring_engine.py    # Multi-component mathematical scoring engine
│   └── tests/                       # Comprehensive unit and integration test suite
├── frontend/
│   ├── Dockerfile                   # Node 20 Vite build & dev server
│   ├── package.json                 # React 18 & UI dependencies
│   ├── vite.config.js               # Vite proxy config to backend
│   ├── tailwind.config.js           # Google Stitch custom design system tokens
│   ├── index.html                   # HTML entrypoint with Scorume title & metadata
│   └── src/
│       ├── App.jsx                  # Root state orchestration & notifications
│       ├── api/client.js            # Axios REST client with error recovery
│       └── components/
│           ├── Navbar.jsx           # Top navigation with status badge
│           ├── CampaignSetupView.jsx# Step 1: JD input, preview & resume upload
│           ├── CandidateRankingsView.jsx # Step 2: Leaderboard & live weight tuning
│           ├── CandidateDeepDiveDrawer.jsx # Step 3: Explainable AI inspection
│           ├── RoleMatcherFinderView.jsx  # Step 4: Multi-role cross-drive matcher
│           ├── EvaluationHistoryView.jsx  # Step 5: Historical drives audit
│           └── Footer.jsx           # System metadata footer
├── sample_data/
│   ├── sample_jd_fullstack_ai.txt   # Real AI Engineer benchmark JD
│   ├── public_profiles_manifest.json# Provenance manifest for test profiles
│   └── resumes/                     # 12 diverse test resumes (PDF & DOCX)
└── terraform/                       # AWS IaC Deployment
    ├── main.tf                      # EC2, Security Group, SSH Key, 4GB Swap, Nginx
    ├── variables.tf                 # AWS region (ap-south-1), instance type, disk
    └── outputs.tf                   # Public IP, Application URLs & SSH helper
```

---

## 🚀 Quick Start Guide

You can run Scorume either using **Docker Compose** (recommended, zero manual dependency installation) or directly on your **local machine**.

### Option A: Running with Docker Compose (Recommended)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/sekar-kumaran/scorume.git
   cd scorume
   ```

2. **Launch the entire stack**:
   ```bash
   docker compose up -d --build
   ```

3. **Access the services**:
   - 🌐 **Interactive Web UI**: [http://localhost:5173](http://localhost:5173)
   - 📑 **Backend OpenAPI Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - 🩺 **Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

4. **Tear down**:
   ```bash
   docker compose down
   ```

---

### Option B: Running Locally (Manual Setup)

#### 1. Backend Setup (Python 3.11+)
```bash
cd backend
python -m venv venv

# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Start FastAPI dev server:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Frontend Setup (Node.js 18+)
```bash
cd ../frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## ☁️ Cloud Deployment on AWS with Terraform

The `terraform/` directory contains complete Infrastructure-as-Code to provision Scorume onto **AWS (Mumbai `ap-south-1`)**:

- **Compute**: AWS EC2 `t3.micro` (Free-Tier eligible) with 2 vCPUs and an automated **4GB swapfile** on 30GB gp3 SSD to easily handle local neural embeddings without out-of-memory errors.
- **Security**: Security Group exposing port 80 (HTTP Nginx reverse proxy), port 22 (SSH), port 5173 (direct frontend), and port 8000 (direct API).
- **Automation (`user_data`)**: Automated script that mounts swap space, installs Docker Engine & Docker Compose, clones this repository, builds all containers, and starts Nginx.

### Deploying to AWS:

```bash
cd terraform

# 1. Initialize Terraform plugins
terraform init

# 2. Preview the plan
terraform plan

# 3. Apply and deploy
terraform apply -auto-approve
```

Terraform outputs the live application URL, Swagger documentation link, and SSH connection string:
```text
Outputs:
application_url  = "http://<EC2_PUBLIC_IP>"
backend_api_docs = "http://<EC2_PUBLIC_IP>/docs"
ssh_command      = "ssh -i scorume-key.pem ubuntu@<EC2_PUBLIC_IP>"
```

To destroy all cloud resources when testing is complete:
```bash
terraform destroy -auto-approve
```

---

## 🧪 Running Automated Tests

Scorume includes automated unit and integration tests covering all critical components:

```bash
cd backend
pytest -v
```

Test coverage includes:
- `test_document_parser.py`: PDF layout extraction and white-text keyword stuffing detection.
- `test_section_segmenter.py`: Accurate extraction of Experience, Skills, Education, and Projects.
- `test_entity_extractor.py`: Taxonomy normalization and experience tenure calculation.
- `test_semantic_engine.py`: MiniLM dense vector similarity and dimension checks.
- `test_scoring_engine.py`: Weighted formula correctness, edge cases, and explainability payloads.
- `test_api_endpoints.py`: End-to-end FastAPI endpoint integration tests.

---

## 🔒 Security & Privacy Compliance

- **DPDP Act (India) Compliant**: Resumes contain sensitive Personal Identifiable Information (PII). By running 100% on-premise, no candidate data ever leaves the local server boundary.
- **Adversarial Resilience**: Defends hiring teams against prompt injection in resumes and invisible keyword tricks used to game traditional screening filters.
- **Deterministic & Auditable**: Every single score contains an immutable JSON breakdown detailing exact skill matches, experience calculations, and semantic similarity vectors for compliance audits.

---

## 👤 Author & License

- **Developer**: Sekar Kumaran ([@sekar-kumaran](https://github.com/sekar-kumaran))
- **Project**: Scorume (evaluation engine)
- **License**: MIT License
