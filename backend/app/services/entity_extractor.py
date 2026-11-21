"""
Feature 1.3: Skill Taxonomy Normalization & Date-Range Experience Math (entity_extractor.py)

Implements:
1. `extract_skills(text: str) -> list[str]`:
   Loads `skills_taxonomy.json` (300+ canonical skills and 1,600+ aliases) and combines
   spaCy `EntityRuler` / `PhraseMatcher` (when spaCy is installed) with compiled
   word-boundary regex matchers (handling punctuation tokens like `C++`, `C#`, `.NET`,
   `Node.js`, `React.js`, `CI/CD`) to extract canonical skill names deterministically.
2. `calculate_experience_years(experience_section_text: str, full_text: str = "") -> float`:
   Parses date ranges strictly from the experience section first, converts ranges into
   `(start_month_index, end_month_index)` intervals, merges overlapping intervals so
   concurrent roles/internships are never double-counted, and returns total years
   rounded to 1 decimal place.
3. `extract_jd_min_experience_years(jd_text: str) -> float`:
   Parses explicit JD requirements like `"3+ years of experience"`, `"Minimum 2-4 years"`,
   or `"At least 5 years"`.
4. Candidate contact & education metadata extraction (`Name`, `Email`, `Phone`, `Education`).
"""

from __future__ import annotations

import datetime
import json
import logging
import re
from pathlib import Path
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

# Optional spaCy import with automatic fallback to blank English pipeline + EntityRuler
try:
    import spacy
    from spacy.language import Language
except ImportError:
    spacy = None  # type: ignore[assignment]
    Language = Any  # type: ignore[assignment,misc]


MONTH_MAP: dict[str, int] = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}

# Short ambiguous tokens that require case-sensitive or strict context matching
CASE_SENSITIVE_SHORT_ALIASES: dict[str, str] = {
    "c": "C",
    "r": "R",
    "go": "Go",
}


