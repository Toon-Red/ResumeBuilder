"""Tests for active resume operations."""

import pytest
from server.models import (
    ActiveResume,
    Repertoire,
    ResumeItem,
    ResumeSection,
    ResumeTitle,
)
from server.active import (
    add_item_ref,
    add_section_ref,
    add_title_ref,
    clear_all_tweaks,
    clear_tweak,
    get_all_tweaks,
    remove_item_ref,
    remove_section_ref,
    remove_title_ref,
    reorder_items,
    reorder_sections,
    reorder_titles,
    resolve_active,
    set_tweak,
)
from server.repertoire import add_item, add_section, add_title


@pytest.fixture
def setup():
    r = Repertoire()
    s = add_section(r, "Experience")
    t = add_title(r, s.id, "Engineer", "2024", "Co", "Remote")
    i1 = add_item(r, t.id, "Bullet 1")
    i2 = add_item(r, t.id, "Bullet 2")

    s2 = add_section(r, "Projects")
    t2 = add_title(r, s2.id, "Project X", "2023")
    i3 = add_item(r, t2.id, "Project bullet")

    a = ActiveResume()
    return r, a, s, t, i1, i2, s2, t2, i3


def test_add_section_ref(setup):
    r, a, s, *_ = setup
    ref = add_section_ref(a, r, s.id)
    assert ref is not None
    assert len(a.sections) == 1


def test_add_duplicate_section(setup):
    r, a, s, *_ = setup
    add_section_ref(a, r, s.id)
    ref2 = add_section_ref(a, r, s.id)
    assert len(a.sections) == 1  # No duplicate


def test_add_title_ref(setup):
    r, a, s, t, *_ = setup
    add_section_ref(a, r, s.id)
    ref = add_title_ref(a, r, s.id, t.id)
    assert ref is not None
    assert len(a.sections[0].titles) == 1


def test_add_item_ref(setup):
    r, a, s, t, i1, *_ = setup
    add_section_ref(a, r, s.id)
    add_title_ref(a, r, s.id, t.id)
    ref = add_item_ref(a, r, t.id, i1.id)
    assert ref is not None


def test_remove_section_ref(setup):
    r, a, s, *_ = setup
    add_section_ref(a, r, s.id)
    assert remove_section_ref(a, s.id)
    assert len(a.sections) == 0


def test_remove_title_ref(setup):
    r, a, s, t, *_ = setup
    add_section_ref(a, r, s.id)
    add_title_ref(a, r, s.id, t.id)
    assert remove_title_ref(a, s.id, t.id)
    assert len(a.sections[0].titles) == 0


def test_remove_item_ref(setup):
    r, a, s, t, i1, *_ = setup
    add_section_ref(a, r, s.id)
    add_title_ref(a, r, s.id, t.id)
    add_item_ref(a, r, t.id, i1.id)
    assert remove_item_ref(a, t.id, i1.id)


def test_reorder_sections(setup):
    r, a, s, _, _, _, s2, *_ = setup
    add_section_ref(a, r, s.id)
    add_section_ref(a, r, s2.id)
    assert reorder_sections(a, s2.id, 0)
    assert a.sections[0].section_id == s2.id


def test_reorder_titles(setup):
    r, a, s, t, _, _, s2, t2, _ = setup
    add_section_ref(a, r, s.id)
    add_title_ref(a, r, s.id, t.id)
    # Add second title to same section for reorder
    t3 = add_title(r, s.id, "New Title")
    add_title_ref(a, r, s.id, t3.id)
    assert reorder_titles(a, s.id, t3.id, 0)
    assert a.sections[0].titles[0].title_id == t3.id


def test_reorder_items(setup):
    r, a, s, t, i1, i2, *_ = setup
    add_section_ref(a, r, s.id)
    add_title_ref(a, r, s.id, t.id)
    add_item_ref(a, r, t.id, i1.id)
    add_item_ref(a, r, t.id, i2.id)
    assert reorder_items(a, t.id, i2.id, 0)
    assert a.sections[0].titles[0].items[0].item_id == i2.id


def test_set_and_clear_tweak(setup):
    r, a, s, t, i1, *_ = setup
    add_section_ref(a, r, s.id)
    add_title_ref(a, r, s.id, t.id)
    add_item_ref(a, r, t.id, i1.id)

    assert set_tweak(a, i1.id, "text", "Modified bullet")
    assert a.sections[0].titles[0].items[0].tweak == "Modified bullet"

    assert clear_tweak(a, i1.id)
    assert a.sections[0].titles[0].items[0].tweak is None


def test_set_title_tweak(setup):
    r, a, s, t, *_ = setup
    add_section_ref(a, r, s.id)
    add_title_ref(a, r, s.id, t.id)

    assert set_tweak(a, t.id, "arg1", "Senior Engineer")
    assert a.sections[0].titles[0].tweak_arg1 == "Senior Engineer"


def test_clear_all_tweaks(setup):
    r, a, s, t, i1, *_ = setup
    add_section_ref(a, r, s.id)
    add_title_ref(a, r, s.id, t.id)
    add_item_ref(a, r, t.id, i1.id)
    set_tweak(a, i1.id, "text", "Tweaked")
    set_tweak(a, t.id, "arg1", "Tweaked title")

    count = clear_all_tweaks(a)
    assert count == 2


def test_get_all_tweaks(setup):
    r, a, s, t, i1, *_ = setup
    add_section_ref(a, r, s.id)
    add_title_ref(a, r, s.id, t.id)
    add_item_ref(a, r, t.id, i1.id)
    set_tweak(a, i1.id, "text", "Tweaked")

    tweaks = get_all_tweaks(a)
    assert len(tweaks) == 1
    assert tweaks[0]["value"] == "Tweaked"


def test_resolve_active(setup):
    r, a, s, t, i1, i2, *_ = setup
    add_section_ref(a, r, s.id)
    add_title_ref(a, r, s.id, t.id)
    add_item_ref(a, r, t.id, i1.id)
    add_item_ref(a, r, t.id, i2.id)

    resolved = resolve_active(a, r)
    assert len(resolved) == 1
    assert resolved[0]["name"] == "Experience"
    assert len(resolved[0]["titles"]) == 1
    assert len(resolved[0]["titles"][0]["items"]) == 2
    assert resolved[0]["titles"][0]["items"][0]["text"] == "Bullet 1"


def test_resolve_with_tweak(setup):
    r, a, s, t, i1, *_ = setup
    add_section_ref(a, r, s.id)
    add_title_ref(a, r, s.id, t.id)
    add_item_ref(a, r, t.id, i1.id)
    set_tweak(a, i1.id, "text", "MODIFIED")

    resolved = resolve_active(a, r)
    assert resolved[0]["titles"][0]["items"][0]["text"] == "MODIFIED"
    assert resolved[0]["titles"][0]["items"][0]["tweaked"] is True
