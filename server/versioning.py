"""Per-entry version history and branching for vault items/titles.

Each edit auto-snapshots the previous state. Entries can be branched
(duplicated for experimental rewrites) and restored to any version.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from .models import EntryVersion, ResumeItem, ResumeTitle, Repertoire, new_id
from .repertoire import find_item, find_title


def snapshot_item(item: ResumeItem, label: str = "") -> None:
    """Save the current state of an item before it's modified."""
    version = EntryVersion(
        timestamp=datetime.now(timezone.utc).isoformat(),
        data={"text": item.text, "commented": item.commented},
        label=label,
    )
    item.versions.append(version)


def snapshot_title(title: ResumeTitle, label: str = "") -> None:
    """Save the current state of a title before it's modified."""
    version = EntryVersion(
        timestamp=datetime.now(timezone.utc).isoformat(),
        data={
            "arg1": title.arg1, "arg2": title.arg2,
            "arg3": title.arg3, "arg4": title.arg4,
        },
        label=label,
    )
    title.versions.append(version)


def restore_item(item: ResumeItem, version_index: int) -> bool:
    """Restore an item to a previous version. Snapshots current state first."""
    if version_index < 0 or version_index >= len(item.versions):
        return False
    # Snapshot current state before restoring
    snapshot_item(item, label="before restore")
    version = item.versions[version_index]
    item.text = version.data.get("text", item.text)
    item.commented = version.data.get("commented", item.commented)
    return True


def restore_title(title: ResumeTitle, version_index: int) -> bool:
    """Restore a title to a previous version. Snapshots current state first."""
    if version_index < 0 or version_index >= len(title.versions):
        return False
    snapshot_title(title, label="before restore")
    version = title.versions[version_index]
    for field in ("arg1", "arg2", "arg3", "arg4"):
        if field in version.data:
            setattr(title, field, version.data[field])
    return True


def branch_item(
    repertoire: Repertoire,
    item_id: str,
    label: str = "",
) -> Optional[ResumeItem]:
    """Create a branch (duplicate) of an item for experimental edits.

    The new item is placed right after the original in the same title.
    """
    result = find_item(repertoire, item_id)
    if not result:
        return None
    parent_title, original = result

    new_item = ResumeItem(
        id=new_id(),
        text=original.text,
        commented=original.commented,
        branch_of=original.id,
        branch_label=label or "experimental",
    )

    # Insert right after the original
    for i, item in enumerate(parent_title.items):
        if item.id == original.id:
            parent_title.items.insert(i + 1, new_item)
            return new_item
    return None


def branch_title(
    repertoire: Repertoire,
    title_id: str,
    label: str = "",
) -> Optional[ResumeTitle]:
    """Create a branch (duplicate) of a title for experimental edits.

    The new title is placed right after the original in the same section.
    Items are NOT duplicated — only the title header fields.
    """
    result = find_title(repertoire, title_id)
    if not result:
        return None
    parent_section, original = result

    new_title = ResumeTitle(
        id=new_id(),
        arg1=original.arg1,
        arg2=original.arg2,
        arg3=original.arg3,
        arg4=original.arg4,
        trailing_text=original.trailing_text,
        branch_of=original.id,
        branch_label=label or "experimental",
    )

    # Copy items too
    for item in original.items:
        new_title.items.append(ResumeItem(
            id=new_id(),
            text=item.text,
            commented=item.commented,
        ))

    for i, title in enumerate(parent_section.titles):
        if title.id == original.id:
            parent_section.titles.insert(i + 1, new_title)
            return new_title
    return None


def get_item_history(repertoire: Repertoire, item_id: str) -> Optional[list[dict]]:
    """Get version history for an item."""
    result = find_item(repertoire, item_id)
    if not result:
        return None
    _, item = result
    return [
        {
            "index": i,
            "timestamp": v.timestamp,
            "label": v.label,
            "data": v.data,
        }
        for i, v in enumerate(item.versions)
    ]


def get_title_history(repertoire: Repertoire, title_id: str) -> Optional[list[dict]]:
    """Get version history for a title."""
    result = find_title(repertoire, title_id)
    if not result:
        return None
    _, title = result
    return [
        {
            "index": i,
            "timestamp": v.timestamp,
            "label": v.label,
            "data": v.data,
        }
        for i, v in enumerate(title.versions)
    ]