class EntityExtractionService:
    """
    Singleton service managing the curated skill taxonomy, spaCy EntityRuler pipeline,
    and compiled word-boundary regex matchers.
    """

    _instance: EntityExtractionService | None = None

    # Role: Initializes the singleton entity and skill extraction service.
    # Workflow: Loads the skill taxonomy from disk, initializes the spaCy language pipeline, and pre-compiles boundary regexes for skill matching.
    def __init__(self, taxonomy_path: Path | None = None) -> None:
        self.taxonomy_path = taxonomy_path or settings.SKILLS_TAXONOMY_PATH
        self.taxonomy_data: dict[str, Any] = {}
        self.canonical_skills: dict[str, dict[str, Any]] = {}
        self.alias_to_canonical: dict[str, str] = {}
        self.semantic_adjacency_map: dict[str, list[dict[str, Any]]] = {}
        self.compiled_alias_patterns: list[tuple[str, re.Pattern[str]]] = []
        self.nlp: Any = None

        self._load_taxonomy()
        self._init_spacy_pipeline()
        self._compile_regex_patterns()

    # Role: Provides singleton access to the EntityExtractionService instance.
    # Workflow: Checks if an instance exists, creates and stores one if needed, and returns the shared instance.
    @classmethod
    def get_instance(cls) -> EntityExtractionService:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # Role: Loads the curated JSON skill taxonomy and aliases into memory.
    # Workflow: Reads the skills taxonomy file, parses canonical skill definitions and alias lookups, and registers domain category mappings.
    def _load_taxonomy(self) -> None:
        if not self.taxonomy_path.exists():
            raise FileNotFoundError(f"Skills taxonomy file not found at {self.taxonomy_path}")

        raw = json.loads(self.taxonomy_path.read_text(encoding="utf-8"))
        self.taxonomy_data = raw
        self.canonical_skills = raw.get("skills", {})
        self.alias_to_canonical = {
            k.lower().strip(): v for k, v in raw.get("alias_to_canonical", {}).items()
        }
        self.semantic_adjacency_map = raw.get("semantic_adjacency_map", {})

        # Fallback if JSON only had `categories`
        if not self.alias_to_canonical and "categories" in raw:
            for cat_name, skills_dict in raw["categories"].items():
                for canonical, aliases in skills_dict.items():
                    all_aliases = sorted({a.lower().strip() for a in ([canonical.lower()] + aliases)})
                    self.canonical_skills[canonical] = {
                        "canonical": canonical,
                        "category": cat_name,
                        "aliases": all_aliases,
                    }
                    for alias in all_aliases:
                        self.alias_to_canonical[alias] = canonical

    # Role: Sets up the spaCy Natural Language Processing pipeline and EntityRuler.
    # Workflow: Loads the English spaCy model or a blank English pipeline, configures an EntityRuler component, and registers all canonical skill alias patterns.
    def _init_spacy_pipeline(self) -> None:
        """
        Initializes spaCy `en_core_web_sm` (or `spacy.blank("en")` if model weights
        aren't downloaded) and attaches a custom `EntityRuler` populated with all
        canonical skills and aliases from `skills_taxonomy.json`.
        """
        if spacy is None:
            self.nlp = None
            return

        try:
            self.nlp = spacy.load(settings.SPACY_MODEL_NAME, disable=["parser", "lemmatizer"])
        except Exception:
            self.nlp = spacy.blank("en")

        if "entity_ruler" not in self.nlp.pipe_names:
            ruler = self.nlp.add_pipe("entity_ruler", config={"overwrite_ents": True})
            patterns = []
            for alias, canonical in self.alias_to_canonical.items():
                if alias in CASE_SENSITIVE_SHORT_ALIASES:
                    # Match exact case token for C, R, Go
                    patterns.append(
                        {
                            "label": "SKILL",
                            "pattern": [{"TEXT": canonical}],
                            "id": canonical,
                        }
                    )
                else:
                    tokens = alias.split()
                    patterns.append(
                        {
                            "label": "SKILL",
                            "pattern": [{"LOWER": t} for t in tokens],
                            "id": canonical,
                        }
                    )
            ruler.add_patterns(patterns)

    # Role: Compiles word-boundary regular expressions for technical skill aliases.
    # Workflow: Sorts skill aliases longest-first, handles special symbols like plus signs and dots, configures case-sensitive checks for short acronyms, and compiles regex patterns.
    def _compile_regex_patterns(self) -> None:
        """
        Compiles word-boundary regexes for all aliases (sorted longest-first) so skills
        with special characters (`C++`, `C#`, `.NET`, `Node.js`, `CI/CD`) and multi-word
        phrases are matched accurately even around punctuation.
        """
        sorted_aliases = sorted(
            self.alias_to_canonical.items(),
            key=lambda kv: len(kv[0]),
            reverse=True,
        )
        compiled: list[tuple[str, re.Pattern[str]]] = []

        for alias, canonical in sorted_aliases:
            if alias in CASE_SENSITIVE_SHORT_ALIASES:
                if alias == "c":
                    # Match 'C' when listed among languages or before/after comma/slash
                    pat = re.compile(r"(?:(?<=[\s,;/\(])|^)C(?=(?:[\s,;/\)]|$))")
                elif alias == "r":
                    pat = re.compile(r"(?:(?<=[\s,;/\(])|^)R(?=(?:[\s,;/\)]|$))")
                else:
                    # "Go" only when capitalized and not followed by common English prepositions ("Go to", "Go through", "Go into", "Go live")
                    pat = re.compile(
                        r"(?:(?<=[\s,;/\(])|^)Go(?!\s+(?:to|through|into|beyond|ahead|live|with|for|from|over|out|back|down|up|on)\b)(?=(?:[\s,;/\)\.]|$))"
                    )
                compiled.append((canonical, pat))
                continue

            escaped = re.escape(alias)
            # Allow flexible whitespace or hyphen between multi-word tokens
            escaped = escaped.replace(r"\ ", r"[\s\-]+")
            # Custom non-alphanumeric boundary so C++, C#, .NET, Node.js match cleanly
            pattern_str = rf"(?<![A-Za-z0-9_]){escaped}(?![A-Za-z0-9_])"
            compiled.append((canonical, re.compile(pattern_str, re.IGNORECASE)))

        self.compiled_alias_patterns = compiled

    # Role: Extracts recognized canonical skills from candidate text using spaCy and regexes.
    # Workflow: Runs spaCy EntityRuler pattern matching, searches compiled boundary regexes, merges unique canonical skills, and sorts them by first appearance in the document.
    def extract_skills(self, text: str) -> list[str]:
        """
        Extracts canonical skills from input text using both the spaCy EntityRuler
        pipeline and boundary-aware regex matchers, preserving order of first appearance.
        """
        if not text or not text.strip():
            return []

        discovered_with_pos: dict[str, int] = {}

        # 1. Run spaCy EntityRuler when available
        if self.nlp is not None:
            doc = self.nlp(text[:100_000])
            for ent in doc.ents:
                if ent.label_ == "SKILL" and ent.ent_id_:
                    canonical = ent.ent_id_
                    # Verify short case-sensitive tokens (C, R, Go) aren't false positives
                    if canonical in {"C", "R", "Go"}:
                        if ent.text != canonical:
                            continue
                        if canonical == "Go":
                            following = text[ent.end_char : ent.end_char + 15]
                            if re.match(
                                r"^\s+(?:to|through|into|beyond|ahead|live|with|for|from|over|out|back|down|up|on)\b",
                                following,
                                re.IGNORECASE,
                            ):
                                continue
                    if canonical not in discovered_with_pos:
                        discovered_with_pos[canonical] = ent.start_char

        # 2. Run boundary-aware regex patterns (catches C++, C#, .NET, Node.js, etc.)
        for canonical, pattern in self.compiled_alias_patterns:
            m = pattern.search(text)
            if m:
                pos = m.start()
                if canonical not in discovered_with_pos or pos < discovered_with_pos[canonical]:
                    discovered_with_pos[canonical] = pos

        # Sort extracted canonical skills by first occurrence position in the document
        ordered_skills = [
            skill
            for skill, _ in sorted(discovered_with_pos.items(), key=lambda item: item[1])
        ]
        return ordered_skills

    # Role: Maps raw skill phrases to their official canonical taxonomy name.
    # Workflow: Trims whitespace, looks up lowercase aliases in the canonical dictionary, tests skill extraction as fallback, and returns the canonical or cleaned skill string.
    def normalize_skill_name(self, raw_skill: str) -> str:
        """Maps a raw user-entered skill chip to its canonical taxonomy name if known."""
        cleaned = raw_skill.strip()
        if not cleaned:
            return ""
        lower = cleaned.lower()
        if lower in self.alias_to_canonical:
            return self.alias_to_canonical[lower]
        # Try extracting from the string
        extracted = self.extract_skills(cleaned)
        if extracted:
            return extracted[0]
        return cleaned


