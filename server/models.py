"""Pydantic models for the Resume Builder.

Hierarchy: Repertoire -> Section -> Title -> Item
Active resume stores references by ID with optional tweaks.
"""

from __future__ import annotations

import uuid
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


def new_id() -> str:
    """Generate a short unique ID."""
    return uuid.uuid4().hex[:8]


class SectionType(str, Enum):
    """Types of resume sections with different rendering rules."""
    HEADING = "heading"
    SKILLS = "skills"
    INTRO = "intro"
    STANDARD = "standard"


class EntryVersion(BaseModel):
    """A snapshot of an entry's state at a point in time."""
    timestamp: str  # ISO format
    data: dict  # snapshot of the entry fields
    label: str = ""


class ResumeItem(BaseModel):
    """A single bullet point / resume item."""
    id: str = Field(default_factory=new_id)
    text: str
    commented: bool = False
    versions: list[EntryVersion] = Field(default_factory=list)
    branch_of: Optional[str] = None
    branch_label: str = ""


class ResumeTitle(BaseModel):
    """A subheading with up to 4 arguments and child items."""
    id: str = Field(default_factory=new_id)
    arg1: str = ""
    arg2: str = ""
    arg3: str = ""
    arg4: str = ""
    items: list[ResumeItem] = Field(default_factory=list)
    commented: bool = False
    trailing_text: str = ""
    versions: list[EntryVersion] = Field(default_factory=list)
    branch_of: Optional[str] = None
    branch_label: str = ""


class ResumeSection(BaseModel):
    """A top-level section (Experience, Projects, etc.)."""
    id: str = Field(default_factory=new_id)
    name: str
    section_type: SectionType = SectionType.STANDARD
    titles: list[ResumeTitle] = Field(default_factory=list)
    raw_content: str = ""
    commented: bool = False


class Repertoire(BaseModel):
    """Master library of all resume entries."""
    sections: list[ResumeSection] = Field(default_factory=list)


# --- Active Resume Models ---

class ActiveItemRef(BaseModel):
    """Reference to a repertoire item in the active resume."""
    item_id: str
    tweak: Optional[str] = None


class ActiveTitleRef(BaseModel):
    """Reference to a repertoire title in the active resume."""
    title_id: str
    items: list[ActiveItemRef] = Field(default_factory=list)
    tweak_arg1: Optional[str] = None
    tweak_arg2: Optional[str] = None
    tweak_arg3: Optional[str] = None
    tweak_arg4: Optional[str] = None


class ActiveSectionRef(BaseModel):
    """Reference to a repertoire section in the active resume."""
    section_id: str
    titles: list[ActiveTitleRef] = Field(default_factory=list)


class ActiveResume(BaseModel):
    """The active resume configuration - references into repertoire with tweaks."""
    name: str = "default"
    sections: list[ActiveSectionRef] = Field(default_factory=list)


# --- API Request/Response Models ---

class ReorderRequest(BaseModel):
    """Request to reorder an item."""
    id: str
    new_index: int


class TweakRequest(BaseModel):
    """Request to set a tweak."""
    field: str
    value: str


class TailorAction(BaseModel):
    """A single tailoring action."""
    action: str  # add_section, remove_section, add_title, remove_title,
                 # add_item, remove_item, reorder_section, reorder_title,
                 # reorder_item, tweak, clear_tweak
    target_id: str
    parent_id: Optional[str] = None
    new_index: Optional[int] = None
    field: Optional[str] = None
    value: Optional[str] = None


class TailorRequest(BaseModel):
    """Batch tailoring request."""
    actions: list[TailorAction]


class CompileResult(BaseModel):
    """Result of a compilation."""
    success: bool
    pdf_path: Optional[str] = None
    tex_path: Optional[str] = None
    error: Optional[str] = None
    log: Optional[str] = None
