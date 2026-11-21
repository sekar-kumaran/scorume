"""
Feature 5.1: Public Developer & Job Platform Dataset Builder (generate_synthetic_resumes.py)

Builds 12 real-world candidate resumes (6 PDFs via `reportlab` and 6 DOCX files via `python-docx`,
including table-embedded skill blocks and an adversarial white-text test case) plus 1 real-world
Job Description (`sample_jd_fullstack_ai.txt`) sourced from public developer portfolios, GitHub Pages
CVs, Hacker News "Who Wants to Be Hired", and Wellfound job listings:

- Job Description Benchmark:
  Senior Full-Stack AI Engineer (sourced from VisibilityStack.ai on Wellfound:
  https://wellfound.com/jobs/4410736-senior-full-stack-ai-engineer) requiring 4+ years of
  experience, Python, FastAPI, React, PostgreSQL, Docker, Natural Language Processing, and AWS.

- Candidates 1-3 (Top Tier, 85-98% Match — Strong Exact Matches, 4.5-6+ yrs exp):
  1. Omkar Chittar (`01_omkar_chittar.pdf`) — https://omkarchittar.com/cv/
  2. Sean Chang (`02_sean_chang.docx`) — https://r05323028.github.io/
  3. Sergio Sabater Ruiz (`03_sergio_sabater_ruiz.pdf`) — https://sergiosaba12.github.io/portfolio/

- Candidates 4-6 (Semantic Cousins, 72-82% Match — Adjacent Frameworks/DBs/Cloud):
  4. Adarsh Chate (`04_adarsh_chate.docx`) — https://adarshchate.github.io/
     (Uses Django/Flask, MySQL, Vue.js, Google Cloud Platform, Hugging Face Transformers)
  5. Ryan Morshead (`05_ryan_morshead.pdf`) — https://ryanmorshead.com/resume/
     (Uses Flask, Vue.js, SQLite/MySQL, Kubernetes, Hugging Face Transformers)
  6. Hemang Negandhi (`06_hemang_negandhi.docx`) — https://hemangnegandhi.github.io/img/Hemang%20Negandhi%20Resume.pdf
     (Uses Flask, MySQL/Oracle Database, NLTK/Transformers, Google Cloud Platform)

- Candidates 7-9 (Junior High-Skill, 65-75% Match — High Skill Overlap, 1.0-2.0 yrs exp):
  7. Abdoali Mazhar Zakir (`07_abdoali_mazhar_zakir.pdf`) — https://abdoali-zakir.github.io/
  8. Chirag Jain (`08_chirag_jain.docx`) — https://cjchirag7.github.io/
  9. Florian Lotz (`09_florian_lotz.pdf`) — https://lightgaming.github.io/portfolio-website/

- Candidates 10-12 (Low Match / Career Pivot, 15-45% Match — Data Analyst, QA, UI/UX Designer):
  10. Cristina Attfield (`10_cristina_attfield.docx`) — https://nss-full-time-data-analytics-1.github.io/assets/resume/cristina.pdf
  11. Anand Bhagwat (`11_anand_bhagwat.pdf`) — https://anandbhagwat.github.io/
  12. Bharti Rajoriya (`12_bharti_rajoriya.docx`) — https://bhartirajoriya.github.io/
      (Includes an adversarial 1pt white-text keyword-stuffing block to demonstrate Feature 1.1 integrity flagging)

Also supports `--import-json <path>` to convert custom LinkedIn / JSON Resume exports directly into
PDF/DOCX batches.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import docx
from docx.shared import Inches, Pt, RGBColor
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


SAMPLE_JD_TEXT = """Job Title: Senior Full-Stack AI Engineer
Source Platform: Wellfound (https://wellfound.com/jobs/4410736-senior-full-stack-ai-engineer — VisibilityStack.ai)

About the Role:
You will help build the intelligence layer behind the product: systems that collect data, run AI workflows, orchestrate agents, generate insights, power recommendations, and turn messy real-world search visibility problems into clean customer-facing product experiences. Minimum 4+ years of software engineering experience shipping production systems.

Key Responsibilities:
- Own backend systems and APIs: Design and build scalable asynchronous backend services using Python and FastAPI for ingestion, document parsing, scoring, semantic analysis, and recommendations.
- Build data and relational storage infrastructure: Design clean service boundaries, relational data models, and JSONB schemas in PostgreSQL supporting high-volume monitoring, scoring, and benchmarking.
- Build AI-native and Natural Language Processing workflows: Implement dense vector embeddings, and multi-step NLP evaluation harnesses.
- Build product surfaces and internal operator tools: Create responsive customer-facing analytics dashboards and interactive workflow interfaces using React.
- Own AWS infrastructure and containerized deployment: Package services with Docker and deploy reliable, observable workloads on AWS.

Required Qualifications:
- Bachelor's or Master's degree in Computer Science, Software Engineering, or Artificial Intelligence.
- Minimum 4+ years of professional software engineering experience.
- Core Required Skills: Python, FastAPI, React, PostgreSQL, Docker, Natural Language Processing, AWS.
"""


REAL_PUBLIC_CANDIDATES: list[dict[str, Any]] = [
    # ==========================================================================
    # TIER 1: TOP TIER EXACT MATCHES (Candidates 1 - 3 | 85% - 98%)
    # ==========================================================================
    {
        "filename": "01_omkar_chittar.pdf",
        "format": "pdf",
        "persona_tier": "Top Tier Exact Match (Public CV)",
        "source_url": "https://omkarchittar.com/cv/",
        "name": "Omkar Chittar",
        "role": "Senior Full-Stack & AI Engineer",
        "email": "omkar.chittar@omkarchittar.com",
        "phone": "+1 (415) 890-4412",
        "summary": (
            "Senior Software & AI Engineer with 5.5+ years of experience building full-stack applications, "
            "FastAPI backend services, React/TypeScript interfaces, PostgreSQL data layers, and production "
            "Natural Language Processing & retrieval pipelines deployed with Docker on AWS."
        ),
        "experience": [
            {
                "title": "Senior Full-Stack AI Engineer — Universal Creative & UDX",
                "dates": "Jan 2023 - Present",
                "bullets": [
                    "Independently designed and built a full-stack platform with a Python and FastAPI backend and React frontend, including document ingestion, OCR, and AI-assisted extraction backed by 900+ automated tests.",
                    "Built semantic retrieval and Natural Language Processing evaluation infrastructure over 10,000+ documents using PostgreSQL, dense embeddings, and deterministic validation checks.",
                    "Engineered event-driven monitoring and NLP natural-language-to-SQL services deployed via Docker on AWS (Lambda, Bedrock, ECS, S3) with sub-1.3s p95 latency.",
                ],
            },
            {
                "title": "Software & AI Systems Engineer — Multimodal Search Platform",
                "dates": "May 2021 - Dec 2022",
                "bullets": [
                    "Built and deployed production NLP transcription, speaker diarization, and semantic embedding pipelines using Python, FastAPI, PostgreSQL, and Docker.",
                    "Developed interactive React operator dashboards for real-time drift alerts, precision@k evaluation harnesses, and workflow management on AWS.",
                ],
            },
        ],
        "projects": [
            "Enterprise Contract Lifecycle & Semantic Search Engine: Built ETL and unified Natural Language Processing vector search over 10,000+ legal documents using Python, FastAPI, PostgreSQL, React, Docker, and AWS.",
            "Natural-Language-to-SQL Copilot: Built low-latency semantic query translation service with Python, FastAPI, PostgreSQL, and React.",
        ],
        "skills": [
            "Python",
            "FastAPI",
            "React",
            "PostgreSQL",
            "Docker",
            "Natural Language Processing",
            "AWS",
            "TypeScript",
            "PyTorch",
            "Kubernetes",
            "CI/CD",
        ],
        "education": "M.S. in Computer Science & Engineering — Class of 2021 | B.E. in Computer Engineering",
        "inject_white_text": False,
    },
    {
        "filename": "02_sean_chang.docx",
        "format": "docx",
        "persona_tier": "Top Tier Exact Match (GitHub Portfolio CV)",
        "source_url": "https://r05323028.github.io/",
        "name": "Sean Chang",
        "role": "Senior Software & NLP Engineer",
        "email": "sean.chang@kklab-tech.io",
        "phone": "+886 912-345-678",
        "summary": (
            "Senior Software Engineer & Data Scientist with 6+ years of experience building workflow "
            "orchestration systems, public opinion mining SaaS platforms, FastAPI backends, React dashboards, "
            "PostgreSQL data stores, and spaCy Natural Language Processing models deployed via Docker on AWS."
        ),
        "experience": [
            {
                "title": "Senior Software Engineer — TSMC",
                "dates": "Mar 2022 - Present",
                "bullets": [
                    "Architected high-availability workflow orchestration and backend API services using Python, FastAPI, PostgreSQL, and Docker across cloud-native AWS and Kubernetes clusters.",
                    "Built real-time operator dashboards in React and TypeScript for telemetry visualization, anomaly detection, and pipeline monitoring.",
                ],
            },
            {
                "title": "Senior Data Scientist & NLP Lead — KKLab, KKBOX Group",
                "dates": "Jul 2020 - Feb 2022",
                "bullets": [
                    "Led Natural Language Processing venture projects and maintained the KKBOX SaaS opinion mining system using Python, FastAPI, spaCy, React, and PostgreSQL.",
                    "Containerized NLP inference services with Docker and automated multi-stage deployments on AWS.",
                ],
            },
        ],
        "projects": [
            "Eyes Public Opinion Mining SaaS: Full-stack Natural Language Processing analytics platform built with Python, FastAPI, React, PostgreSQL, and Docker.",
            "TTS Recorder & Labeling Platform: Built human-in-the-loop audio/text annotation platform using React, FastAPI, and PostgreSQL.",
        ],
        "skills": [
            "Python",
            "FastAPI",
            "React",
            "PostgreSQL",
            "Docker",
            "Natural Language Processing",
            "AWS",
            "spaCy",
            "Kubernetes",
            "GraphQL",
        ],
        "education": "M.S. in Computer Science — National Taiwan University (NTU)",
        "inject_white_text": False,
    },
    {
        "filename": "03_sergio_sabater_ruiz.pdf",
        "format": "pdf",
        "persona_tier": "Top Tier Exact Match (GitHub Portfolio CV)",
        "source_url": "https://sergiosaba12.github.io/portfolio/",
        "name": "Sergio Sabater Ruiz",
        "role": "Full-Stack & AI Product Engineer",
        "email": "sergio.sabater@aiportfolio.dev",
        "phone": "+34 611 298 410",
        "summary": (
            "Full-Stack & AI Engineer with 4.5 years of experience taking AI products from prototype to "
            "production-ready systems using Python, FastAPI, React, PostgreSQL, Docker, Natural Language "
            "Processing, Hugging Face, and AWS cloud infrastructure."
        ),
        "experience": [
            {
                "title": "Lead Full-Stack AI Engineer — NeuralProduct Labs",
                "dates": "Jun 2022 - Present",
                "bullets": [
                    "Designed and shipped production AI workflows and REST APIs using Python, FastAPI, and PostgreSQL with JWT authentication and role-based access control.",
                    "Built customer-facing analytics dashboards in React and Tailwind CSS, integrating Natural Language Processing semantic search and model evaluation tools.",
                    "Managed containerized microservice deployments using Docker on AWS.",
                ],
            },
        ],
        "projects": [
            "Voice & Text AI Workflow Engine: Built end-to-end Natural Language Processing and semantic retrieval pipeline with Python, FastAPI, React, PostgreSQL, and Docker.",
            "Realtime Model Evaluation Dashboard: Developed interactive React and FastAPI benchmarking suite backed by PostgreSQL.",
        ],
        "skills": [
            "Python",
            "FastAPI",
            "React",
            "PostgreSQL",
            "Docker",
            "Natural Language Processing",
            "AWS",
            "PyTorch",
            "Scikit-Learn",
            "Tailwind CSS",
        ],
        "education": "B.S. in Computer Science & Artificial Intelligence",
        "inject_white_text": False,
    },
    # ==========================================================================
    # TIER 2: SEMANTIC COUSINS (Candidates 4 - 6 | 72% - 82% Match)
    # Uses Flask/Django instead of FastAPI, MySQL/SQLite instead of PostgreSQL,
    # Vue.js/React Native instead of React, GCP instead of AWS, HF Transformers/spaCy for NLP
    # ==========================================================================
    {
        "filename": "04_adarsh_chate.docx",
        "format": "docx",
        "persona_tier": "Semantic Cousin (Django/Flask + MySQL + Vue.js + GCP)",
        "source_url": "https://adarshchate.github.io/",
        "name": "Adarsh Chate",
        "role": "Senior Python Backend & Full-Stack Engineer",
        "email": "adarsh.chate@backenddev.in",
        "phone": "+91 98220 45112",
        "summary": (
            "Software Engineer with 4.5 years of professional experience developing backend services, "
            "RESTful APIs, and full-stack web applications across EdTech and enterprise platforms using "
            "Python, Django, Flask, MySQL, Vue.js, Docker, and Google Cloud Platform."
        ),
        "experience": [
            {
                "title": "Senior Software Engineer (Python Backend) — EdTech & Travel Systems",
                "dates": "May 2022 - Present",
                "bullets": [
                    "Architected scalable backend services and REST APIs using Python, Django, and Flask for high-volume learning management and travel platforms.",
                    "Designed relational database schemas and query optimizations in MySQL, and built reactive frontend dashboards using Vue.js.",
                    "Integrated Hugging Face Transformers for automated course text tagging and deployed containerized services with Docker on Google Cloud Platform.",
                ],
            },
        ],
        "projects": [
            "Intelligent Document Classifier: Built text classification and embedding pipeline using Python, Flask, Hugging Face Transformers, MySQL, and Docker.",
            "Enterprise Booking & Analytics Portal: Built full-stack web application with Django REST APIs, Vue.js frontend components, and MySQL.",
        ],
        "skills": [
            "Python",
            "Django",
            "Flask",
            "Vue.js",
            "MySQL",
            "Docker",
            "Google Cloud Platform",
            "Hugging Face Transformers",
            "REST APIs",
        ],
        "education": "B.E. in Computer Science & Engineering — Pune University",
        "inject_white_text": False,
    },
    {
        "filename": "05_ryan_morshead.pdf",
        "format": "pdf",
        "persona_tier": "Semantic Cousin (Flask + SQLite/MySQL + Vue.js + Transformers)",
        "source_url": "https://ryanmorshead.com/resume/",
        "name": "Ryan Morshead",
        "role": "Platforms & Machine Learning Engineer",
        "email": "ryan.morshead@primer-alumni.dev",
        "phone": "+1 (650) 442-8819",
        "summary": (
            "Platforms & ML Engineer with 5+ years of experience supporting machine learning and text "
            "intelligence systems, building Python and Flask microservices, reactive UI components, "
            "MySQL/SQLite data stores, and containerized deployments on Google Cloud Platform."
        ),
        "experience": [
            {
                "title": "Senior Platform & ML Engineer — Text Intelligence Systems",
                "dates": "Aug 2021 - Present",
                "bullets": [
                    "Built and deployed backend REST API microservices using Python, Flask, and Tornado to serve Sentence Transformers and spaCy text models.",
                    "Managed relational metadata in MySQL and SQLite, and built interactive frontend dashboards in Vue.js.",
                    "Automated container builds with Docker and orchestrated workloads on Google Cloud Platform and Kubernetes.",
                ],
            },
        ],
        "projects": [
            "IDOM Reactive Python UI Framework: Created declarative component rendering library inspired by reactive hooks using Python, Flask, and WebSockets.",
            "Semantic Text Indexing Service: Built dense embedding retrieval API with Python, Flask, Sentence Transformers, MySQL, and Docker.",
        ],
        "skills": [
            "Python",
            "Flask",
            "Tornado",
            "Vue.js",
            "MySQL",
            "SQLite",
            "Docker",
            "Google Cloud Platform",
            "Sentence Transformers",
            "spaCy",
        ],
        "education": "B.S. in Computational Physics & Computer Science — University of San Francisco",
        "inject_white_text": False,
    },
    {
        "filename": "06_hemang_negandhi.docx",
        "format": "docx",
        "persona_tier": "Semantic Cousin (Flask + MySQL/Oracle + NLTK + GCP)",
        "source_url": "https://hemangnegandhi.github.io/img/Hemang%20Negandhi%20Resume.pdf",
        "name": "Hemang Negandhi",
        "role": "Software & Data Intelligence Engineer",
        "email": "hemangnegandhi1993@gmail.com",
        "phone": "+91 93215 73159",
        "summary": (
            "Engineer with 5 years of experience in backend Python development, ETL data pipelines, "
            "Flask web frameworks, MySQL and Oracle relational databases, NLTK text processing, "
            "and Google Cloud Platform deployments."
        ),
        "experience": [
            {
                "title": "Senior Data & Python Backend Engineer — BNP Paribas / Infogain",
                "dates": "Nov 2021 - Present",
                "bullets": [
                    "Created web applications and REST services using Flask in Python with MySQL and Oracle Database backends handling 1.5M+ rows.",
                    "Implemented text analytics pipelines using NumPy, Pandas, and NLTK for tokenization, stemming, and genre classification deployed on Google Cloud Platform.",
                    "Built frontend administrative workflows using Angular and containerized services with Docker.",
                ],
            },
        ],
        "projects": [
            "Large-Scale Text Genre Prediction Engine: Built with Python, Flask, NLTK, Pandas, MySQL, and deployed on Google Cloud Platform.",
            "Healthcare Relational Data Model & Portal: Designed MySQL schema and Flask backend APIs.",
        ],
        "skills": [
            "Python",
            "Flask",
            "Angular",
            "MySQL",
            "Oracle Database",
            "Docker",
            "Google Cloud Platform",
            "NLTK",
            "Pandas",
            "NumPy",
        ],
        "education": "M.S. in Information Systems — University of Texas at Arlington",
        "inject_white_text": False,
    },
    # ==========================================================================
    # TIER 3: JUNIOR HIGH-SKILL (Candidates 7 - 9 | 65% - 75% Match)
    # Match almost all required technical skills via projects/internships,
    # but have only 1.2 - 1.8 years of non-overlapping professional experience.
    # ==========================================================================
    {
        "filename": "07_abdoali_mazhar_zakir.pdf",
        "format": "pdf",
        "persona_tier": "Junior High-Skill (1.5 yrs exp, High Technical Overlap)",
        "source_url": "https://abdoali-zakir.github.io/",
        "name": "Abdoali Mazhar Zakir",
        "role": "Junior Full-Stack & Applied ML Engineer",
        "email": "abdoali.zakir@unsw-alumni.edu.au",
        "phone": "+61 412 889 301",
        "summary": (
            "Early-career Full-Stack Software & ML Engineer with 1.5 years of professional experience "
            "shipping Python and FastAPI services, React/Next.js interfaces, PostgreSQL data layers, "
            "PyTorch & Natural Language Processing models, and Docker containers."
        ),
        "experience": [
            {
                "title": "Junior Software & Data Engineer — Futures Sport & Entertainment / TCS",
                "dates": "Sep 2025 - Present",
                "bullets": [
                    "Designed and maintained a PostgreSQL data layer and FastAPI backend services in Python, cutting manual reporting effort by 30%.",
                    "Built React and Next.js analytics views and automated Docker deployment workflows using GitHub Actions CI/CD.",
                ],
            },
        ],
        "projects": [
            "TerraCast Advisory Platform: Built ETL pipelines with a React/Next.js frontend, FastAPI microservices, and Natural Language Processing advisory generation.",
            "Cloud Invoice RESTful API: Containerized backend API with PostgreSQL and Docker.",
            "Heterogeneous Graph Neural Network Citation Predictor: Built node embedding and NLP text link prediction in Python and PyTorch.",
        ],
        "skills": [
            "Python",
            "FastAPI",
            "React",
            "Next.js",
            "PostgreSQL",
            "Docker",
            "Natural Language Processing",
            "PyTorch",
            "Neo4j",
        ],
        "education": "B.S. (Hons) in Computer Science — UNSW Sydney",
        "inject_white_text": False,
    },
    {
        "filename": "08_chirag_jain.docx",
        "format": "docx",
        "persona_tier": "Junior High-Skill (1.8 yrs exp, Strong Full-Stack & ML)",
        "source_url": "https://cjchirag7.github.io/",
        "name": "Chirag Jain",
        "role": "Software Engineer (Early Career)",
        "email": "chirag.jain@iitism-tech.in",
        "phone": "+91 97114 55209",
        "summary": (
            "Early-career Software Engineer with 1.8 years of experience building full-stack web "
            "applications and deep learning interfaces using Python, FastAPI, Flask, React, PostgreSQL, "
            "MySQL, PyTorch, and Docker."
        ),
        "experience": [
            {
                "title": "Software Engineer — Cloud & AI Products",
                "dates": "Aug 2025 - Present",
                "bullets": [
                    "Developed backend microservices in Python (FastAPI and Flask) and interactive frontend dashboards in React and TypeScript.",
                    "Managed relational data in PostgreSQL and MySQL and packaged services using Docker.",
                ],
            },
        ],
        "projects": [
            "Dataset Creation & Model Evaluation UI (Inter-IIT Tech Meet Bronze): Built interactive React dashboard and Python/FastAPI backend for PyTorch and computer vision model inspection.",
            "Deepmoth AI Pipeline: Implemented deep learning and vision model serving with Python, Docker, and React.",
        ],
        "skills": [
            "Python",
            "FastAPI",
            "Flask",
            "React",
            "PostgreSQL",
            "MySQL",
            "Docker",
            "PyTorch",
            "TypeScript",
        ],
        "education": "B.Tech in Computer Science & Engineering — IIT (ISM) Dhanbad",
        "inject_white_text": False,
    },
    {
        "filename": "09_florian_lotz.pdf",
        "format": "pdf",
        "persona_tier": "Junior High-Skill (1.4 yrs exp, React + Python + Docker)",
        "source_url": "https://lightgaming.github.io/portfolio-website/",
        "name": "Florian Lotz",
        "role": "Junior Full-Stack & Security Developer",
        "email": "florian.lotz@marqably.eu",
        "phone": "+43 664 391 8204",
        "summary": (
            "Junior Full-Stack Developer with 1.4 years of professional experience building responsive "
            "React web applications, Python backend services (Django/FastAPI), PostgreSQL databases, "
            "and Docker CI/CD pipelines."
        ),
        "experience": [
            {
                "title": "Junior Full-Stack & Application Developer — Syslifters / Marqably Digital",
                "dates": "Jul 2025 - Present",
                "bullets": [
                    "Developed and maintained full-stack web applications using Python, FastAPI, Django, and React backed by PostgreSQL.",
                    "Created automated DevOps build pipelines using Docker, Jenkins, and Playwright.",
                ],
            },
        ],
        "projects": [
            "Automated Web Security Report Analyzer: Built with Python, FastAPI, React, PostgreSQL, and Docker.",
            "Enterprise CI/CD Dashboard: Built React frontend components and Docker deployment workflows.",
        ],
        "skills": [
            "Python",
            "FastAPI",
            "Django",
            "React",
            "PostgreSQL",
            "Docker",
            "Jenkins",
            "Playwright",
        ],
        "education": "B.Sc. in Software Engineering & IT Security — Vienna University of Technology",
        "inject_white_text": False,
    },
    # ==========================================================================
    # TIER 4: LOW MATCH / DOMAIN PIVOT (Candidates 10 - 12 | 15% - 45% Match)
    # Data Analyst, QA Automation Tester, and UI/UX Visual Designer
    # Candidate 12 includes adversarial white-text keyword stuffing to prove Feature 1.1!
    # ==========================================================================
    {
        "filename": "10_cristina_attfield.docx",
        "format": "docx",
        "persona_tier": "Low Match / Pivot (BI Data Analyst — SQL/Excel/Tableau)",
        "source_url": "https://nss-full-time-data-analytics-1.github.io/assets/resume/cristina.pdf",
        "name": "Cristina Attfield",
        "role": "Business Intelligence & Data Analyst",
        "email": "cristina.attfield@nss-analytics.org",
        "phone": "+1 (615) 732-9014",
        "summary": (
            "Business Intelligence & Data Analyst specializing in translating raw business data into "
            "visual dashboards and KPI reports using Microsoft Excel, Tableau, Power BI, and basic SQL."
        ),
        "experience": [
            {
                "title": "Data Analyst — Corporate Meeting & Retail Operations",
                "dates": "Jan 2024 - Present",
                "bullets": [
                    "Created weekly and monthly KPI dashboards using Tableau, Power BI, and Microsoft Excel to track regional revenue trends.",
                    "Cleaned spreadsheet exports and wrote basic SQL queries for ad-hoc business reporting and stakeholder presentations.",
                ],
            },
        ],
        "projects": [
            "Market ROI Comparison Dashboard: Designed Tableau and Power BI line charts comparing regional market returns.",
            "Operations Grant Reporting Tracker: Consolidated Excel workbooks into standardized pivot tables.",
        ],
        "skills": [
            "Tableau",
            "Power BI",
            "Excel Analytics",
            "SQL",
            "Agile & Scrum",
        ],
        "education": "Data Analytics Certificate — Nashville Software School | B.A. in Communications",
        "inject_white_text": False,
    },
    {
        "filename": "11_anand_bhagwat.pdf",
        "format": "pdf",
        "persona_tier": "Low Match / Pivot (QA Automation & Manual Tester)",
        "source_url": "https://anandbhagwat.github.io/",
        "name": "Anand Bhagwat",
        "role": "Software QA & Test Engineer",
        "email": "anand.bhagwat@qatesting.in",
        "phone": "+91 98901 11223",
        "summary": (
            "Detail-oriented Software Quality Assurance Engineer focused on manual regression testing, "
            "Selenium browser automation, Jira defect tracking, TestRail test management, and JMeter load testing."
        ),
        "experience": [
            {
                "title": "Software QA Engineer — Enterprise Web & Mobile Testing",
                "dates": "Mar 2023 - Present",
                "bullets": [
                    "Designed and executed functional, smoke, and regression test suites using Selenium, Java, and Cucumber BDD.",
                    "Logged and triaged defects in Jira and managed test cases in TestRail across Agile Scrum sprints.",
                ],
            },
        ],
        "projects": [
            "E-Commerce Browser Regression Suite: Automated UI checkout test scenarios using Selenium WebDriver and JUnit.",
            "API & Load Testing Harness: Created JMeter stress test plans and SoapUI test cases.",
        ],
        "skills": [
            "Selenium",
            "JUnit",
            "Manual QA & Test Management",
            "Load & Performance Testing",
            "Java",
            "Agile & Scrum",
        ],
        "education": "B.E. in Information Technology — Savitribai Phule Pune University",
        "inject_white_text": False,
    },
    {
        "filename": "12_bharti_rajoriya.docx",
        "format": "docx",
        "persona_tier": "Low Match / Pivot + White-Text Keyword Stuffing Test Case",
        "source_url": "https://bhartirajoriya.github.io/",
        "name": "Bharti Rajoriya",
        "role": "Visual & UI/UX Designer",
        "email": "bharti.rajoriya@designstudio.io",
        "phone": "+1 (510) 338-9921",
        "summary": (
            "Visual and UI/UX Designer creating brand identity assets, print brochures, wireframes, "
            "and interactive prototypes using Figma, Sketch, Adobe XD, Photoshop, and Illustrator."
        ),
        "experience": [
            {
                "title": "Visual & UI Designer — Life Chiropractic / Hippie Vibe Studio",
                "dates": "Jul 2024 - Present",
                "bullets": [
                    "Created marketing banners, print brochures, wedding cards, and weekly newsletters using Adobe Photoshop and Illustrator.",
                    "Developed low- and high-fidelity user flows, wireframes, and interactive UI mockups in Figma, Sketch, and Adobe XD.",
                ],
            },
        ],
        "projects": [
            "Brand Identity & Print Collateral Suite: Designed digital and print assets using Adobe Creative Suite.",
            "Mobile App Wireframe Prototype: Crafted user persona flows and clickable Figma prototypes.",
        ],
        "skills": [
            "UI/UX Design",
            "HTML5",
            "CSS3",
        ],
        "education": "Certificate in Graphic Design — Mission College, Santa Clara | M.A. in Fine Arts",
        # Adversarial test case: injects invisible 1pt #FFFFFF white text with all JD keywords
        # so the document_parser.py White-Text Detector flags it and strips the hidden keywords!
        "inject_white_text": True,
    },
]


def _render_candidate_pdf(candidate: dict[str, Any], out_path: Path) -> None:
    """Generates a clean, multi-section PDF resume using ReportLab."""
    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=LETTER,
        leftMargin=48,
        rightMargin=48,
        topMargin=42,
        bottomMargin=42,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CandName",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=2,
    )
    meta_style = ParagraphStyle(
        "CandMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#475569"),
        spaceAfter=10,
    )
    section_header_style = ParagraphStyle(
        "SecHeader",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=10,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.8,
        leading=13.5,
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=4,
    )
    bullet_style = ParagraphStyle(
        "BulletItem",
        parent=body_style,
        leftIndent=12,
        spaceAfter=2.5,
    )

    story: list[Any] = []

    # 1. Header & Contact (Top 15%)
    story.append(Paragraph(f"{candidate['name']} | {candidate['role']}", title_style))
    story.append(
        Paragraph(
            f"Email: {candidate['email']} | Phone: {candidate['phone']} | Public Profile: {candidate['source_url']}",
            meta_style,
        )
    )

    # 2. Professional Summary
    story.append(Paragraph("PROFESSIONAL SUMMARY", section_header_style))
    story.append(Paragraph(candidate["summary"], body_style))

    # 3. Work Experience
    story.append(Paragraph("WORK EXPERIENCE", section_header_style))
    for role in candidate["experience"]:
        story.append(
            Paragraph(f"<b>{role['title']}</b> ({role['dates']})", body_style)
        )
        for b in role["bullets"]:
            story.append(Paragraph(f"• {b}", bullet_style))
        story.append(Spacer(1, 4))

    # 4. Key Projects
    story.append(Paragraph("KEY PROJECTS", section_header_style))
    for proj in candidate["projects"]:
        story.append(Paragraph(f"• {proj}", bullet_style))

    # 5. Technical Skills
    story.append(Paragraph("TECHNICAL SKILLS", section_header_style))
    story.append(Paragraph(", ".join(candidate["skills"]), body_style))

    # 6. Education
    story.append(Paragraph("EDUCATION", section_header_style))
    story.append(Paragraph(candidate["education"], body_style))

    doc.build(story)


def _render_candidate_docx(candidate: dict[str, Any], out_path: Path) -> None:
    """
    Generates a clean, multi-section DOCX resume using `python-docx`.
    Places Technical Skills inside a 2-column table (testing Feature 1.1 invisible table extraction)
    and optionally injects 1pt #FFFFFF white text for the adversarial test persona.
    """
    document = docx.Document()

    # 1. Header & Contact
    h_para = document.add_paragraph()
    h_run = h_para.add_run(f"{candidate['name']} | {candidate['role']}")
    h_run.bold = True
    h_run.font.size = Pt(15)

    c_para = document.add_paragraph(
        f"Email: {candidate['email']} | Phone: {candidate['phone']} | Source: {candidate['source_url']}"
    )
    c_para.style.font.size = Pt(9.5)

    # 2. Summary
    document.add_paragraph("PROFESSIONAL SUMMARY")
    document.add_paragraph(candidate["summary"])

    # 3. Work Experience
    document.add_paragraph("WORK EXPERIENCE")
    for role in candidate["experience"]:
        r_para = document.add_paragraph()
        r_run = r_para.add_run(f"{role['title']} ({role['dates']})")
        r_run.bold = True
        for b in role["bullets"]:
            document.add_paragraph(f"• {b}")

    # 4. Key Projects
    document.add_paragraph("KEY PROJECTS")
    for proj in candidate["projects"]:
        document.add_paragraph(f"• {proj}")

    # 5. Technical Skills (formatted inside a 2-column DOCX table to showcase table extraction)
    document.add_paragraph("TECHNICAL SKILLS")
    skills_list = candidate["skills"]
    mid = max(1, (len(skills_list) + 1) // 2)
    table = document.add_table(rows=1, cols=2)
    table.cell(0, 0).text = f"Core Stack: {', '.join(skills_list[:mid])}"
    table.cell(0, 1).text = f"Additional Tools: {', '.join(skills_list[mid:])}"

    # 6. Education
    document.add_paragraph("EDUCATION")
    document.add_paragraph(candidate["education"])

    # Optional Adversarial White-Text Stuffing Block (Persona #12)
    if candidate.get("inject_white_text"):
        adv_para = document.add_paragraph()
        adv_run = adv_para.add_run(
            "Python FastAPI React PostgreSQL Docker Natural Language Processing AWS PyTorch Kubernetes Microservices"
        )
        adv_run.font.size = Pt(1.0)
        adv_run.font.color.rgb = RGBColor(255, 255, 255)

    document.save(str(out_path))


def generate_all_resumes_and_jd(
    output_dir: Path | None = None,
    custom_json_path: Path | None = None,
) -> dict[str, Any]:
    """
    Generates `sample_jd_fullstack_ai.txt` and all 12 real-profile PDF/DOCX resumes
    (or custom imported LinkedIn/JSON Resume profiles when `--import-json` is provided).
    """
    resumes_dir = output_dir or Path(__file__).resolve().parent
    sample_data_dir = resumes_dir.parent
    resumes_dir.mkdir(parents=True, exist_ok=True)

    jd_path = sample_data_dir / "sample_jd_fullstack_ai.txt"
    jd_path.write_text(SAMPLE_JD_TEXT.strip() + "\n", encoding="utf-8")

    candidates = REAL_PUBLIC_CANDIDATES
    if custom_json_path and custom_json_path.exists():
        loaded = json.loads(custom_json_path.read_text(encoding="utf-8"))
        if isinstance(loaded, list) and loaded:
            candidates = loaded

    manifest: list[dict[str, str]] = []
    for cand in candidates:
        out_file = resumes_dir / cand["filename"]
        if cand.get("format", "pdf").lower() == "pdf" or out_file.suffix.lower() == ".pdf":
            _render_candidate_pdf(cand, out_file)
        else:
            _render_candidate_docx(cand, out_file)

        manifest.append(
            {
                "filename": cand["filename"],
                "name": cand["name"],
                "persona_tier": cand.get("persona_tier", "Public Profile"),
                "source_url": cand.get("source_url", ""),
            }
        )

    manifest_path = sample_data_dir / "public_profiles_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Generated Job Description: {jd_path}")
    print(f"Generated {len(manifest)} real-profile PDF/DOCX resumes in: {resumes_dir}")
    for item in manifest:
        print(f"  - {item['filename']:28s} | {item['name']:22s} | {item['persona_tier']} ({item['source_url']})")

    return {
        "jd_path": str(jd_path),
        "resumes_dir": str(resumes_dir),
        "count": len(manifest),
        "manifest": manifest,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build 12 real-profile PDF/DOCX resumes from public developer/job platforms or import custom LinkedIn/JSON Resume files."
    )
    parser.add_argument(
        "--import-json",
        type=str,
        default=None,
        help="Optional path to a custom JSON array of LinkedIn/JSON-Resume profiles.",
    )
    args = parser.parse_args()
    custom_path = Path(args.import_json) if args.import_json else None
    generate_all_resumes_and_jd(custom_json_path=custom_path)
