"""Tests for JD analysis API endpoints."""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path

from server.api import app, init_app
from server import jd_routes


@pytest.fixture(autouse=True)
def setup_app(tmp_path):
    """Set up app with temp directories for each test."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "active").mkdir()

    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    real_template = Path(__file__).parent.parent / "data" / "templates"
    for f in ["preamble.tex", "custom-commands.tex"]:
        src = real_template / f
        if src.exists():
            (template_dir / f).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    config = {
        "data_dir": str(data_dir),
        "output_dir": str(tmp_path / "output"),
        "template_dir": str(template_dir),
        "source_dir": r"C:\Users\prest\Desktop\Flash\AMZ Template Brendan",
        "pdflatex_path": r"C:\texlive\2025\bin\windows\pdflatex.exe",
    }
    init_app(config, tmp_path)

    # Reset in-memory JD state between tests
    jd_routes._current_analysis = None
    jd_routes._current_jd_text = None


@pytest.fixture
def client():
    return TestClient(app)


def _seed_resume(client):
    """Create a minimal resume with some keywords for matching."""
    s = client.post("/api/repertoire/sections", json={"name": "Experience"}).json()
    t = client.post(f"/api/repertoire/titles/{s['id']}", json={
        "arg1": "Software Engineer", "arg2": "2024",
        "arg3": "Amazon Robotics", "arg4": "Boston, MA",
    }).json()
    i1 = client.post(f"/api/repertoire/items/{t['id']}", json={
        "text": "Built Python microservices with Docker and deployed to AWS using Kubernetes."
    }).json()
    i2 = client.post(f"/api/repertoire/items/{t['id']}", json={
        "text": "Led cross-functional team of 8 engineers. Improved CI/CD pipeline reliability."
    }).json()

    # Add to active resume (section + title + items)
    client.post("/api/active/sections", json={"section_id": s["id"]})
    client.post(f"/api/active/sections/{s['id']}/titles", json={"title_id": t["id"]})
    client.post(f"/api/active/titles/{t['id']}/items", json={"item_id": i1["id"]})
    client.post(f"/api/active/titles/{t['id']}/items", json={"item_id": i2["id"]})
    return s, t


class TestAnalyzeEndpoint:

    def test_analyze_basic(self, client):
        _seed_resume(client)
        resp = client.post("/api/jd/analyze", json={
            "text": "Need Python Docker AWS experience."
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "score" in data
        assert "keywords" in data
        assert data["total_keywords"] > 0

    def test_analyze_returns_matched_keywords(self, client):
        _seed_resume(client)
        resp = client.post("/api/jd/analyze", json={
            "text": "Python and Docker required."
        })
        data = resp.json()
        matched = [k for k in data["keywords"] if k["matched"]]
        assert len(matched) >= 2  # python, docker

    def test_analyze_empty_text_returns_400(self, client):
        resp = client.post("/api/jd/analyze", json={"text": ""})
        assert resp.status_code == 400

    def test_analyze_no_resume_data(self, client):
        """Analysis should work even with empty resume (0% score)."""
        resp = client.post("/api/jd/analyze", json={
            "text": "Need Python and Docker."
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["score"] == 0.0

    def test_analyze_with_many_keywords(self, client):
        _seed_resume(client)
        jd = """
        Senior Software Engineer - Robotics

        Requirements:
        - 5+ years Python, Java, or C++ experience
        - Docker, Kubernetes, AWS (EC2, S3, Lambda)
        - CI/CD pipelines (Jenkins, GitHub Actions)
        - Strong leadership and communication skills
        - Experience with Agile/Scrum methodologies
        - Machine Learning or Computer Vision a plus
        """
        resp = client.post("/api/jd/analyze", json={"text": jd})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_keywords"] >= 5
        assert data["matched_count"] >= 2


class TestCurrentEndpoint:

    def test_get_current_no_analysis(self, client):
        resp = client.get("/api/jd/current")
        assert resp.status_code == 404

    def test_get_current_after_analysis(self, client):
        _seed_resume(client)
        client.post("/api/jd/analyze", json={"text": "Need Python."})

        resp = client.get("/api/jd/current")
        assert resp.status_code == 200
        assert resp.json()["total_keywords"] > 0

    def test_clear_current(self, client):
        _seed_resume(client)
        client.post("/api/jd/analyze", json={"text": "Need Python."})

        resp = client.delete("/api/jd/current")
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

        resp = client.get("/api/jd/current")
        assert resp.status_code == 404
