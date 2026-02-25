"""Active resume operations.

Manages the active resume configuration - adding/removing references
to repertoire items, reordering, and applying tweaks.
"""

from __future__ import annotations

from typing import Optional

from .models import (
    ActiveItemRef,
    ActiveResume,
    ActiveSectionRef,
    ActiveTitleRef,
    Repertoire,
)
from .repertoire import find_item, find_section, find_title


# --- Add references ---

def add_section_ref(
    active: ActiveResume, repertoire: Repertoire, section_id: str
) -> Optional[ActiveSectionRef]:
    """Add a section reference to the active resume."""
    if not find_section(repertoire, section_id):
        return None
    # Don't add duplicate
    for ref in active.sections:
        if ref.section_id == section_id:
            return ref
    ref = ActiveSectionRef(section_id=section_id)
    active.sections.append(ref)
    return ref


def add_title_ref(
    active: ActiveResume,
    repertoire: Repertoire,
    section_id: str,
    title_id: str,
) -> Optional[ActiveTitleRef]:
    """Add a title reference under a section in the active resume."""
    if not find_title(repertoire, title_id):
        return None
    section_ref = _find_section_ref(active, section_id)
    if not section_ref:
        return None
    for ref in section_ref.titles:
        if ref.title_id == title_id:
            return ref
    ref = ActiveTitleRef(title_id=title_id)
    section_ref.titles.append(ref)
    return ref


def add_item_ref(
    active: ActiveResume,
    repertoire: Repertoire,
    title_id: str,
    item_id: str,
) -> Optional[ActiveItemRef]:
    """Add an item reference under a title in the active resume."""
    if not find_item(repertoire, item_id):
        return None
    title_ref = _find_title_ref(active, title_id)
    if not title_ref:
        return None
    for ref in title_ref.items:
        if ref.item_id == item_id:
            return ref
    ref = ActiveItemRef(item_id=item_id)
    title_ref.items.append(ref)
    return ref


# --- Remove references ---

def remove_section_ref(active: ActiveResume, section_id: str) -> bool:
    """Remove a section reference from the active resume."""
    for i, ref in enumerate(active.sections):
        if ref.section_id == section_id:
            active.sections.pop(i)
            return True
    return False


def remove_title_ref(active: ActiveResume, section_id: str, title_id: str) -> bool:
    """Remove a title reference from a section in the active resume."""
    section_ref = _find_section_ref(active, section_id)
    if not section_ref:
        return False
    for i, ref in enumerate(section_ref.titles):
        if ref.title_id == title_id:
            section_ref.titles.pop(i)
            return True
    return False


def remove_item_ref(active: ActiveResume, title_id: str, item_id: str) -> bool:
    """Remove an item reference from a title in the active resume."""
    title_ref = _find_title_ref(active, title_id)
    if not title_ref:
        return False
    for i, ref in enumerate(title_ref.items):
        if ref.item_id == item_id:
            title_ref.items.pop(i)
            return True
    return False


# --- Reorder ---

def reorder_sections(active: ActiveResume, section_id: str, new_index: int) -> bool:
    """Move a section to a new position."""
    for i, ref in enumerate(active.sections):
        if ref.section_id == section_id:
            ref = active.sections.pop(i)
            new_index = max(0, min(new_index, len(active.sections)))
            active.sections.insert(new_index, ref)
            return True
    return False


def reorder_titles(
    active: ActiveResume, section_id: str, title_id: str, new_index: int
) -> bool:
    """Move a title to a new position within its section."""
    section_ref = _find_section_ref(active, section_id)
    if not section_ref:
        return False
    for i, ref in enumerate(section_ref.titles):
        if ref.title_id == title_id:
            ref = section_ref.titles.pop(i)
            new_index = max(0, min(new_index, len(section_ref.titles)))
            section_ref.titles.insert(new_index, ref)
            return True
    return False


def reorder_items(
    active: ActiveResume, title_id: str, item_id: str, new_index: int
) -> bool:
    """Move an item to a new position within its title."""
    title_ref = _find_title_ref(active, title_id)
    if not title_ref:
        return False
    for i, ref in enumerate(title_ref.items):
        if ref.item_id == item_id:
            ref = title_ref.items.pop(i)
            new_index = max(0, min(new_index, len(title_ref.items)))
            title_ref.items.insert(new_index, ref)
            return True
    return False


# --- Tweaks ---

