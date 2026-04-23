"""Tests for the section template library."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from server.models import ActiveResume, Repertoire
from server.templates import apply_template, get_template, list_templates


class TestListTemplates:
    def test_returns_five_templates(self):
        templates = list_templates()
        assert len(templates) == 5

    def test_all_required_ids_present(self):
        ids = {t["id"] for t in list_templates()}
        assert "chronological" in ids
        assert "functional" in ids
        assert "combination" in ids
        assert "tech" in ids
        assert "executive" in ids

    def test_each_template_has_metadata(self):
        for t in list_templates():
            assert t["name"]
            assert t["description"]
            assert t["section_count"] > 0
            assert len(t["section_names"]) == t["section_count"]


class TestGetTemplate:
    def test_known_template_returned(self):
        tmpl = get_template("tech")
        assert tmpl is not None
        assert tmpl["name"] == "Tech-focused"

    def test_unknown_template_returns_none(self):
        assert get_template("nonexistent") is None


class TestApplyTemplate:
    def _apply(self, template_id: str):
        r = Repertoire()
        a = ActiveResume()
        return apply_template(template_id, r, a)

    def test_chronological_creates_five_sections(self):
        r, a = self._apply("chronological")
        assert len(r.sections) == 5

    def test_tech_creates_six_sections(self):
        r, a = self._apply("tech")
        assert len(r.sections) == 6

    def test_active_resume_matches_repertoire(self):
        r, a = self._apply("combination")
        assert len(a.sections) == len(r.sections)
        for sec_ref, sec in zip(a.sections, r.sections):
            assert sec_ref.section_id == sec.id

    def test_section_type_mapping(self):
        r, _ = self._apply("tech")
        types = {s.name: s.section_type.value for s in r.sections}
        assert types["Technical Skills"] == "skills"
        assert types["Experience"] == "standard"
        assert types["Summary"] == "intro"
        assert types["Contact"] == "heading"

    def test_placeholder_items_populated(self):
        r, _ = self._apply("tech")
        exp_section = next(s for s in r.sections if s.name == "Experience")
        assert len(exp_section.titles) >= 1
        title = exp_section.titles[0]
        assert title.arg1 != ""
        assert len(title.items) >= 1

    def test_unknown_template_raises(self):
        with pytest.raises(ValueError, match="Unknown template"):
            apply_template("nope", Repertoire(), ActiveResume())

    def test_preserves_existing_repertoire_content(self):
        from server.models import ResumeSection
        r = Repertoire()
        r.sections.append(ResumeSection(name="Existing Section"))
        a = ActiveResume()
        r, a = apply_template("functional", r, a)
        names = [s.name for s in r.sections]
        assert "Existing Section" in names
        assert "Contact" in names

    def test_active_refs_have_correct_title_ids(self):
        r, a = self._apply("chronological")
        for sec_ref, sec in zip(a.sections, r.sections):
            expected_ids = {t.id for t in sec.titles}
            actual_ids = {tr.title_id for tr in sec_ref.titles}
            assert actual_ids == expected_ids
