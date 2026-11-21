"""
Feature 1.2: Section-Aware Segmentation (section_segmenter.py)

Splits raw resume or job description text into structured semantic buckets using
case-insensitive regex anchors rather than treating the document as one giant blob:
- `header_contact`: Top 15% of document prior to the first section header.
- `summary`: Executive summary / profile / objective block.
- `experience`: Anchored by `(WORK|PROFESSIONAL)?\\s*(EXPERIENCE|HISTORY|EMPLOYMENT)`.
- `projects`: Anchored by `(PERSONAL|ACADEMIC|KEY)?\\s*PROJECTS`.
- `skills`: Anchored by `(TECHNICAL|CORE)?\\s*(SKILLS|COMPETENCIES|TECHNOLOGIES)`.
- `education`: Anchored by `EDUCATION|ACADEMIC BACKGROUND|QUALIFICATIONS`.
- `certifications`: Certifications, awards, or publications.

Includes graceful fallback to full-text context with segmentation warnings when a
resume uses non-standard formatting.
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Ordered section regex patterns matching standalone header lines.
# Each pattern matches optional numbering/bullets, the core section heading,
# and optional trailing punctuation (colon, dash, pipe) up to 48 characters total.
SECTION_HEADER_PATTERNS: dict[str, re.Pattern[str]] = {
    "experience": re.compile(
        r"^(?:[\d\.\-\*\•\#]+\s*)?"
        r"(?:(?:WORK|PROFESSIONAL|RELEVANT|INDUSTRY|CAREER|ENGINEERING|TECHNICAL)\s+)?"
        r"(?:EXPERIENCE|WORK\s+HISTORY|EMPLOYMENT(?:\s+HISTORY)?|CAREER\s+HISTORY|PROFESSIONAL\s+BACKGROUND)"
        r"\s*[:\-–—\|]*\s*$",
        re.IGNORECASE,
    ),
    "projects": re.compile(
        r"^(?:[\d\.\-\*\•\#]+\s*)?"
        r"(?:(?:PERSONAL|ACADEMIC|KEY|SELECTED|FEATURED|TECHNICAL|OPEN[\s\-]SOURCE|NOTABLE|ENGINEERING)\s+)?"
        r"(?:PROJECTS|PROJECT\s+EXPERIENCE|PORTFOLIO)"
        r"\s*[:\-–—\|]*\s*$",
        re.IGNORECASE,
    ),
    "skills": re.compile(
        r"^(?:[\d\.\-\*\•\#]+\s*)?"
        r"(?:(?:TECHNICAL|CORE|KEY|PRIMARY|PROGRAMMING|ENGINEERING|SOFTWARE)\s+)?"
        r"(?:SKILLS(?:\s*&\s*(?:TECHNOLOGIES|TOOLS|COMPETENCIES))?|COMPETENCIES|TECHNOLOGIES|TECH\s+STACK|AREAS\s+OF\s+EXPERTISE|TOOLS\s*&\s*TECHNOLOGIES)"
        r"\s*[:\-–—\|]*\s*$",
        re.IGNORECASE,
    ),
    "education": re.compile(
        r"^(?:[\d\.\-\*\•\#]+\s*)?"
        r"(?:EDUCATION(?:\s*&\s*(?:TRAINING|QUALIFICATIONS|CERTIFICATIONS))?|ACADEMIC\s+BACKGROUND|ACADEMIC\s+QUALIFICATIONS|QUALIFICATIONS|EDUCATIONAL\s+BACKGROUND)"
        r"\s*[:\-–—\|]*\s*$",
        re.IGNORECASE,
    ),
    "summary": re.compile(
        r"^(?:[\d\.\-\*\•\#]+\s*)?"
        r"(?:(?:PROFESSIONAL|EXECUTIVE|CAREER|TECHNICAL)\s+)?"
        r"(?:SUMMARY|PROFILE|OBJECTIVE|ABOUT\s+ME|OVERVIEW)"
        r"\s*[:\-–—\|]*\s*$",
        re.IGNORECASE,
    ),
    "certifications": re.compile(
        r"^(?:[\d\.\-\*\•\#]+\s*)?"
        r"(?:CERTIFICATIONS?(?:\s*&\s*(?:LICENSES|AWARDS|ACHIEVEMENTS))?|AWARDS(?:\s*&\s*HONORS)?|PUBLICATIONS|LICENSES)"
        r"\s*[:\-–—\|]*\s*$",
        re.IGNORECASE,
    ),
}

# Inline header prefix patterns (e.g., "TECHNICAL SKILLS: Python, FastAPI, React")
INLINE_HEADER_PATTERNS: dict[str, re.Pattern[str]] = {
    "skills": re.compile(
        r"^(?:(?:TECHNICAL|CORE|KEY)\s+)?(?:SKILLS|COMPETENCIES|TECHNOLOGIES|TECH\s+STACK)\s*:\s*(.+)$",
        re.IGNORECASE,
    ),
    "education": re.compile(
        r"^(?:EDUCATION|ACADEMIC\s+BACKGROUND|QUALIFICATIONS)\s*:\s*(.+)$",
        re.IGNORECASE,
    ),
    "summary": re.compile(
        r"^(?:(?:PROFESSIONAL|EXECUTIVE)\s+)?(?:SUMMARY|PROFILE|OBJECTIVE)\s*:\s*(.+)$",
        re.IGNORECASE,
    ),
}


# Role: Detects if a text line represents a section heading or inline header.
# Workflow: Strips whitespace, tests standalone heading length and regex patterns, checks inline heading prefixes, and returns the section key and any trailing inline text.
def _match_header_line(line: str) -> tuple[str | None, str | None]:
    """
    Checks if a single line is a section header or an inline header.
    Returns (section_key, inline_remainder_or_None).
    """
    cleaned = line.strip()
    if not cleaned:
        return None, None

    # Standalone section headers are concise (at most 55 chars, no sentence-ending period)
    if len(cleaned) <= 55 and not cleaned.endswith("."):
        for section_key, pattern in SECTION_HEADER_PATTERNS.items():
            if pattern.match(cleaned):
                return section_key, None

    # Check inline header prefixes (e.g. "Skills: Python, React, PostgreSQL")
    for section_key, inline_pattern in INLINE_HEADER_PATTERNS.items():
        m = inline_pattern.match(cleaned)
        if m:
            return section_key, m.group(1).strip()

    return None, None


# Role: Segments raw candidate resume text into structured section buckets.
# Workflow: Iterates through text lines, identifies section boundaries via header matching, collects lines into appropriate buckets like experience or skills, handles fallback for unsegmented text, and returns a dictionary of sections.
def segment_resume(raw_text: str) -> dict[str, str]:
    """
    Feature 1.2: Splits a candidate resume into logical structural sections.

    Buckets returned:
    - `header_contact`: Top 15% of document prior to the first detected section header.
    - `summary`: Executive summary / profile block.
    - `experience`: Professional work history & employment section.
    - `projects`: Personal, academic, or key technical projects section.
    - `skills`: Technical skills, competencies, and tools section.
    - `education`: Academic background and qualifications section.
    - `certifications`: Certifications, awards, and publications.
    - `segmentation_warning`: Empty string if standard headers were found, or a
      warning description if fallback to full-text context was triggered.
    """
    sections: dict[str, list[str]] = {
        "header_contact": [],
        "summary": [],
        "experience": [],
        "projects": [],
        "skills": [],
        "education": [],
        "certifications": [],
    }

    if not raw_text or not raw_text.strip():
        return {k: "" for k in [*sections.keys(), "segmentation_warning"]}

    lines = raw_text.splitlines()
    total_lines = max(len(lines), 1)
    top_15_pct_line_cutoff = max(4, int(round(total_lines * 0.15)))

    current_section: str | None = None
    detected_headers_count = 0

    for idx, line in enumerate(lines):
        matched_section, inline_content = _match_header_line(line)

        if matched_section is not None:
            current_section = matched_section
            detected_headers_count += 1
            if inline_content:
                sections[current_section].append(inline_content)
            continue

        if current_section is None:
            # Before any section header is encountered:
            # Top 15% goes to header_contact; remaining pre-header text goes to summary
            if idx <= top_15_pct_line_cutoff or not sections["header_contact"]:
                sections["header_contact"].append(line)
            else:
                sections["summary"].append(line)
        else:
            sections[current_section].append(line)

    result: dict[str, str] = {
        key: "\n".join(val).strip() for key, val in sections.items()
    }

    # Ensure header_contact always captures at least the top 15% of characters if empty
    if not result["header_contact"]:
        cutoff_chars = max(150, int(len(raw_text) * 0.15))
        result["header_contact"] = raw_text[:cutoff_chars].strip()

    # Check if resume lacked standard headers (e.g., unstructured CV)
    core_populated = sum(
        1 for k in ("experience", "projects", "skills", "education") if result[k]
    )
    if detected_headers_count == 0 or core_populated == 0:
        warning_msg = (
            "Non-standard resume layout detected: fewer than 1 canonical section header matched. "
            "Falling back gracefully to full-text context for downstream semantic and entity extraction."
        )
        logger.warning(warning_msg)
        if not result["experience"]:
            result["experience"] = raw_text.strip()
        if not result["skills"]:
            result["skills"] = raw_text.strip()
        result["segmentation_warning"] = warning_msg
    elif not result["experience"] and result["projects"]:
        # Candidate (e.g. recent grad / intern) may only have Projects and Education
        warning_msg = (
            "No dedicated Work Experience header found; using Projects section for technical context."
        )
        logger.info(warning_msg)
        result["segmentation_warning"] = warning_msg
    else:
        result["segmentation_warning"] = ""

    return result


# Role: Segments a job description into structured role components.
# Workflow: Extracts explicit title lines, isolates responsibilities and qualifications blocks using regex headings, strips metadata prefixes, and returns a structured dictionary of JD components.
def segment_job_description(jd_text: str) -> dict[str, Any]:
    """
    Segments a Job Description into structured components:
    - `title`: Extracted job title from the opening lines.
    - `responsibilities`: Core role duties and engineering responsibilities.
    - `requirements`: Required qualifications, technical skills, and experience.
    - `education_reqs`: Extracted degree/academic requirements list.
    - `full_text`: Complete normalized JD text.
    """
    if not jd_text or not jd_text.strip():
        return {
            "title": "Untitled Role",
            "responsibilities": "",
            "requirements": "",
            "education_reqs": [],
            "full_text": "",
        }

    lines = [line.strip() for line in jd_text.splitlines() if line.strip()]

    # 1. Extract Job Title from the first few lines
    title = "Software / AI Engineer"
    title_pattern = re.compile(
        r"^(?:job\s+title|position|role|title)\s*[:\-–—]\s*(.+)$",
        re.IGNORECASE,
    )
    for line in lines[:6]:
        cleaned = re.sub(r"^[#\*]+\s*", "", line).strip()
        m = title_pattern.match(cleaned)
        if m:
            title = m.group(1).strip()
            break
        if 4 <= len(cleaned) <= 85 and not cleaned.endswith("."):
            title = cleaned
            break

    # 2. Split into Responsibilities vs Requirements
    resp_header = re.compile(
        r"^(?:[\d\.\-\*\•\#]+\s*)?(?:key\s+|core\s+|role\s+)?(?:responsibilities|what\s+you(?:'ll|\s+will)\s+do|duties|the\s+role|about\s+the\s+role)\s*[:\-–—]*$",
        re.IGNORECASE,
    )
    req_header = re.compile(
        r"^(?:[\d\.\-\*\•\#]+\s*)?(?:minimum\s+|required\s+|preferred\s+|technical\s+|key\s+)?(?:requirements|qualifications|skills(?:\s*&\s*experience)?|what\s+we(?:'re|\s+are)\s+looking\s+for|must\s+haves)\s*[:\-–—]*$",
        re.IGNORECASE,
    )

    responsibilities_lines: list[str] = []
    requirements_lines: list[str] = []
    bucket = "responsibilities"

    for line in lines:
        if resp_header.match(line):
            bucket = "responsibilities"
            continue
        if req_header.match(line):
            bucket = "requirements"
            continue
        if bucket == "requirements":
            requirements_lines.append(line)
        else:
            responsibilities_lines.append(line)

    # 3. Extract explicit education requirement phrases
    edu_pattern = re.compile(
        r"\b(?:Bachelor(?:'s)?|Master(?:'s)?|Ph\.?D\.?|B\.?S\.?|M\.?S\.?|B\.?Tech|M\.?Tech|B\.?E\.?|degree)\b[^.\n]{0,95}",
        re.IGNORECASE,
    )
    edu_matches: list[str] = []
    for match in edu_pattern.finditer(jd_text):
        snippet = match.group(0).strip(" ,;:-")
        if snippet and snippet not in edu_matches:
            edu_matches.append(snippet)

    resp_text = "\n".join(responsibilities_lines).strip() or jd_text.strip()
    req_text = "\n".join(requirements_lines).strip() or jd_text.strip()

    return {
        "title": title,
        "responsibilities": resp_text,
        "requirements": req_text,
        "education_reqs": edu_matches[:5],
        "full_text": jd_text.strip(),
    }
