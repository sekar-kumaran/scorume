import sys
import time
from pathlib import Path

# Add backend and app directory to path
current_file = Path(__file__).resolve()
backend_dir = current_file.parent.parent  # D:\Downloads\resume-matcher-ai-complete\resume-matcher-ai\backend
root_dir = backend_dir.parent             # D:\Downloads\resume-matcher-ai-complete\resume-matcher-ai
sys.path.insert(0, str(backend_dir))

from app.services.section_segmenter import segment_job_description, segment_resume
from app.services.entity_extractor import (
    extract_skills,
    extract_jd_min_experience_years,
    calculate_experience_years,
    extract_contact_metadata,
    extract_education_summary,
)
from app.services.document_parser import extract_document
from app.services.scoring_engine import calculate_candidate_scores

print("Loading JD...")
jd_path = root_dir / "sample_data" / "sample_jd_fullstack_ai.txt"
jd_text = jd_path.read_text(encoding="utf-8")

t0 = time.time()
jd_segments = segment_job_description(jd_text)
jd_skills = extract_skills(jd_text)
jd_min_years = extract_jd_min_experience_years(jd_text)

print(f"=== JD Parsed in {time.time()-t0:.2f}s ===")
print("Title:", jd_segments.get("title"))
print("Required Skills Extracted:", jd_skills)
print("Min Experience Required:", jd_min_years, "years")

jd_context = f"{jd_segments.get('responsibilities', '')}\n{jd_segments.get('requirements', '')}".strip()

# Test 2 different candidate profiles:
# 1. 01_omkar_chittar.pdf (Top Match)
# 2. 12_bharti_rajoriya.docx (Adversarial White-Text / Keyword-stuffed)
test_files = [
    "01_omkar_chittar.pdf",
    "06_hemang_negandhi.docx",
    "12_bharti_rajoriya.docx",
]

for filename in test_files:
    file_path = root_dir / "sample_data" / "resumes" / filename
    print(f"\n=======================================================")
    print(f"=== Evaluating Candidate: {filename} ===")
    print(f"=======================================================")
    t1 = time.time()
    parsed_doc = extract_document(file_path.read_bytes(), filename)
    print(f"Doc parsed in {time.time()-t1:.2f}s | Hidden text detected: {parsed_doc.hidden_text_detected} | Integrity: {parsed_doc.integrity_score}")
    if parsed_doc.integrity_flags:
        print("Integrity Flags:", parsed_doc.integrity_flags)

    analysis_text = parsed_doc.clean_visible_text or parsed_doc.raw_text
    sections = segment_resume(analysis_text)
    cand_skills = extract_skills(analysis_text)
    cand_exp_years = calculate_experience_years(sections.get("experience", ""), analysis_text)
    contact = extract_contact_metadata(sections.get("header_contact", ""), analysis_text, filename)
    edu = extract_education_summary(sections.get("education", ""), analysis_text)

    exp_proj_text = f"{sections.get('experience', '')}\n{sections.get('projects', '')}".strip()

    t2 = time.time()
    scoring = calculate_candidate_scores(
        jd_required_skills=jd_skills,
        jd_min_experience_years=jd_min_years,
        jd_context_text=jd_context,
        candidate_skills=cand_skills,
        candidate_experience_years=cand_exp_years,
        candidate_experience_and_projects_text=exp_proj_text,
        hidden_text_detected=parsed_doc.hidden_text_detected,
        integrity_score=parsed_doc.integrity_score,
    )
    print(f"Scoring completed in {time.time()-t2:.2f}s!")
    print(f"Candidate Name: {contact.get('candidate_name')}")
    print(f"Detected Experience: {cand_exp_years} years (Req: {jd_min_years} yrs)")
    print(f"Education: {edu}")
    print(f"Candidate Extracted Skills: {cand_skills}")
    print(f"--- Sub-scores & Composite Score ---")
    print(f"  Overall Score:    {scoring.overall_score}%")
    print(f"  Skill Score:      {scoring.skill_score}%")
    print(f"  Semantic Score:   {scoring.semantic_score}% (Raw Cosine: {scoring.raw_semantic_cosine})")
    print(f"  Experience Score: {scoring.experience_score}%")
    print(f"--- Skill Breakdown ---")
    print(f"  Matched: {scoring.matched_skills}")
    print(f"  Partial: {scoring.partial_skills}")
    print(f"  Missing: {scoring.missing_skills}")
    print(f"--- Explainable AI (XAI) Reasoning ---")
    for expl in scoring.explanations:
        print(f"  • {expl}")
