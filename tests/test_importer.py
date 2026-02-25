"""Tests for the LaTeX importer."""

import pytest
from pathlib import Path
from server.importer import import_tex, _extract_brace_args, _try_parse_resume_item
from server.models import SectionType


SOURCE_DIR = Path(r"C:\Users\prest\Desktop\Flash\AMZ Template Brendan")


class TestBraceExtraction:
    def test_simple_args(self):
        args = _extract_brace_args(r"\resumeSubheading{A}{B}{C}{D}", r"\resumeSubheading")
        assert args == ["A", "B", "C", "D"]

    def test_nested_braces(self):
        args = _extract_brace_args(
            r"\resumeSubheading{\textbf{Engineer}}{2024}{Sub}{Loc}",
            r"\resumeSubheading",
        )
        assert args[0] == r"\textbf{Engineer}"

    def test_incomplete_returns_none(self):
        assert _extract_brace_args(r"\resumeSubheading{A}{B", r"\resumeSubheading") is None

    def test_no_command(self):
        assert _extract_brace_args("no command here", r"\resumeSubheading") is None


class TestResumeItemParsing:
    def test_simple_item(self):
        item = _try_parse_resume_item(r"\resumeItem{Did something cool}", False)
        assert item is not None
        assert item.text == "Did something cool"
        assert item.commented is False

    def test_commented_item(self):
        item = _try_parse_resume_item(r"\resumeItem{Old bullet}", True)
        assert item is not None
        assert item.commented is True

    def test_not_an_item(self):
        assert _try_parse_resume_item("just some text", False) is None


@pytest.mark.skipif(not SOURCE_DIR.exists(), reason="Source .tex files not available")
class TestRealImport:
    def test_import_parses_all_sections(self):
        rep = import_tex(SOURCE_DIR / "resume.tex")
        section_names = [s.name for s in rep.sections]
        # Should have at least heading, education, experience, projects, certifications
        assert len(rep.sections) >= 5
        assert any("Experience" in n for n in section_names)
        assert any("Education" in n for n in section_names)
        assert any("Project" in n for n in section_names)

    def test_experience_has_items(self):
        rep = import_tex(SOURCE_DIR / "resume.tex")
        exp = next(s for s in rep.sections if "Experience" in s.name)
        assert len(exp.titles) >= 1
        # Amazon Robotics title should have items
        amz_title = exp.titles[0]
        assert len(amz_title.items) >= 3

    def test_commented_entries_detected(self):
        rep = import_tex(SOURCE_DIR / "resume.tex")
        # Skills section is commented out in resume.tex (%\input{src/skills.tex})
        skills = next((s for s in rep.sections if "Skill" in s.name), None)
        if skills:
            assert skills.commented is True

    def test_projects_has_commented_items(self):
        rep = import_tex(SOURCE_DIR / "resume.tex")
        proj = next(s for s in rep.sections if "Project" in s.name)
        all_items = [item for t in proj.titles for item in t.items]
        commented = [i for i in all_items if i.commented]
        assert len(commented) >= 1, "Should detect commented-out items"

    def test_education_trailing_text(self):
        rep = import_tex(SOURCE_DIR / "resume.tex")
        edu = next(s for s in rep.sections if "Education" in s.name)
        assert len(edu.titles) >= 1
        nau = edu.titles[0]
        assert "Related Courses" in nau.trailing_text or "course" in nau.trailing_text.lower()

    def test_heading_detected(self):
        rep = import_tex(SOURCE_DIR / "resume.tex")
        heading = next(
            (s for s in rep.sections if s.section_type == SectionType.HEADING),
            None,
        )
        assert heading is not None, "Should detect heading section"

    def test_certifications_parsed(self):
        rep = import_tex(SOURCE_DIR / "resume.tex")
        cert = next(s for s in rep.sections if "Certification" in s.name)
        assert len(cert.titles) >= 1
        assert "IBM" in cert.titles[0].arg1 or "Certificate" in cert.titles[0].arg3

    def test_total_item_count(self):
        rep = import_tex(SOURCE_DIR / "resume.tex")
        total = sum(len(t.items) for s in rep.sections for t in s.titles)
        # Should have a reasonable number of items across all sections
        assert total >= 10, f"Expected >=10 items, got {total}"