# Role: Module-level wrapper for extracting skills from text.
# Workflow: Retrieves the EntityExtractionService singleton and executes skill extraction on the given text.
def extract_skills(text: str) -> list[str]:
    """Module-level convenience wrapper for Feature 1.3 skill extraction."""
    return EntityExtractionService.get_instance().extract_skills(text)


# Role: Converts a parsed month and year token into an absolute month integer index.
# Workflow: Checks for ongoing indicators like Present, converts two-digit or four-digit years, maps month names or numbers, and computes year times twelve plus month.
def _parse_month_year_token(
    month_token: str | None,
    year_token: str,
    is_end_date: bool = False,
    reference_date: datetime.date | None = None,
) -> int:
    """
    Converts a parsed (month, year) or 'Present'/'Current' token into an absolute
    month index (`year * 12 + month`).
    """
    ref = reference_date or datetime.date(2026, 11, 1)

    if year_token.lower() in {"present", "current", "now", "till date", "ongoing", "today"}:
        return ref.year * 12 + ref.month

    year = int(year_token)
    if year < 100:
        year += 2000 if year < 50 else 1900

    if month_token:
        m_clean = month_token.strip().rstrip(".").lower()
        if m_clean.isdigit():
            month = max(1, min(12, int(m_clean)))
        else:
            month = MONTH_MAP.get(m_clean[:3], 12 if is_end_date else 1)
    else:
        # When only a year is given (e.g. "2021 - 2023"), assume Jan for start and Dec for end
        month = 12 if is_end_date else 1

    return year * 12 + month


