"""FastAPI routes for the Resume Builder.

All REST endpoints for repertoire CRUD, active resume management,
compilation, and Claude Code tailoring.
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import active as active_ops
from . import repertoire as rep_ops
from .jd_routes import router as jd_router
from .compiler import compile_pdf, generate_tex
from .importer import import_tex
from .models import (
    ActiveResume,
    CompileResult,
    ReorderRequest,
    Repertoire,
    SectionType,
    TailorRequest,
    TweakRequest,
)
from .storage import load_active, load_repertoire, save_active, save_repertoire

app = FastAPI(title="Resume Builder", version="1.0.0")
app.include_router(jd_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files & index.html
_frontend_dir = Path(__file__).resolve().parent.parent / "frontend"

app.mount("/static", StaticFiles(directory=str(_frontend_dir)), name="static")


@app.get("/")
def serve_index():
    """Serve the frontend index.html."""
    return FileResponse(str(_frontend_dir / "index.html"))

# Paths - set by init_app()
_data_dir: Path = Path("data")
_output_dir: Path = Path("output")
_template_dir: Path = Path("data/templates")
_source_dir: Path = Path(".")
_pdflatex_path: str = "pdflatex"


def init_app(config: dict, base_dir: Path) -> None:
    """Initialize app with config paths."""
    global _data_dir, _output_dir, _template_dir, _source_dir, _pdflatex_path
    _data_dir = base_dir / config.get("data_dir", "data")
    _output_dir = base_dir / config.get("output_dir", "output")
    _template_dir = base_dir / config.get("template_dir", "data/templates")
    _source_dir = Path(config.get("source_dir", "."))
    _pdflatex_path = config.get("pdflatex_path", "pdflatex")


def _rep_path() -> Path:
    return _data_dir / "repertoire.json"


def _active_path() -> Path:
    return _data_dir / "active" / "default.json"


def _load_rep() -> Repertoire:
    return load_repertoire(_rep_path())


def _save_rep(r: Repertoire) -> None:
    save_repertoire(r, _rep_path())


def _load_active() -> ActiveResume:
    return load_active(_active_path())


def _save_active(a: ActiveResume) -> None:
    save_active(a, _active_path())


# ============================================================
# Repertoire CRUD
# ============================================================

@app.get("/api/repertoire")
def get_repertoire():
    """Get the full repertoire tree."""
    return _load_rep().model_dump()


@app.post("/api/repertoire/sections")
def create_section(body: dict):
    """Create a new section."""
    r = _load_rep()
    section_type = SectionType(body.get("section_type", "standard"))
    section = rep_ops.add_section(r, body["name"], section_type)
    _save_rep(r)
    return section.model_dump()


@app.put("/api/repertoire/sections/{section_id}")
def update_section(section_id: str, body: dict):
    """Update a section."""
    r = _load_rep()
    st = SectionType(body["section_type"]) if "section_type" in body else None
    section = rep_ops.update_section(r, section_id, body.get("name"), st)
    if not section:
        raise HTTPException(404, "Section not found")
    _save_rep(r)
    return section.model_dump()


@app.delete("/api/repertoire/sections/{section_id}")
def delete_section(section_id: str):
    """Delete a section."""
    r = _load_rep()
    if not rep_ops.delete_section(r, section_id):
        raise HTTPException(404, "Section not found")
    _save_rep(r)
    return {"ok": True}


@app.post("/api/repertoire/titles/{section_id}")
def create_title(section_id: str, body: dict):
    """Create a new title in a section."""
    r = _load_rep()
    title = rep_ops.add_title(
        r, section_id,
        body.get("arg1", ""), body.get("arg2", ""),
        body.get("arg3", ""), body.get("arg4", ""),
    )
    if not title:
        raise HTTPException(404, "Section not found")
    _save_rep(r)
    return title.model_dump()


@app.put("/api/repertoire/titles/{title_id}")
def update_title(title_id: str, body: dict):
    """Update a title."""
    r = _load_rep()
    title = rep_ops.update_title(
        r, title_id,
        body.get("arg1"), body.get("arg2"),
        body.get("arg3"), body.get("arg4"),
    )
    if not title:
        raise HTTPException(404, "Title not found")
    _save_rep(r)
    return title.model_dump()


@app.delete("/api/repertoire/titles/{title_id}")
def delete_title(title_id: str):
    """Delete a title."""
    r = _load_rep()
    if not rep_ops.delete_title(r, title_id):
        raise HTTPException(404, "Title not found")
    _save_rep(r)
    return {"ok": True}


@app.post("/api/repertoire/items/{title_id}")
def create_item(title_id: str, body: dict):
    """Create a new item in a title."""
    r = _load_rep()
    item = rep_ops.add_item(r, title_id, body["text"])
    if not item:
        raise HTTPException(404, "Title not found")
    _save_rep(r)
    return item.model_dump()


@app.put("/api/repertoire/items/{item_id}")
def update_item(item_id: str, body: dict):
    """Update an item."""
    r = _load_rep()
    item = rep_ops.update_item(r, item_id, body.get("text"))
    if not item:
        raise HTTPException(404, "Item not found")
    _save_rep(r)
    return item.model_dump()


@app.delete("/api/repertoire/items/{item_id}")
def delete_item(item_id: str):
    """Delete an item."""
    r = _load_rep()
    if not rep_ops.delete_item(r, item_id):
        raise HTTPException(404, "Item not found")
    _save_rep(r)
    return {"ok": True}


# ============================================================
# Version History / Branching
# ============================================================

@app.get("/api/repertoire/items/{item_id}/history")
def item_history(item_id: str):
    """Get version history for an item."""
    from .versioning import get_item_history
    r = _load_rep()
    history = get_item_history(r, item_id)
    if history is None:
        raise HTTPException(404, "Item not found")
    return {"versions": history}


@app.post("/api/repertoire/items/{item_id}/restore")
def item_restore(item_id: str, body: dict):
    """Restore an item to a previous version."""
    from .versioning import restore_item
    from .repertoire import find_item
    r = _load_rep()
    result = find_item(r, item_id)
    if not result:
        raise HTTPException(404, "Item not found")
    _, item = result
    if not restore_item(item, body.get("version_index", 0)):
        raise HTTPException(400, "Invalid version index")
    _save_rep(r)
    return {"ok": True, "text": item.text}


@app.post("/api/repertoire/items/{item_id}/branch")
def item_branch(item_id: str, body: dict):
    """Branch (duplicate) an item for experimental edits."""
    from .versioning import branch_item
    r = _load_rep()
    new_item = branch_item(r, item_id, body.get("label", ""))
    if not new_item:
        raise HTTPException(404, "Item not found")
    _save_rep(r)
    return new_item.model_dump()


@app.get("/api/repertoire/titles/{title_id}/history")
def title_history(title_id: str):
    """Get version history for a title."""
    from .versioning import get_title_history
    r = _load_rep()
    history = get_title_history(r, title_id)
    if history is None:
        raise HTTPException(404, "Title not found")
    return {"versions": history}


@app.post("/api/repertoire/titles/{title_id}/restore")
def title_restore(title_id: str, body: dict):
    """Restore a title to a previous version."""
    from .versioning import restore_title
    from .repertoire import find_title
    r = _load_rep()
    result = find_title(r, title_id)
    if not result:
        raise HTTPException(404, "Title not found")
    _, title = result
    if not restore_title(title, body.get("version_index", 0)):
        raise HTTPException(400, "Invalid version index")
    _save_rep(r)
    return {"ok": True, "arg1": title.arg1, "arg2": title.arg2}


@app.post("/api/repertoire/titles/{title_id}/branch")
def title_branch(title_id: str, body: dict):
    """Branch (duplicate) a title for experimental edits."""
    from .versioning import branch_title
    r = _load_rep()
    new_title = branch_title(r, title_id, body.get("label", ""))
    if not new_title:
        raise HTTPException(404, "Title not found")
    _save_rep(r)
    return new_title.model_dump()


# ============================================================
# Active Resume
# ============================================================

@app.get("/api/active")
def get_active():
    """Get resolved active resume with text filled in."""
    a = _load_active()
    r = _load_rep()
    return {"name": a.name, "sections": active_ops.resolve_active(a, r)}


@app.get("/api/active/raw")
def get_active_raw():
    """Get raw active resume config (refs only)."""
    return _load_active().model_dump()


@app.post("/api/active/sections")
def add_active_section(body: dict):
    """Add a section reference to the active resume."""
    a = _load_active()
    r = _load_rep()
    ref = active_ops.add_section_ref(a, r, body["section_id"])
    if not ref:
        raise HTTPException(404, "Section not found in repertoire")
    _save_active(a)
    return ref.model_dump()


@app.delete("/api/active/sections/{section_id}")
def remove_active_section(section_id: str):
    """Remove a section from the active resume."""
    a = _load_active()
    if not active_ops.remove_section_ref(a, section_id):
        raise HTTPException(404, "Section not in active resume")
    _save_active(a)
    return {"ok": True}


@app.post("/api/active/sections/{section_id}/titles")
def add_active_title(section_id: str, body: dict):
    """Add a title reference to a section in the active resume."""
    a = _load_active()
    r = _load_rep()
    ref = active_ops.add_title_ref(a, r, section_id, body["title_id"])
    if not ref:
        raise HTTPException(404, "Title or section not found")
    _save_active(a)
    return ref.model_dump()


@app.delete("/api/active/sections/{section_id}/titles/{title_id}")
def remove_active_title(section_id: str, title_id: str):
    """Remove a title from the active resume."""
    a = _load_active()
    if not active_ops.remove_title_ref(a, section_id, title_id):
        raise HTTPException(404, "Title not in active section")
    _save_active(a)
    return {"ok": True}


@app.post("/api/active/titles/{title_id}/items")
def add_active_item(title_id: str, body: dict):
    """Add an item reference to a title in the active resume."""
    a = _load_active()
    r = _load_rep()
    ref = active_ops.add_item_ref(a, r, title_id, body["item_id"])
    if not ref:
        raise HTTPException(404, "Item or title not found")
    _save_active(a)
    return ref.model_dump()


@app.delete("/api/active/titles/{title_id}/items/{item_id}")
def remove_active_item(title_id: str, item_id: str):
    """Remove an item from the active resume."""
    a = _load_active()
    if not active_ops.remove_item_ref(a, title_id, item_id):
        raise HTTPException(404, "Item not in active title")
    _save_active(a)
    return {"ok": True}


# ============================================================
# Reorder
# ============================================================

@app.post("/api/active/sections/reorder")
def reorder_sections(body: ReorderRequest):
    """Reorder a section in the active resume."""
    a = _load_active()
    if not active_ops.reorder_sections(a, body.id, body.new_index):
        raise HTTPException(404, "Section not found")
    _save_active(a)
    return {"ok": True}


@app.post("/api/active/sections/{section_id}/titles/reorder")
def reorder_titles(section_id: str, body: ReorderRequest):
    """Reorder a title within a section."""
    a = _load_active()
    if not active_ops.reorder_titles(a, section_id, body.id, body.new_index):
        raise HTTPException(404, "Title or section not found")
    _save_active(a)
    return {"ok": True}


@app.post("/api/active/titles/{title_id}/items/reorder")
def reorder_items(title_id: str, body: ReorderRequest):
    """Reorder an item within a title."""
    a = _load_active()
    if not active_ops.reorder_items(a, title_id, body.id, body.new_index):
        raise HTTPException(404, "Item or title not found")
    _save_active(a)
    return {"ok": True}


# ============================================================
# Tweaks
# ============================================================

@app.put("/api/active/tweaks/{target_id}")
def set_tweak(target_id: str, body: TweakRequest):
    """Set a tweak on a title or item."""
    a = _load_active()
    if not active_ops.set_tweak(a, target_id, body.field, body.value):
        raise HTTPException(404, "Target not found in active resume")
    _save_active(a)
    return {"ok": True}


@app.delete("/api/active/tweaks/{target_id}")
def clear_tweak(target_id: str):
    """Clear tweaks on a target."""
    a = _load_active()
    if not active_ops.clear_tweak(a, target_id):
        raise HTTPException(404, "Target not found")
    _save_active(a)
    return {"ok": True}


@app.post("/api/active/tweaks/{target_id}/commit")
def commit_tweak(target_id: str):
    """Commit a tweak to the vault — saves tweaked text permanently."""
    a = _load_active()
    r = _load_rep()
    if not active_ops.commit_tweak(a, r, target_id):
        raise HTTPException(404, "Target not found or no tweak to commit")
    _save_rep(r)
    _save_active(a)
    return {"ok": True}


@app.get("/api/active/tweaks")
def list_tweaks():
    """List all active tweaks."""
    a = _load_active()
    return {"tweaks": active_ops.get_all_tweaks(a)}


# ============================================================
# Compile
# ============================================================

@app.post("/api/compile")
def compile_resume():
    """Compile the active resume to PDF."""
    a = _load_active()
    r = _load_rep()
    result = compile_pdf(a, r, _template_dir, _output_dir, _pdflatex_path)
    return result.model_dump()


@app.get("/api/compile/preview")
def preview_pdf():
    """Serve the last compiled PDF."""
    pdf_path = _output_dir / "resume.pdf"
    if not pdf_path.exists():
        raise HTTPException(404, "No compiled PDF found. Compile first.")
    return FileResponse(pdf_path, media_type="application/pdf")


@app.get("/api/compile/tex")
def get_tex():
    """Get the generated .tex source."""
    tex_path = _output_dir / "resume.tex"
    if not tex_path.exists():
        raise HTTPException(404, "No generated .tex found. Compile first.")
    return {"tex": tex_path.read_text(encoding="utf-8")}


# ============================================================
# Import / Export
# ============================================================

@app.post("/api/import/tex")
def import_from_tex():
    """Import from the configured source .tex files."""
    main_tex = _source_dir / "resume.tex"
    if not main_tex.exists():
        raise HTTPException(404, f"Source not found: {main_tex}")
    repertoire = import_tex(main_tex)
    _save_rep(repertoire)

    # Auto-build active resume with all non-commented entries
    active = _auto_build_active(repertoire)
    _save_active(active)

    section_count = len(repertoire.sections)
    title_count = sum(len(s.titles) for s in repertoire.sections)
    item_count = sum(
        len(t.items) for s in repertoire.sections for t in s.titles
    )
    return {
        "ok": True,
        "sections": section_count,
        "titles": title_count,
        "items": item_count,
    }


@app.get("/api/export/tex")
def export_tex():
    """Export current active resume as .tex source."""
    a = _load_active()
    r = _load_rep()
    tex_path = generate_tex(a, r, _template_dir, _output_dir)
    return {"tex": tex_path.read_text(encoding="utf-8")}


# ============================================================
# Tailoring (Claude Code CLI)
# ============================================================

@app.get("/api/tailor/state")
def tailor_state():
    """Full state dump for Claude Code tailoring."""
    r = _load_rep()
    a = _load_active()
    resolved = active_ops.resolve_active(a, r)
    tweaks = active_ops.get_all_tweaks(a)

    # Stats
    total_items = sum(
        len(t.items) for s in r.sections for t in s.titles
    )
    active_items = sum(
        len(t["items"]) for s in resolved for t in s["titles"]
    )

    return {
        "repertoire": r.model_dump(),
        "active": {"name": a.name, "sections": resolved},
        "active_raw": a.model_dump(),
        "tweaks": tweaks,
        "stats": {
            "repertoire_sections": len(r.sections),
            "repertoire_items": total_items,
            "active_sections": len(resolved),
            "active_items": active_items,
        },
    }


@app.post("/api/tailor/apply")
def tailor_apply(body: TailorRequest):
    """Apply batch tailoring actions."""
    a = _load_active()
    r = _load_rep()
    results = []

    for action in body.actions:
        result = _apply_tailor_action(a, r, action)
        results.append(result)

    _save_active(a)
    return {"results": results}


@app.post("/api/tailor/clear-tweaks")
def tailor_clear_tweaks():
    """Clear all tweaks."""
    a = _load_active()
    count = active_ops.clear_all_tweaks(a)
    _save_active(a)
    return {"ok": True, "cleared": count}


def _apply_tailor_action(a: ActiveResume, r: Repertoire, action) -> dict:
    """Apply a single tailoring action."""
    try:
        if action.action == "add_section":
            ref = active_ops.add_section_ref(a, r, action.target_id)
            return {"ok": ref is not None, "action": action.action}
        elif action.action == "remove_section":
            ok = active_ops.remove_section_ref(a, action.target_id)
            return {"ok": ok, "action": action.action}
        elif action.action == "add_title":
            ref = active_ops.add_title_ref(
                a, r, action.parent_id, action.target_id
            )
            return {"ok": ref is not None, "action": action.action}
        elif action.action == "remove_title":
            ok = active_ops.remove_title_ref(a, action.parent_id, action.target_id)
            return {"ok": ok, "action": action.action}
        elif action.action == "add_item":
            ref = active_ops.add_item_ref(
                a, r, action.parent_id, action.target_id
            )
            return {"ok": ref is not None, "action": action.action}
        elif action.action == "remove_item":
            ok = active_ops.remove_item_ref(a, action.parent_id, action.target_id)
            return {"ok": ok, "action": action.action}
        elif action.action == "reorder_section":
            ok = active_ops.reorder_sections(a, action.target_id, action.new_index)
            return {"ok": ok, "action": action.action}
        elif action.action == "reorder_title":
            ok = active_ops.reorder_titles(
                a, action.parent_id, action.target_id, action.new_index
            )
            return {"ok": ok, "action": action.action}
        elif action.action == "reorder_item":
            ok = active_ops.reorder_items(
                a, action.parent_id, action.target_id, action.new_index
            )
            return {"ok": ok, "action": action.action}
        elif action.action == "tweak":
            ok = active_ops.set_tweak(
                a, action.target_id, action.field, action.value
            )
            return {"ok": ok, "action": action.action}
        elif action.action == "clear_tweak":
            ok = active_ops.clear_tweak(a, action.target_id)
            return {"ok": ok, "action": action.action}
        else:
            return {"ok": False, "action": action.action, "error": "Unknown action"}
    except Exception as e:
        return {"ok": False, "action": action.action, "error": str(e)}


def _auto_build_active(repertoire: Repertoire) -> ActiveResume:
    """Build an active resume with all non-commented entries."""
    from .models import ActiveItemRef, ActiveSectionRef, ActiveTitleRef

    active = ActiveResume()
    for section in repertoire.sections:
        if section.commented:
            continue
        section_ref = ActiveSectionRef(section_id=section.id)
        for title in section.titles:
            if title.commented:
                continue
            title_ref = ActiveTitleRef(title_id=title.id)
            for item in title.items:
                if item.commented:
                    continue
                title_ref.items.append(ActiveItemRef(item_id=item.id))
            section_ref.titles.append(title_ref)
        active.sections.append(section_ref)
    return active