def set_tweak(
    active: ActiveResume, target_id: str, field: str, value: str
) -> bool:
    """Set a tweak on a title or item in the active resume.

    For items: field='text'
    For titles: field='arg1', 'arg2', 'arg3', or 'arg4'
    """
    # Check items first
    for section_ref in active.sections:
        for title_ref in section_ref.titles:
            if title_ref.title_id == target_id:
                tweak_field = f"tweak_{field}"
                if hasattr(title_ref, tweak_field):
                    setattr(title_ref, tweak_field, value)
                    return True
                return False
            for item_ref in title_ref.items:
                if item_ref.item_id == target_id:
                    if field == "text":
                        item_ref.tweak = value
                        return True
                    return False
    return False


def clear_tweak(active: ActiveResume, target_id: str) -> bool:
    """Clear all tweaks on a target."""
    for section_ref in active.sections:
        for title_ref in section_ref.titles:
            if title_ref.title_id == target_id:
                title_ref.tweak_arg1 = None
                title_ref.tweak_arg2 = None
                title_ref.tweak_arg3 = None
                title_ref.tweak_arg4 = None
                return True
            for item_ref in title_ref.items:
                if item_ref.item_id == target_id:
                    item_ref.tweak = None
                    return True
    return False


def clear_all_tweaks(active: ActiveResume) -> int:
    """Clear all tweaks in the active resume. Returns count cleared."""
    count = 0
    for section_ref in active.sections:
        for title_ref in section_ref.titles:
            if any([
                title_ref.tweak_arg1, title_ref.tweak_arg2,
                title_ref.tweak_arg3, title_ref.tweak_arg4,
            ]):
                title_ref.tweak_arg1 = None
                title_ref.tweak_arg2 = None
                title_ref.tweak_arg3 = None
                title_ref.tweak_arg4 = None
                count += 1
            for item_ref in title_ref.items:
                if item_ref.tweak is not None:
                    item_ref.tweak = None
                    count += 1
    return count


def get_all_tweaks(active: ActiveResume) -> list[dict]:
    """Get all active tweaks."""
    tweaks = []
    for section_ref in active.sections:
        for title_ref in section_ref.titles:
            for field in ["arg1", "arg2", "arg3", "arg4"]:
                val = getattr(title_ref, f"tweak_{field}")
                if val is not None:
                    tweaks.append({
                        "id": title_ref.title_id,
                        "field": field,
                        "value": val,
                    })
            for item_ref in title_ref.items:
                if item_ref.tweak is not None:
                    tweaks.append({
                        "id": item_ref.item_id,
                        "field": "text",
                        "value": item_ref.tweak,
                    })
    return tweaks


def resolve_active(active: ActiveResume, repertoire: Repertoire) -> list[dict]:
    """Resolve active resume references into full data with tweaks applied.

    Returns a list of resolved sections with all text filled in.
    """
    resolved = []
    for section_ref in active.sections:
        section = find_section(repertoire, section_ref.section_id)
        if not section:
            continue
        resolved_section = {
            "id": section.id,
            "name": section.name,
            "section_type": section.section_type.value,
            "raw_content": section.raw_content,
            "titles": [],
        }
        for title_ref in section_ref.titles:
            result = find_title(repertoire, title_ref.title_id)
            if not result:
                continue
            _, title = result
            resolved_title = {
                "id": title.id,
                "arg1": title_ref.tweak_arg1 if title_ref.tweak_arg1 is not None else title.arg1,
                "arg2": title_ref.tweak_arg2 if title_ref.tweak_arg2 is not None else title.arg2,
                "arg3": title_ref.tweak_arg3 if title_ref.tweak_arg3 is not None else title.arg3,
                "arg4": title_ref.tweak_arg4 if title_ref.tweak_arg4 is not None else title.arg4,
                "trailing_text": title.trailing_text,
                "tweaked": any([
                    title_ref.tweak_arg1, title_ref.tweak_arg2,
                    title_ref.tweak_arg3, title_ref.tweak_arg4,
                ]),
                "items": [],
            }
            for item_ref in title_ref.items:
                result = find_item(repertoire, item_ref.item_id)
                if not result:
                    continue
                _, item = result
                resolved_title["items"].append({
                    "id": item.id,
                    "text": item_ref.tweak if item_ref.tweak is not None else item.text,
                    "tweaked": item_ref.tweak is not None,
                })
            resolved_section["titles"].append(resolved_title)
        resolved.append(resolved_section)
    return resolved


# --- Internal helpers ---

def _find_section_ref(
    active: ActiveResume, section_id: str
) -> Optional[ActiveSectionRef]:
    """Find a section ref in the active resume."""
    for ref in active.sections:
        if ref.section_id == section_id:
            return ref
    return None


def _find_title_ref(
    active: ActiveResume, title_id: str
) -> Optional[ActiveTitleRef]:
    """Find a title ref anywhere in the active resume."""
    for section_ref in active.sections:
        for title_ref in section_ref.titles:
            if title_ref.title_id == title_id:
                return title_ref
    return None
