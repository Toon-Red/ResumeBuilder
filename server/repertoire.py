"""Repertoire CRUD operations.

Provides functions to query, add, update, and delete sections, titles,
and items in the master repertoire library.
"""

from __future__ import annotations

from typing import Optional

from .models import (
    Repertoire,
    ResumeItem,
    ResumeSection,
    ResumeTitle,
    SectionType,
    new_id,
)


# --- Lookup helpers ---

def find_section(repertoire: Repertoire, section_id: str) -> Optional[ResumeSection]:
    """Find a section by ID."""
    for section in repertoire.sections:
        if section.id == section_id:
            return section
    return None


def find_title(repertoire: Repertoire, title_id: str) -> Optional[tuple[ResumeSection, ResumeTitle]]:
    """Find a title by ID, returns (parent_section, title)."""
    for section in repertoire.sections:
        for title in section.titles:
            if title.id == title_id:
                return section, title
    return None


def find_item(repertoire: Repertoire, item_id: str) -> Optional[tuple[ResumeTitle, ResumeItem]]:
    """Find an item by ID, returns (parent_title, item)."""
    for section in repertoire.sections:
        for title in section.titles:
            for item in title.items:
                if item.id == item_id:
                    return title, item
    return None


# --- Section CRUD ---

def add_section(
    repertoire: Repertoire,
    name: str,
    section_type: SectionType = SectionType.STANDARD,
) -> ResumeSection:
    """Add a new section to the repertoire."""
    section = ResumeSection(id=new_id(), name=name, section_type=section_type)
    repertoire.sections.append(section)
    return section


def update_section(
    repertoire: Repertoire,
    section_id: str,
    name: Optional[str] = None,
    section_type: Optional[SectionType] = None,
) -> Optional[ResumeSection]:
    """Update a section's name or type."""
    section = find_section(repertoire, section_id)
    if not section:
        return None
    if name is not None:
        section.name = name
    if section_type is not None:
        section.section_type = section_type
    return section


def delete_section(repertoire: Repertoire, section_id: str) -> bool:
    """Delete a section by ID."""
    for i, section in enumerate(repertoire.sections):
        if section.id == section_id:
            repertoire.sections.pop(i)
            return True
    return False


# --- Title CRUD ---

def add_title(
    repertoire: Repertoire,
    section_id: str,
    arg1: str = "",
    arg2: str = "",
    arg3: str = "",
    arg4: str = "",
) -> Optional[ResumeTitle]:
    """Add a new title to a section."""
    section = find_section(repertoire, section_id)
    if not section:
        return None
    title = ResumeTitle(id=new_id(), arg1=arg1, arg2=arg2, arg3=arg3, arg4=arg4)
    section.titles.append(title)
    return title


def update_title(
    repertoire: Repertoire,
    title_id: str,
    arg1: Optional[str] = None,
    arg2: Optional[str] = None,
    arg3: Optional[str] = None,
    arg4: Optional[str] = None,
) -> Optional[ResumeTitle]:
    """Update a title's arguments. Auto-snapshots before edit."""
    result = find_title(repertoire, title_id)
    if not result:
        return None
    _, title = result
    # Auto-snapshot before modifying
    if any(v is not None for v in (arg1, arg2, arg3, arg4)):
        from .versioning import snapshot_title
        snapshot_title(title)
    if arg1 is not None:
        title.arg1 = arg1
    if arg2 is not None:
        title.arg2 = arg2
    if arg3 is not None:
        title.arg3 = arg3
    if arg4 is not None:
        title.arg4 = arg4
    return title


def delete_title(repertoire: Repertoire, title_id: str) -> bool:
    """Delete a title by ID."""
    for section in repertoire.sections:
        for i, title in enumerate(section.titles):
            if title.id == title_id:
                section.titles.pop(i)
                return True
    return False


# --- Item CRUD ---

def add_item(
    repertoire: Repertoire,
    title_id: str,
    text: str,
) -> Optional[ResumeItem]:
    """Add a new item to a title."""
    result = find_title(repertoire, title_id)
    if not result:
        return None
    _, title = result
    item = ResumeItem(id=new_id(), text=text)
    title.items.append(item)
    return item


def update_item(
    repertoire: Repertoire,
    item_id: str,
    text: Optional[str] = None,
) -> Optional[ResumeItem]:
    """Update an item's text. Auto-snapshots before edit."""
    result = find_item(repertoire, item_id)
    if not result:
        return None
    _, item = result
    if text is not None:
        from .versioning import snapshot_item
        snapshot_item(item)
        item.text = text
    return item


def delete_item(repertoire: Repertoire, item_id: str) -> bool:
    """Delete an item by ID."""
    for section in repertoire.sections:
        for title in section.titles:
            for i, item in enumerate(title.items):
                if item.id == item_id:
                    title.items.pop(i)
                    return True
    return False
