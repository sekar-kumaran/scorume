import datetime
import pytest
from app.services.entity_extractor import (
    EntityExtractionService,
    extract_skills,
    calculate_experience_years,
    extract_jd_min_experience_years,
    extract_contact_metadata,
    extract_education_summary,
    _extract_merged_months_from_text,
    _parse_month_year_token,
)


class TestEntityExtractor:
    """Tests for skill taxonomy extraction, contact metadata, and non-overlapping experience math."""

    def test_singleton_initialization(self):
        svc1 = EntityExtractionService.get_instance()
        svc2 = EntityExtractionService.get_instance()
        assert svc1 is svc2
        assert len(svc1.canonical_skills) > 100
        assert len(svc1.alias_to_canonical) > 500

    def test_extract_skills_canonical_and_aliases(self):
        text = "Experienced with ReactJS, NodeJS, postgresql, K8s, and Python3."
        skills = extract_skills(text)

        # Should map to canonical names
        assert "React" in skills
        assert "Node.js" in skills
        assert "PostgreSQL" in skills
        assert "Kubernetes" in skills
        assert "Python" in skills

    def test_extract_skills_punctuation_and_special_characters(self):
        text = "Expert in C++, C#, CI/CD, and Next.js."
        skills = extract_skills(text)

        assert "C++" in skills
        assert "C#" in skills
        assert "CI/CD" in skills
        assert "Next.js" in skills

    def test_extract_skills_case_sensitive_short_tokens(self):
        # Upper case C language
        text1 = "Programmed in C, Python, and Java."
        skills1 = extract_skills(text1)
        assert "C" in skills1

        # Common English "go" shouldn't trigger Go language false positive
        text2 = "We need to go to the office and live with our team."
        skills2 = extract_skills(text2)
        assert "Go" not in skills2

    def test_normalize_skill_name(self):
        svc = EntityExtractionService.get_instance()
        assert svc.normalize_skill_name("reactjs") == "React"
        assert svc.normalize_skill_name("k8s") == "Kubernetes"
        assert svc.normalize_skill_name("postgres") == "PostgreSQL"
        assert svc.normalize_skill_name("FastAPI") == "FastAPI"

    def test_parse_month_year_token(self):
        # January 2021 -> 2021 * 12 + 1
        m_idx = _parse_month_year_token("Jan", "2021")
        assert m_idx == 2021 * 12 + 1

        # Present token
        ref = datetime.date(2026, 11, 1)
        m_pres = _parse_month_year_token(None, "Present", reference_date=ref)
        assert m_pres == 2026 * 12 + 11

    def test_non_overlapping_experience_merging(self):
        # Role 1: Jan 2020 - Dec 2021 (24 months)
        # Role 2: Jul 2021 - Jun 2022 (overlaps by 6 months with Role 1)
        # Total distinct duration: Jan 2020 to Jun 2022 = 30 months = 2.5 years
        # If double-counted, it would be 24 + 12 = 36 months (3.0 years)
        work_text = """
Software Engineer | Company A
Jan 2020 - Dec 2021

Consultant | Company B
Jul 2021 - Jun 2022
"""
        ref = datetime.date(2026, 11, 1)
        months = _extract_merged_months_from_text(work_text, reference_date=ref)
        assert months == 30  # Exactly 30 months non-overlapping!
        years = calculate_experience_years(work_text, reference_date=ref)
        assert years == 2.5

    def test_extract_jd_min_experience_years(self):
        assert extract_jd_min_experience_years("Requires minimum 4+ years of experience") == 4.0
        assert extract_jd_min_experience_years("Minimum 3-5 years of professional experience") == 3.0
        assert extract_jd_min_experience_years("Experience: 5+ years") == 5.0
        assert extract_jd_min_experience_years("No minimum requirement mentioned") == 0.0

    def test_extract_contact_metadata(self):
        header = "Omkar Chittar\nBengaluru, India | omkar@domain.com | +91 98765 43210"
        contact = extract_contact_metadata(header, header, "omkar_chittar.pdf")

        assert contact["candidate_name"] == "Omkar Chittar"
        assert contact["email"] == "omkar@domain.com"
        assert "+91 98765 43210" in contact["phone"]

    def test_extract_education_summary(self):
        edu_text = "Master of Science in Computer Science | Stanford University\nBachelor of Engineering | Mumbai University"
        summary = extract_education_summary(edu_text)
        assert "Master" in summary or "Computer Science" in summary