# Regex matching date ranges such as:
# - "Jan 2021 - Present", "February 2019 – Mar 2022", "06/2020 - 08/2023"
# - "2020 - 2024", "2022 to Current"
DATE_RANGE_REGEX = re.compile(
    r"\b(?:"
    r"(?:(?P<m1>Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?[\s,]+(?P<y1>(?:19|20)\d{2}))"
    r"|(?P<num_m1>0?[1-9]|1[0-2])[/\-](?P<num_y1>(?:19|20)\d{2})"
    r"|(?P<only_y1>(?:19|20)\d{2})"
    r")"
    r"\s*(?:[-–—~]+|\bto\b|\bthrough\b|\buntil\b)\s*"
    r"(?:"
    r"(?P<present>Present|Current|Now|Ongoing|Today|Till\s+Date)"
    r"|(?:(?P<m2>Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?[\s,]+(?P<y2>(?:19|20)\d{2}))"
    r"|(?P<num_m2>0?[1-9]|1[0-2])[/\-](?P<num_y2>(?:19|20)\d{2})"
    r"|(?P<only_y2>(?:19|20)\d{2})"
    r")\b",
    re.IGNORECASE,
)

# Explicit experience mention regex (e.g., "5+ years of experience", "4.5 years of professional experience")
EXPLICIT_EXP_YEARS_REGEX = re.compile(
    r"\b(?P<years>\d{1,2}(?:\.\d)?)\s*\+?\s*(?:to\s*\d{1,2}\s*)?years?\s+of\s+(?:professional\s+|industry\s+|relevant\s+|full[\s\-]stack\s+|software\s+|hands[\s\-]on\s+)?experience\b",
    re.IGNORECASE,
)


# Role: Parses date ranges from text and calculates total non-overlapping duration in months.
# Workflow: Finds all date range regex matches, filters out educational graduation lines, maps start and end month indices, merges overlapping time intervals, and sums the unique months.
def _extract_merged_months_from_text(
    text: str,
    reference_date: datetime.date | None = None,
) -> int:
    """
    Parses all `(start_month, end_month)` intervals from `text`, filters out invalid
    ranges, merges overlapping intervals so concurrent roles/internships are never
    double-counted, and returns total non-overlapping months.
    """
    if not text or not text.strip():
        return 0

    ref = reference_date or datetime.date(2026, 11, 1)
    max_valid_month = ref.year * 12 + ref.month
    intervals: list[tuple[int, int]] = []

    for match in DATE_RANGE_REGEX.finditer(text):
        gd = match.groupdict()

        # Start date extraction
        m1 = gd.get("m1") or gd.get("num_m1")
        y1 = gd.get("y1") or gd.get("num_y1") or gd.get("only_y1")
        if not y1:
            continue

        # End date extraction
        if gd.get("present"):
            m2 = None
            y2 = "present"
        else:
            m2 = gd.get("m2") or gd.get("num_m2")
            y2 = gd.get("y2") or gd.get("num_y2") or gd.get("only_y2")
        if not y2:
            continue

        # Avoid treating graduation/degree date ranges (e.g. "B.S. Computer Science 2016 - 2020")
        # as work experience if full_text fallback is used
        line_start = text.rfind("\n", 0, match.start()) + 1
        line_end = text.find("\n", match.end())
        if line_end == -1:
            line_end = len(text)
        context_line = text[line_start:line_end]
        if re.search(
            r"\b(?:Bachelor|Master|B\.?S\.?|M\.?S\.?|B\.?Tech|M\.?Tech|Ph\.?D|High\s+School|University|College|GPA)\b",
            context_line,
            re.IGNORECASE,
        ):
            continue

        start_idx = _parse_month_year_token(m1, y1, is_end_date=False, reference_date=ref)
        end_idx = _parse_month_year_token(m2, y2, is_end_date=True, reference_date=ref)
        end_idx = min(end_idx, max_valid_month)

        if end_idx >= start_idx and (end_idx - start_idx) <= 480:  # Cap single role at 40 yrs
            # Inclusive month counting (+1 month when start and end months are given)
            duration_end = end_idx + (1 if (m1 or m2 or gd.get("present")) else 0)
            intervals.append((start_idx, duration_end))

    if not intervals:
        return 0

    # Sort by start month and merge overlapping intervals
    intervals.sort(key=lambda iv: (iv[0], iv[1]))
    merged: list[tuple[int, int]] = [intervals[0]]

    for current_start, current_end in intervals[1:]:
        prev_start, prev_end = merged[-1]
        if current_start <= prev_end:
            merged[-1] = (prev_start, max(prev_end, current_end))
        else:
            merged.append((current_start, current_end))

    total_months = sum(max(0, end - start) for start, end in merged)
    return total_months


