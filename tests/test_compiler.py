"""Tests for the LaTeX compiler."""

import pytest
from pathlib import Path
from server.compiler import generate_tex, _render_standard, _render_heading, _render_skills
from server.models import (
    ActiveItemRef,
    ActiveResume,
    ActiveSectionRef,
    ActiveTitleRef,
    Repertoire,
    ResumeItem,
    ResumeSection,
    ResumeTitle,
    SectionType,
)

_PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATE_DIR = _PROJECT_ROOT / "data" / "templates"
OUTPUT_DIR = _PROJECT_ROOT / "output"


def _make_test_data():
    """Create a minimal repertoire + active resume for testing."""
    r = Repertoire(sections=[
        ResumeSection(id="s1", name="Experience", titles=[
            ResumeTitle(
                id="t1",
                arg1=r"\textbf{Software Engineer}",
                arg2="2024 -- Present",
                arg3="Company Inc.",
                arg4="Remote",
                items=[
                    ResumeItem(id="i1", text="Built a thing"),
                    ResumeItem(id="i2", text="Fixed a bug"),
                ],
            ),
        ]),
        ResumeSection(id="s2", name="Projects", titles=[
            ResumeTitle(
                id="t2",
                arg1=r"\textbf{Cool Project}",
                arg2="2023",
                arg3="Python, FastAPI",
                arg4="GitHub",
                items=[
                    ResumeItem(id="i3", text="Did something cool"),
                ],
            ),
        ]),
    ])

    a = ActiveResume(sections=[
        ActiveSectionRef(section_id="s1", titles=[
            ActiveTitleRef(title_id="t1", items=[
                ActiveItemRef(item_id="i1"),
                ActiveItemRef(item_id="i2"),
            ]),
        ]),
        ActiveSectionRef(section_id="s2", titles=[
            ActiveTitleRef(title_id="t2", items=[
                ActiveItemRef(item_id="i3"),
            ]),
        ]),
    ])
    return r, a


class TestTexGeneration:
    def test_generates_valid_tex(self):
        r, a = _make_test_data()
        tex_path = generate_tex(a, r, TEMPLATE_DIR, OUTPUT_DIR)
        assert tex_path.exists()
        content = tex_path.read_text(encoding="utf-8")
        assert r"\begin{document}" in content
        assert r"\end{document}" in content
        assert r"\section{Experience}" in content
        assert "Built a thing" in content

    def test_tweak_applied(self):
        r, a = _make_test_data()
        # Apply a tweak
        a.sections[0].titles[0].items[0].tweak = "TWEAKED TEXT"
        tex_path = generate_tex(a, r, TEMPLATE_DIR, OUTPUT_DIR)
        content = tex_path.read_text(encoding="utf-8")
        assert "TWEAKED TEXT" in content
        assert "Built a thing" not in content

    def test_section_order_preserved(self):
        r, a = _make_test_data()
        tex_path = generate_tex(a, r, TEMPLATE_DIR, OUTPUT_DIR)
        content = tex_path.read_text(encoding="utf-8")
        exp_pos = content.index("Experience")
        proj_pos = content.index("Projects")
        assert exp_pos < proj_pos

    def test_empty_active_generates_minimal_tex(self):
        r, _ = _make_test_data()
        a = ActiveResume()
        tex_path = generate_tex(a, r, TEMPLATE_DIR, OUTPUT_DIR)
        content = tex_path.read_text(encoding="utf-8")
        assert r"\begin{document}" in content
        assert r"\end{document}" in content


class TestRenderFunctions:
    def test_render_standard(self):
        data = {
            "name": "Experience",
            "titles": [{
                "arg1": "Engineer",
                "arg2": "2024",
                "arg3": "Company",
                "arg4": "Remote",
                "trailing_text": "",
                "items": [{"text": "Did work"}],
            }],
        }
        tex = _render_standard(data)
        assert r"\section{Experience}" in tex
        assert r"\resumeSubheading" in tex
        assert "Did work" in tex

    def test_render_heading(self):
        data = {
            "titles": [{
                "arg1": "John Doe",
                "items": [{"text": "john@example.com"}],
            }],
        }
        tex = _render_heading(data)
        assert "John Doe" in tex
        assert r"\begin{center}" in tex

    def test_render_skills(self):
        data = {
            "name": "Technical Skills",
            "titles": [{
                "items": [{"text": "Python, Java, C++"}],
            }],
        }
        tex = _render_skills(data)
        assert "Python, Java, C++" in tex
