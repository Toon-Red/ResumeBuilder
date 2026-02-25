"""Tests for Pydantic models."""

import pytest
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
    new_id,
)


def test_new_id_unique():
    ids = {new_id() for _ in range(100)}
    assert len(ids) == 100


def test_resume_item_defaults():
    item = ResumeItem(text="test bullet")
    assert item.text == "test bullet"
    assert item.commented is False
    assert len(item.id) == 8


def test_resume_title_defaults():
    title = ResumeTitle(arg1="Engineer", arg2="2024")
    assert title.arg1 == "Engineer"
    assert title.items == []
    assert title.commented is False


def test_resume_section_defaults():
    section = ResumeSection(name="Experience")
    assert section.section_type == SectionType.STANDARD
    assert section.titles == []


def test_repertoire_roundtrip():
    r = Repertoire(sections=[
        ResumeSection(name="Exp", titles=[
            ResumeTitle(arg1="Job", items=[
                ResumeItem(text="Did stuff"),
            ]),
        ]),
    ])
    data = r.model_dump()
    r2 = Repertoire.model_validate(data)
    assert r2.sections[0].name == "Exp"
    assert r2.sections[0].titles[0].items[0].text == "Did stuff"


def test_active_resume_structure():
    a = ActiveResume(sections=[
        ActiveSectionRef(section_id="s1", titles=[
            ActiveTitleRef(title_id="t1", items=[
                ActiveItemRef(item_id="i1", tweak="Modified text"),
            ]),
        ]),
    ])
    assert a.sections[0].titles[0].items[0].tweak == "Modified text"


def test_active_resume_tweaks():
    ref = ActiveTitleRef(
        title_id="t1",
        tweak_arg1="New title",
        tweak_arg2=None,
    )
    assert ref.tweak_arg1 == "New title"
    assert ref.tweak_arg2 is None