# Role: Calculates total non-overlapping professional work experience in years.
# Workflow: Extracts non-overlapping months from the work experience section, checks full text or explicit summary mentions if empty, converts months to years, and rounds to one decimal place.
def calculate_experience_years(
    experience_section_text: str,
    full_text: str = "",
    reference_date: datetime.date | None = None,
) -> float:
    """
    Feature 1.3: Calculates candidate's total non-overlapping professional experience in years.

    1. Strictly parses date ranges from `experience_section_text` first and merges
       overlapping intervals so concurrent internships/jobs are not double-counted.
    2. If `experience_section_text` yields 0 months, checks `full_text` date ranges
       (excluding education lines) and explicit summary statements (e.g. "5+ years of experience").
    3. Returns total years rounded to 1 decimal place (e.g., `4.2`).
    """
    months = _extract_merged_months_from_text(
        experience_section_text, reference_date=reference_date
    )
    if months > 0:
        return round(months / 12.0, 1)

    if full_text:
        fallback_months = _extract_merged_months_from_text(
            full_text, reference_date=reference_date
        )
        if fallback_months > 0:
            return round(fallback_months / 12.0, 1)

        explicit_match = EXPLICIT_EXP_YEARS_REGEX.search(full_text)
        if explicit_match:
            return round(float(explicit_match.group("years")), 1)

    if experience_section_text:
        explicit_match = EXPLICIT_EXP_YEARS_REGEX.search(experience_section_text)
        if explicit_match:
            return round(float(explicit_match.group("years")), 1)

    return 0.0


# Role: Extracts the minimum required years of experience from a job description.
# Workflow: Evaluates regex patterns matching required tenure phrasing, collects numeric candidates, and returns the lowest required tenure threshold.
def extract_jd_min_experience_years(jd_text: str) -> float:
    """
    Extracts minimum required experience years from a Job Description.
    Supports patterns like:
    - "3+ years of experience"
    - "Minimum 2-4 years" -> returns lower bound (2.0)
    - "At least 5 years of professional experience"
    - "Experience: 4+ years"
    """
    if not jd_text or not jd_text.strip():
        return 0.0

    patterns = [
        # "Minimum of 3-5 years" or "3 - 5+ years of experience"
        re.compile(
            r"(?:minimum(?:\s+of)?|at\s+least|requires?)?\s*(?P<min_yr>\d{1,2}(?:\.\d)?)\s*(?:[-–—to]+\s*\d{1,2}(?:\.\d)?)?\s*\+?\s*years?\s+(?:of\s+)?(?:[\w\-\s/]{0,35}?)experience",
            re.IGNORECASE,
        ),
        # "Experience: 4+ years" or "Required Experience: 3 years"
        re.compile(
            r"experience\s*[:\-–—]\s*(?:minimum\s+)?(?P<min_yr>\d{1,2}(?:\.\d)?)\s*\+?\s*years?",
            re.IGNORECASE,
        ),
        # "Minimum 4 years"
        re.compile(
            r"\b(?:minimum|at\s+least)\s+(?:of\s+)?(?P<min_yr>\d{1,2}(?:\.\d)?)\s*\+?\s*years?\b",
            re.IGNORECASE,
        ),
    ]

    candidates: list[float] = []
    for pat in patterns:
        for m in pat.finditer(jd_text):
            val = float(m.group("min_yr"))
            if 0.0 < val <= 25.0:
                candidates.append(val)

    if candidates:
        return round(min(candidates), 1)
    return 0.0


EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
PHONE_REGEX = re.compile(
    r"(?:(?:\+?\d{1,3}[\s.\-]?)?(?:\(\d{3}\)|\d{3})[\s.\-]?\d{3}[\s.\-]?\d{4}|\+\d{1,3}[\s.\-]?\d{4,5}[\s.\-]?\d{4,6})"
)


# Role: Extracts candidate name, email address, and phone number from resume text.
# Workflow: Scans text with email and phone regexes, inspects top lines of the header to identify candidate name while filtering out job titles, and returns a dictionary of contact details.
def extract_contact_metadata(
    header_text: str,
    full_text: str,
    filename: str = "",
) -> dict[str, str]:
    """
    Extracts candidate Name, Email, and Phone number from the resume header or full text.
    """
    search_space = f"{header_text}\n{full_text[:1500]}"

    email_match = EMAIL_REGEX.search(search_space)
    email = email_match.group(0) if email_match else "not_provided@candidate.local"

    phone_match = PHONE_REGEX.search(search_space)
    phone = phone_match.group(0).strip() if phone_match else "Not Provided"

    # Extract candidate name from first non-empty line of header_text
    candidate_name = ""
    lines = [line.strip() for line in (header_text or full_text).splitlines() if line.strip()]
    for line in lines[:5]:
        # Strip markdown symbols or role labels after pipe/dash
        cleaned = re.sub(r"^[#\*]+\s*", "", line).split("|")[0].split("—")[0].split(" - ")[0].strip()
        if "@" in cleaned or re.search(r"\d{3,}", cleaned):
            continue
        if re.match(
            r"^(?:resume|curriculum\s+vitae|cv|contact|summary|profile|work\s+experience)$",
            cleaned,
            re.IGNORECASE,
        ):
            continue
        words = cleaned.split()
        if 2 <= len(words) <= 5 and all(re.match(r"^[A-Za-z.\-']+$", w) for w in words):
            candidate_name = " ".join(w.capitalize() if w.isupper() else w for w in words)
            break

    if not candidate_name and filename:
        stem = Path(filename).stem
        stem = re.sub(r"^(?:resume|cv)[_\-\s]*", "", stem, flags=re.IGNORECASE)
        stem = re.sub(r"^\d+[_\-\s]*", "", stem)
        candidate_name = stem.replace("_", " ").replace("-", " ").title().strip()

    if not candidate_name:
        candidate_name = "Candidate"

    return {
        "candidate_name": candidate_name,
        "email": email,
        "phone": phone,
    }


# Role: Extracts candidate degree level and academic institution into a concise summary.
# Workflow: Searches the education section for recognized degree patterns, combines the highest degrees found, or falls back to first lines of the education section.
def extract_education_summary(education_section_text: str, full_text: str = "") -> str:
    """Extracts a concise 1-line summary of the candidate's highest degree and university."""
    source = education_section_text.strip() if education_section_text.strip() else full_text
    if not source:
        return "Not Specified"

    degree_pattern = re.compile(
        r"(?:Bachelor|Master|Ph\.?D|Doctor|B\.?S\.?|M\.?S\.?|B\.?Tech|M\.?Tech|B\.?E\.?|M\.?E\.?|M\.?B\.?A\.?|B\.?A\.?)[^\n]{0,120}",
        re.IGNORECASE,
    )
    matches = [m.group(0).strip(" •-*|") for m in degree_pattern.finditer(source)]
    if matches:
        return " | ".join(matches[:2])

    first_lines = [
        line.strip(" •-*")
        for line in education_section_text.splitlines()
        if line.strip()
    ]
    if first_lines:
        return " — ".join(first_lines[:2])[:180]

    return "Not Specified"
