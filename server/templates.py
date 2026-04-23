"""Resume section template library — 5 common resume formats.

Each template defines the sections that should be pre-populated in a new
resume. Applying a template creates matching ResumeSection entries in the
repertoire and wires them into the active resume.
"""
from __future__ import annotations

from typing import Any

from .models import (
    ActiveResume, ActiveSectionRef, ActiveTitleRef,
    Repertoire, ResumeItem, ResumeSection, ResumeTitle, SectionType,
)

# ---------------------------------------------------------------------------
# Template definitions
# ---------------------------------------------------------------------------

_TEMPLATES: dict[str, dict[str, Any]] = {
    "chronological": {
        "name": "Chronological",
        "description": "Traditional format listing work history newest-first. Best for steady career progression.",
        "sections": [
            {"name": "Contact", "type": "heading", "placeholder_titles": []},
            {"name": "Summary", "type": "intro", "placeholder_titles": [
                {"arg1": "Professional Summary", "items": ["Results-driven professional with X years of experience in …"]}
            ]},
            {"name": "Experience", "type": "standard", "placeholder_titles": [
                {"arg1": "Job Title", "arg2": "Company Name", "arg3": "City, ST", "arg4": "Month Year – Present",
                 "items": ["Led a team of X engineers to deliver … resulting in …", "Reduced … by X% through …"]}
            ]},
            {"name": "Education", "type": "standard", "placeholder_titles": [
                {"arg1": "Degree, Major", "arg2": "University Name", "arg3": "City, ST", "arg4": "Year",
                 "items": []}
            ]},
            {"name": "Skills", "type": "skills", "placeholder_titles": [
                {"arg1": "Technical Skills", "items": ["Skill A, Skill B, Skill C"]}
            ]},
        ],
    },
    "functional": {
        "name": "Functional",
        "description": "Emphasises skills and competencies over chronology. Good for career changers.",
        "sections": [
            {"name": "Contact", "type": "heading", "placeholder_titles": []},
            {"name": "Summary", "type": "intro", "placeholder_titles": [
                {"arg1": "Professional Summary", "items": ["Versatile professional bringing expertise in …"]}
            ]},
            {"name": "Core Competencies", "type": "skills", "placeholder_titles": [
                {"arg1": "Competencies", "items": ["Leadership, Project Management, Communication"]}
            ]},
            {"name": "Work History", "type": "standard", "placeholder_titles": [
                {"arg1": "Job Title", "arg2": "Company Name", "arg3": "City, ST", "arg4": "Start – End Year",
                 "items": []}
            ]},
            {"name": "Education", "type": "standard", "placeholder_titles": [
                {"arg1": "Degree, Major", "arg2": "University Name", "arg3": "City, ST", "arg4": "Year",
                 "items": []}
            ]},
        ],
    },
    "combination": {
        "name": "Combination",
        "description": "Blends skills summary with chronological history. Most flexible format.",
        "sections": [
            {"name": "Contact", "type": "heading", "placeholder_titles": []},
            {"name": "Summary", "type": "intro", "placeholder_titles": [
                {"arg1": "Professional Summary", "items": ["Dynamic professional combining X and Y expertise …"]}
            ]},
            {"name": "Core Strengths", "type": "skills", "placeholder_titles": [
                {"arg1": "Strengths", "items": ["Strategic Planning, Cross-functional Collaboration, Data Analysis"]}
            ]},
            {"name": "Experience", "type": "standard", "placeholder_titles": [
                {"arg1": "Job Title", "arg2": "Company Name", "arg3": "City, ST", "arg4": "Month Year – Present",
                 "items": ["Spearheaded … initiative that generated $X in revenue"]}
            ]},
            {"name": "Education", "type": "standard", "placeholder_titles": [
                {"arg1": "Degree, Major", "arg2": "University Name", "arg3": "City, ST", "arg4": "Year",
                 "items": []}
            ]},
            {"name": "Skills", "type": "skills", "placeholder_titles": [
                {"arg1": "Technical Skills", "items": ["Tool A, Tool B, Tool C"]}
            ]},
        ],
    },
    "tech": {
        "name": "Tech-focused",
        "description": "Leads with technical skills and projects. Ideal for software engineers.",
        "sections": [
            {"name": "Contact", "type": "heading", "placeholder_titles": []},
            {"name": "Summary", "type": "intro", "placeholder_titles": [
                {"arg1": "Engineering Profile", "items": ["Software engineer with X years building scalable systems in …"]}
            ]},
            {"name": "Technical Skills", "type": "skills", "placeholder_titles": [
                {"arg1": "Languages", "items": ["Python, TypeScript, Go, Rust"]},
                {"arg1": "Frameworks & Tools", "items": ["FastAPI, React, Docker, Kubernetes, PostgreSQL"]},
            ]},
            {"name": "Projects", "type": "standard", "placeholder_titles": [
                {"arg1": "Project Name", "arg2": "github.com/user/project", "arg3": "", "arg4": "Year",
                 "items": ["Built … using … achieving X ms p99 latency", "Implemented … reducing memory usage by X%"]}
            ]},
            {"name": "Experience", "type": "standard", "placeholder_titles": [
                {"arg1": "Software Engineer", "arg2": "Company Name", "arg3": "City, ST", "arg4": "Month Year – Present",
                 "items": ["Designed and shipped … feature used by X MAU", "Reduced on-call incidents by X% through …"]}
            ]},
            {"name": "Education", "type": "standard", "placeholder_titles": [
                {"arg1": "B.S. Computer Science", "arg2": "University Name", "arg3": "City, ST", "arg4": "Year",
                 "items": []}
            ]},
        ],
    },
    "executive": {
        "name": "Executive",
        "description": "Senior leadership format with board-level scope and P&L ownership.",
        "sections": [
            {"name": "Contact", "type": "heading", "placeholder_titles": []},
            {"name": "Executive Summary", "type": "intro", "placeholder_titles": [
                {"arg1": "Executive Summary", "items": [
                    "C-suite leader with $XB P&L ownership and track record of …",
                    "Transformational operator across X, Y, and Z verticals."
                ]}
            ]},
            {"name": "Core Competencies", "type": "skills", "placeholder_titles": [
                {"arg1": "Leadership Capabilities",
                 "items": ["P&L Management, M&A Integration, Board Relations, Organizational Design"]}
            ]},
            {"name": "Experience", "type": "standard", "placeholder_titles": [
                {"arg1": "Chief Executive Officer", "arg2": "Company Name", "arg3": "City, ST",
                 "arg4": "Month Year – Present",
                 "items": [
                     "Grew revenue from $XM to $YM in Z years through …",
                     "Led acquisition of … creating $X in shareholder value",
                 ]}
            ]},
            {"name": "Board & Advisory", "type": "standard", "placeholder_titles": [
                {"arg1": "Board Member", "arg2": "Organization Name", "arg3": "", "arg4": "Year – Present",
                 "items": []}
            ]},
            {"name": "Education", "type": "standard", "placeholder_titles": [
                {"arg1": "MBA", "arg2": "University Name", "arg3": "City, ST", "arg4": "Year",
                 "items": []}
            ]},
        ],
    },
}

