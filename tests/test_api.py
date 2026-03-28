"""Tests for API endpoints."""

import json
import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from server.api import app, init_app


@pytest.fixture(autouse=True)
def setup_app(tmp_path):
    """Set up app with temp directories for each test."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "active").mkdir()

    # Copy templates
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


@pytest.fixture
def client():
    return TestClient(app)


def test_get_empty_repertoire(client):
    resp = client.get("/api/repertoire")
    assert resp.status_code == 200
    assert resp.json()["sections"] == []


def test_create_section(client):
    resp = client.post("/api/repertoire/sections", json={"name": "Experience"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Experience"
    assert "id" in data


def test_crud_flow(client):
    # Create section
    s = client.post("/api/repertoire/sections", json={"name": "Exp"}).json()

    # Create title
    t = client.post(f"/api/repertoire/titles/{s['id']}", json={
        "arg1": "Engineer", "arg2": "2024", "arg3": "Co", "arg4": "Remote",
    }).json()

    # Create item
    i = client.post(f"/api/repertoire/items/{t['id']}", json={"text": "Did work"}).json()

    # Verify repertoire
    rep = client.get("/api/repertoire").json()
    assert len(rep["sections"]) == 1
    assert len(rep["sections"][0]["titles"]) == 1
    assert len(rep["sections"][0]["titles"][0]["items"]) == 1

    # Add to active
    client.post("/api/active/sections", json={"section_id": s["id"]})
    client.post(f"/api/active/sections/{s['id']}/titles", json={"title_id": t["id"]})
    client.post(f"/api/active/titles/{t['id']}/items", json={"item_id": i["id"]})

    # Verify active
    active = client.get("/api/active").json()
    assert len(active["sections"]) == 1
    assert active["sections"][0]["titles"][0]["items"][0]["text"] == "Did work"


def test_reorder(client):
    s = client.post("/api/repertoire/sections", json={"name": "A"}).json()
    s2 = client.post("/api/repertoire/sections", json={"name": "B"}).json()

    client.post("/api/active/sections", json={"section_id": s["id"]})
    client.post("/api/active/sections", json={"section_id": s2["id"]})

    # Reorder: move B to position 0
    resp = client.post("/api/active/sections/reorder", json={
        "id": s2["id"], "new_index": 0,
    })
    assert resp.status_code == 200

    active = client.get("/api/active/raw").json()
    assert active["sections"][0]["section_id"] == s2["id"]


def test_tweaks(client):
    s = client.post("/api/repertoire/sections", json={"name": "Exp"}).json()
    t = client.post(f"/api/repertoire/titles/{s['id']}", json={"arg1": "Eng"}).json()
    i = client.post(f"/api/repertoire/items/{t['id']}", json={"text": "Original"}).json()

    client.post("/api/active/sections", json={"section_id": s["id"]})
    client.post(f"/api/active/sections/{s['id']}/titles", json={"title_id": t["id"]})
    client.post(f"/api/active/titles/{t['id']}/items", json={"item_id": i["id"]})

    # Set tweak
    resp = client.put(f"/api/active/tweaks/{i['id']}", json={"field": "text", "value": "Modified"})
    assert resp.status_code == 200

    # Verify tweak in resolved active
    active = client.get("/api/active").json()
    assert active["sections"][0]["titles"][0]["items"][0]["text"] == "Modified"

    # List tweaks
    tweaks = client.get("/api/active/tweaks").json()
    assert len(tweaks["tweaks"]) == 1

    # Clear tweak
    client.delete(f"/api/active/tweaks/{i['id']}")
    active = client.get("/api/active").json()
    assert active["sections"][0]["titles"][0]["items"][0]["text"] == "Original"


@pytest.mark.skipif(
    not (Path(os.environ.get("RESUME_SOURCE_DIR", r"C:\nonexistent")) / "resume.tex").exists(),
    reason="Source .tex not available",
)
def test_import_tex(client):
    resp = client.post("/api/import/tex")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["sections"] >= 5
    assert data["items"] >= 10


def test_tailor_state(client):
    # Create some data first
    s = client.post("/api/repertoire/sections", json={"name": "Exp"}).json()
    client.post("/api/active/sections", json={"section_id": s["id"]})

    resp = client.get("/api/tailor/state")
    assert resp.status_code == 200
    data = resp.json()
    assert "repertoire" in data
    assert "active" in data
    assert "stats" in data


def test_tailor_apply(client):
    s = client.post("/api/repertoire/sections", json={"name": "Exp"}).json()
    t = client.post(f"/api/repertoire/titles/{s['id']}", json={"arg1": "Eng"}).json()

    client.post("/api/active/sections", json={"section_id": s["id"]})

    resp = client.post("/api/tailor/apply", json={
        "actions": [
            {"action": "add_title", "target_id": t["id"], "parent_id": s["id"]},
        ],
    })
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert results[0]["ok"] is True
