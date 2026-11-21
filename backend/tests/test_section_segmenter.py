import pytest
from app.services.section_segmenter import (
    _match_header_line,
    segment_resume,
    segment_job_description,
)


class TestSectionSegmenter:
    """Tests for section-aware document segmentation."""

    def test_match_header_line_standalone(self):
        sec, rem = _match_header_line("WORK EXPERIENCE")
        assert sec == "experience"
        assert rem is None

        sec, rem = _match_header_line("TECHNICAL SKILLS:")
        assert sec == "skills"
        assert rem is None

        sec, rem = _match_header_line("EDUCATION & QUALIFICATIONS")
        assert sec == "education"
        assert rem is None

        sec, rem = _match_header_line("PROJECTS")
        assert sec == "projects"
        assert rem is None

    def test_match_header_line_inline(self):
        sec, rem = _match_header_line("Technical Skills: Python, FastAPI, React")
        assert sec == "skills"
        assert rem == "Python, FastAPI, React"

    def test_segment_resume_structure(self, sample_candidate_resume):
        sections = segment_resume(sample_candidate_resume)

        assert "header_contact" in sections
        assert "experience" in sections
        assert "skills" in sections
        assert "education" in sections
        assert "summary" in sections

        # Header contact should have candidate name
        assert "Omkar Chittar" in sections["header_contact"]

        # Experience section should contain company and bullet points
        assert "TechScale Solutions" in sections["experience"]
        assert "Innovate Labs" in sections["experience"]

        # Skills section should contain tech stack
        assert "FastAPI" in sections["skills"]
        assert "Docker" in sections["skills"]

        # Education should contain degree
        assert "B.Tech" in sections["education"]

    def test_segment_resume_non_standard_fallback(self):
        # Resume without standard headers should trigger fallback and warning
        unstructured_text = "I am a programmer. I coded in C++ and Python at various companies for 3 years."
        sections = segment_resume(unstructured_text)

        assert sections["segmentation_warning"] != ""
        assert len(sections["experience"]) > 0

    def test_segment_job_description(self, sample_jd_text):
        jd_dict = segment_job_description(sample_jd_text)

        assert "title" in jd_dict
        assert "Senior Full-Stack AI Engineer" in jd_dict["title"]
        assert "responsibilities" in jd_dict
        assert "requirements" in jd_dict
        assert "Python" in jd_dict["requirements"]
        assert len(jd_dict["education_reqs"]) > 0