_TYPE_MAP = {
    "heading": SectionType.HEADING,
    "intro": SectionType.INTRO,
    "skills": SectionType.SKILLS,
    "standard": SectionType.STANDARD,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def list_templates() -> list[dict]:
    """Return template metadata (no section content)."""
    return [
        {
            "id": tid,
            "name": t["name"],
            "description": t["description"],
            "section_count": len(t["sections"]),
            "section_names": [s["name"] for s in t["sections"]],
        }
        for tid, t in _TEMPLATES.items()
    ]


def get_template(template_id: str) -> dict | None:
    return _TEMPLATES.get(template_id)


def apply_template(
    template_id: str,
    repertoire: Repertoire,
    active: ActiveResume,
) -> tuple[Repertoire, ActiveResume]:
    """Populate repertoire and active resume from a template.

    Existing repertoire content is preserved. New sections are appended.
    Returns (updated_repertoire, updated_active).
    """
    tmpl = _TEMPLATES.get(template_id)
    if not tmpl:
        raise ValueError(f"Unknown template: {template_id!r}")

    for sec_def in tmpl["sections"]:
        sec = ResumeSection(
            name=sec_def["name"],
            section_type=_TYPE_MAP.get(sec_def["type"], SectionType.STANDARD),
        )
        for title_def in sec_def.get("placeholder_titles", []):
            title = ResumeTitle(
                arg1=title_def.get("arg1", ""),
                arg2=title_def.get("arg2", ""),
                arg3=title_def.get("arg3", ""),
                arg4=title_def.get("arg4", ""),
                items=[ResumeItem(text=txt) for txt in title_def.get("items", [])],
            )
            sec.titles.append(title)
        repertoire.sections.append(sec)

        title_refs = []
        for title in sec.titles:
            title_refs.append(ActiveTitleRef(
                title_id=title.id,
                items=[],
            ))
        active.sections.append(ActiveSectionRef(
            section_id=sec.id,
            titles=title_refs,
        ))

    return repertoire, active
