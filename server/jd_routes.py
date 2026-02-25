"""FastAPI routes for Job Description analysis."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from . import active as active_ops
from .jd_analyzer import JDAnalysisResult, analyze_jd
from .storage import load_active, load_repertoire

router = APIRouter(prefix="/api/jd", tags=["jd"])

# In-memory store for the current analysis
_current_analysis: Optional[dict] = None
_current_jd_text: Optional[str] = None


class JDAnalyzeRequest(BaseModel):
    text: str


class JDScrapeRequest(BaseModel):
    url: str


def _get_resume_text() -> str:
    """Extract plain text from the active resume for matching."""
    # Import here to avoid circular dependency
    from .api import _active_path, _rep_path

    a = load_active(_active_path())
    r = load_repertoire(_rep_path())
    resolved = active_ops.resolve_active(a, r)

    parts = []
    for section in resolved:
        parts.append(section.get("name", ""))
        for title in section.get("titles", []):
            parts.append(title.get("arg1", ""))
            parts.append(title.get("arg2", ""))
            parts.append(title.get("arg3", ""))
            parts.append(title.get("arg4", ""))
            for item in title.get("items", []):
                parts.append(item.get("text", ""))

    return " ".join(p for p in parts if p)


@router.post("/analyze")
def analyze_jd_endpoint(body: JDAnalyzeRequest):
    """Analyze a job description against the active resume."""
    global _current_analysis, _current_jd_text

    if not body.text.strip():
        raise HTTPException(400, "Job description text is empty")

    resume_text = _get_resume_text()
    result = analyze_jd(body.text, resume_text)

    _current_jd_text = body.text
    _current_analysis = result.to_dict()

    return _current_analysis


@router.post("/scrape")
def scrape_jd_endpoint(body: JDScrapeRequest):
    """Scrape a URL, extract JD text, and analyze against resume."""
    global _current_analysis, _current_jd_text

    if not body.url.strip():
        raise HTTPException(400, "URL is empty")

    try:
        from .jd_scraper import scrape_jd
        jd_text = scrape_jd(body.url)
    except Exception as e:
        raise HTTPException(400, f"Failed to fetch URL: {e}")

    if not jd_text:
        raise HTTPException(422, "Could not extract job description from that page")

    resume_text = _get_resume_text()
    result = analyze_jd(jd_text, resume_text)

    _current_jd_text = jd_text
    _current_analysis = result.to_dict()
    _current_analysis["extracted_text"] = jd_text

    return _current_analysis


@router.get("/current")
def get_current_analysis():
    """Get the last JD analysis result."""
    if _current_analysis is None:
        raise HTTPException(404, "No analysis available. Run an analysis first.")
    return _current_analysis


@router.delete("/current")
def clear_current_analysis():
    """Clear the current analysis."""
    global _current_analysis, _current_jd_text
    _current_analysis = None
    _current_jd_text = None
    return {"ok": True}
