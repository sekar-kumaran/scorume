import time
from pathlib import Path
from app.database import SessionLocal
from app.models import db_list_jds
from app.routers.evaluation_router import evaluate_single_resume_bytes
from app.services.section_segmenter import segment_job_description

db = SessionLocal()
jds = db_list_jds(db, limit=1)
if not jds:
    print("No JDs")
    exit(0)

jd = jds[0]
jd_segments = segment_job_description(jd.raw_text)
jd_context = jd_segments['responsibilities'] + "\n" + jd_segments['requirements']

pdf_path = Path("/sample_data/resumes/01_omkar_chittar.pdf")
if not pdf_path.exists():
    print("No sample PDF")
    exit(0)

pdf_bytes = pdf_path.read_bytes()

t0 = time.time()
res = evaluate_single_resume_bytes(pdf_bytes, "01_omkar_chittar.pdf", jd, jd_context)
t1 = time.time()

print(f"DONE in {t1 - t0:.2f}s | Name: {res.candidate_name} | Score: {res.overall_score}")
