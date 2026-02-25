"""Tests for repertoire CRUD operations."""

import pytest
from server.models import Repertoire, ResumeItem, ResumeSection, ResumeTitle, SectionType
from server.repertoire import (
    add_item,
    add_section,
    add_title,
    delete_item,
    delete_section,
    delete_title,
    find_item,
    find_section,
    find_title,
    update_item,
    update_section,
    update_title,
)


@pytest.fixture
def repertoire():
    r = Repertoire()
    s = add_section(r, "Experience")
    t = add_title(r, s.id, "Engineer", "2024", "Company", "Remote")
    add_item(r, t.id, "Did work")
    add_item(r, t.id, "Fixed bugs")
    return r


def test_add_section(repertoire):
    s = add_section(repertoire, "Projects")
    assert s.name == "Projects"
    assert len(repertoire.sections) == 2


def test_find_section(repertoire):
    s = repertoire.sections[0]
    found = find_section(repertoire, s.id)
    assert found is s


def test_update_section(repertoire):
    s = repertoire.sections[0]
    updated = update_section(repertoire, s.id, name="Work Experience")
    assert updated.name == "Work Experience"


def test_delete_section(repertoire):
    s = repertoire.sections[0]
    assert delete_section(repertoire, s.id)
    assert len(repertoire.sections) == 0


def test_add_title(repertoire):
    s = repertoire.sections[0]
    t = add_title(repertoire, s.id, "New Job", "2025")
    assert t.arg1 == "New Job"
    assert len(s.titles) == 2


def test_find_title(repertoire):
    t = repertoire.sections[0].titles[0]
    section, found = find_title(repertoire, t.id)
    assert found is t
    assert section is repertoire.sections[0]


def test_update_title(repertoire):
    t = repertoire.sections[0].titles[0]
    updated = update_title(repertoire, t.id, arg1="Senior Engineer")
    assert updated.arg1 == "Senior Engineer"
    assert updated.arg2 == "2024"  # Unchanged


def test_delete_title(repertoire):
    t = repertoire.sections[0].titles[0]
    assert delete_title(repertoire, t.id)
    assert len(repertoire.sections[0].titles) == 0


def test_add_item(repertoire):
    t = repertoire.sections[0].titles[0]
    item = add_item(repertoire, t.id, "New bullet")
    assert item.text == "New bullet"
    assert len(t.items) == 3


def test_find_item(repertoire):
    item = repertoire.sections[0].titles[0].items[0]
    title, found = find_item(repertoire, item.id)
    assert found is item


def test_update_item(repertoire):
    item = repertoire.sections[0].titles[0].items[0]
    updated = update_item(repertoire, item.id, text="Updated text")
    assert updated.text == "Updated text"


def test_delete_item(repertoire):
    item = repertoire.sections[0].titles[0].items[0]
    assert delete_item(repertoire, item.id)
    assert len(repertoire.sections[0].titles[0].items) == 1


def test_find_nonexistent():
    r = Repertoire()
    assert find_section(r, "nope") is None
    assert find_title(r, "nope") is None
    assert find_item(r, "nope") is None
