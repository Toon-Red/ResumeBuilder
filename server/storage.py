"""JSON file I/O for repertoire and active resume persistence."""

from __future__ import annotations

import json
from pathlib import Path

from .models import ActiveResume, Repertoire


def load_repertoire(path: Path) -> Repertoire:
    """Load repertoire from JSON file."""
    if not path.exists():
        return Repertoire()
    data = json.loads(path.read_text(encoding="utf-8"))
    return Repertoire.model_validate(data)


def save_repertoire(repertoire: Repertoire, path: Path) -> None:
    """Save repertoire to JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        repertoire.model_dump_json(indent=2),
        encoding="utf-8",
    )


def load_active(path: Path) -> ActiveResume:
    """Load active resume from JSON file."""
    if not path.exists():
        return ActiveResume()
    data = json.loads(path.read_text(encoding="utf-8"))
    return ActiveResume.model_validate(data)


def save_active(active: ActiveResume, path: Path) -> None:
    """Save active resume to JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        active.model_dump_json(indent=2),
        encoding="utf-8",
    )
