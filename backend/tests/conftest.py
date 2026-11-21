import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Configure test environment
os.environ["USE_SQLITE_FALLBACK"] = "true"
os.environ["SQLITE_FALLBACK_URL"] = "sqlite:///./test_scorume.db"

from app.database import Base, engine, get_db, init_db, SessionLocal
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Initializes the database schema before running tests and cleans up afterwards."""
    init_db()
    yield
    test_db_file = Path("test_scorume.db")
    if test_db_file.exists():
        try:
            test_db_file.unlink()
        except Exception:
            pass


@pytest.fixture
def db_session():
    """Provides a transactional database session for tests."""
    db = SessionLocal() if SessionLocal is not None else get_db()
    try:
        yield db
    finally:
        if hasattr(db, "close"):
            db.close()


@pytest.fixture
def client():
    """Provides a FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_jd_text():
    return """
Job Title: Senior Full-Stack AI Engineer
Location: Bengaluru, Karnataka (Hybrid)
Compensation: ₹28 - ₹42 LPA
Experience: Minimum 4+ years of professional engineering experience.

Key Responsibilities:
- Design, build, and deploy production-grade async microservices in Python (FastAPI).
- Architect interactive responsive web frontends using React.js and TypeScript.
- Implement scalable data storage and vector search with PostgreSQL and pgvector.
- Deploy and monitor microservices using Docker, Kubernetes, and CI/CD pipelines.

Requirements:
- Strong hands-on coding in Python, FastAPI, and React.js.
- Experience with PostgreSQL, Docker, and CI/CD.
- Working knowledge of Natural Language Processing (NLP) and Large Language Models.
- Bachelor's or Master's degree in Computer Science or related engineering field.
""".strip()


@pytest.fixture
def sample_candidate_resume():
    return """
Omkar Chittar
Bengaluru, India | omkar.chittar@techdev.in | +91 98765 43210

PROFESSIONAL SUMMARY
Senior Full-Stack AI Engineer with 5+ years of experience designing and scaling web platforms and distributed NLP systems.

WORK EXPERIENCE
Senior Software Engineer | TechScale Solutions (Bengaluru, India)
Jan 2022 - Present
- Architected enterprise REST APIs using Python, FastAPI, and PostgreSQL with sub-100ms response times.
- Built interactive frontend client dashboards using React, TypeScript, and Tailwind CSS.
- Automated deployment workflows with Docker containerization and GitHub Actions CI/CD pipelines.

Full-Stack Developer | Innovate Labs
Jun 2019 - Dec 2021
- Developed web services using Python, Flask, and PostgreSQL.
- Implemented Natural Language Processing algorithms for text classification and semantic retrieval.
- Collaborated in cross-functional agile teams to deliver cloud features on AWS.

TECHNICAL SKILLS
Languages: Python, JavaScript, TypeScript, SQL, C++
Frameworks: FastAPI, React, Flask, Next.js
Databases & Tools: PostgreSQL, Docker, Git, CI/CD, Redis, Linux
AI / NLP: Natural Language Processing, Sentence Transformers, spaCy

EDUCATION
B.Tech in Computer Science and Engineering | National Institute of Technology (2015 - 2019)
""".strip()


@pytest.fixture
def sample_unrelated_resume():
    return """
Anand Bhagwat
Pune, India | anand.b@testinghub.in | +91 91234 56789

PROFESSIONAL SUMMARY
Quality Assurance Lead with 4 years of experience specializing in manual test execution, regression suites, and bug triage.

WORK EXPERIENCE
QA Test Analyst | QualitySoft India
Feb 2020 - Present
- Authored test cases and executed user acceptance testing (UAT) for enterprise billing applications.
- Documented bug reports in Jira and tracked defects across sprint lifecycles.
- Performed regression testing and exploratory testing for monthly software releases.

TECHNICAL SKILLS
Testing Methodologies: Manual Testing, Black Box Testing, Regression Testing, UAT
Tools: Jira, Bugzilla, TestRail, Postman, Excel

EDUCATION
Bachelor of Commerce | Pune University (2016 - 2019)
""".strip()
