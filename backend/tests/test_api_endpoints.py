import pytest
from fastapi.testclient import TestClient


class TestApiEndpoints:
    """End-to-end tests for Scorume REST API routes."""

    def test_health_endpoint(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "embedding_backend" in data
        assert data["canonical_skills_count"] > 100

    def test_jd_lifecycle_and_evaluation(self, client: TestClient, sample_jd_text: str, sample_candidate_resume: str):
        # 1. Parse JD
        parse_resp = client.post(
            "/api/jd/parse",
            json={
                "title": "Senior AI Platform Engineer",
                "raw_text": sample_jd_text,
                "min_experience_years": 4.0,
            },
        )
        assert parse_resp.status_code == 201
        jd_data = parse_resp.json()
        jd_id = jd_data["id"]
        assert jd_data["title"] == "Senior AI Platform Engineer"
        assert len(jd_data["required_skills"]) > 0
        assert jd_data["min_experience_years"] == 4.0

        # 2. Get JD by ID
        get_jd_resp = client.get(f"/api/jd/{jd_id}")
        assert get_jd_resp.status_code == 200
        assert get_jd_resp.json()["id"] == jd_id

        # 3. List JDs
        list_jd_resp = client.get("/api/jd")
        assert list_jd_resp.status_code == 200
        assert any(j["id"] == jd_id for j in list_jd_resp.json())

        # 4. Evaluate a candidate resume manually
        manual_resp = client.post(
            f"/api/evaluations/{jd_id}/manual",
            json={
                "candidate_name": "Omkar Chittar",
                "email": "omkar.chittar@test.in",
                "phone": "+91 98765 43210",
                "raw_resume_text": sample_candidate_resume,
            },
        )
        assert manual_resp.status_code == 201
        batch_data = manual_resp.json()
        assert batch_data["jd_id"] == jd_id
        assert batch_data["total_candidates"] >= 1
        top_cand = batch_data["candidates"][0]
        assert top_cand["candidate_name"] == "Omkar Chittar"
        assert top_cand["overall_score"] > 60.0
        eval_id = top_cand["id"]

        # 5. Get ranked candidates for JD
        ranked_resp = client.get(f"/api/evaluations/{jd_id}")
        assert ranked_resp.status_code == 200
        assert ranked_resp.json()["total_candidates"] >= 1

        # 6. Get candidate deep-dive details (Drawer endpoint)
        detail_resp = client.get(f"/api/evaluations/candidate/{eval_id}")
        assert detail_resp.status_code == 200
        detail_data = detail_resp.json()
        assert detail_data["id"] == eval_id
        assert "segmented_sections" in detail_data
        assert len(detail_data["explanations"]) >= 4

        # 7. Update JD Skills benchmark & recalculate
        update_skills_resp = client.put(
            f"/api/jd/{jd_id}/skills",
            json={
                "required_skills": ["Python", "FastAPI", "React", "PostgreSQL", "Docker"],
                "min_experience_years": 5.0,
                "recalculate_candidates": True,
            },
        )
        assert update_skills_resp.status_code == 200
        updated_jd = update_skills_resp.json()
        assert "Python" in updated_jd["required_skills"]
        assert updated_jd["min_experience_years"] == 5.0

        # 8. Export CSV
        csv_resp = client.get(f"/api/evaluations/{jd_id}/export-csv")
        assert csv_resp.status_code == 200
        assert "text/csv" in csv_resp.headers.get("content-type", "")
        assert "Omkar Chittar" in csv_resp.text

    def test_role_matcher_and_history(self, client: TestClient, sample_candidate_resume: str):
        # 1. Test Role Matcher cross-drive search
        matcher_resp = client.post(
            "/api/evaluations/role-matcher/find-candidates",
            json={
                "role_title": "Lead Python Architect",
                "department": "Core Platform",
                "min_experience_years": 4.0,
                "required_skills": ["Python", "FastAPI", "PostgreSQL"],
                "weight_skills": 0.5,
                "weight_semantic": 0.3,
                "weight_experience": 0.2,
                "include_all_pools": True,
            },
        )
        assert matcher_resp.status_code == 200
        matches = matcher_resp.json()
        assert isinstance(matches, list)

        # 2. Test Reverse Role Matcher
        reverse_resp = client.post(
            "/api/evaluations/role-matcher/reverse-match",
            json={
                "raw_resume_text": sample_candidate_resume,
            },
        )
        assert reverse_resp.status_code == 200
        reverse_matches = reverse_resp.json()
        assert isinstance(reverse_matches, list)

        # 3. Test Evaluation History
        history_resp = client.get("/api/evaluations/history")
        assert history_resp.status_code == 200
        hist_data = history_resp.json()
        assert "summary" in hist_data
        assert "runs" in hist_data
        assert hist_data["summary"]["total_evaluations"] >= 0
