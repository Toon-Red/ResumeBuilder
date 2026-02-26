"""LaTeX compiler - generates .tex from active resume and compiles to PDF.

Resolves active references -> repertoire items, applies tweak overlay,
generates section-type-specific LaTeX, writes to output/, calls pdflatex.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional

from .active import resolve_active
from .models import ActiveResume, CompileResult, Repertoire, SectionType


def generate_tex(
    active: ActiveResume,
    repertoire: Repertoire,
    template_dir: Path,
    output_dir: Path,
) -> Path:
    """Generate a .tex file from the active resume.

    Args:
        active: The active resume configuration.
        repertoire: The master repertoire.
        template_dir: Directory containing preamble.tex and custom-commands.tex.
        output_dir: Directory to write the output .tex file.

    Returns:
        Path to the generated .tex file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    preamble = (template_dir / "preamble.tex").read_text(encoding="utf-8")
    custom_commands = (template_dir / "custom-commands.tex").read_text(encoding="utf-8")

    resolved = resolve_active(active, repertoire)

    lines = []
    lines.append(preamble)
    lines.append("")
    lines.append("% Custom commands")
    lines.append(custom_commands)
    lines.append("")
    lines.append("\\begin{document}")
    lines.append("")

    for section_data in resolved:
        section_type = section_data["section_type"]
        section_tex = _render_section(section_data, section_type)
        lines.append(section_tex)
        lines.append("")

    lines.append("\\end{document}")

    tex_path = output_dir / "resume.tex"
    tex_path.write_text("\n".join(lines), encoding="utf-8")
    return tex_path


def compile_pdf(
    active: ActiveResume,
    repertoire: Repertoire,
    template_dir: Path,
    output_dir: Path,
    pdflatex_path: str = "pdflatex",
) -> CompileResult:
    """Generate .tex and compile to PDF.

    Args:
        active: The active resume configuration.
        repertoire: The master repertoire.
        template_dir: Template directory path.
        output_dir: Output directory path.
        pdflatex_path: Path to pdflatex executable.

    Returns:
        CompileResult with success status and paths.
    """
    try:
        tex_path = generate_tex(active, repertoire, template_dir, output_dir)
    except Exception as e:
        return CompileResult(success=False, error=f"TeX generation failed: {e}")

    pdf_path = output_dir / "resume.pdf"

    try:
        result = subprocess.run(
            [
                pdflatex_path,
                "-interaction=nonstopmode",
                "-output-directory", str(output_dir),
                str(tex_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(output_dir),
        )

        if result.returncode != 0 and not pdf_path.exists():
            log_path = output_dir / "resume.log"
            log_text = ""
            if log_path.exists():
                log_text = log_path.read_text(encoding="utf-8", errors="replace")
            return CompileResult(
                success=False,
                tex_path=str(tex_path),
                error="pdflatex compilation failed",
                log=log_text[-2000:] if log_text else result.stderr[-2000:],
            )

        return CompileResult(
            success=True,
            pdf_path=str(pdf_path),
            tex_path=str(tex_path),
        )

    except FileNotFoundError:
        return CompileResult(
            success=False,
            tex_path=str(tex_path),
            error=f"pdflatex not found at: {pdflatex_path}",
        )
    except subprocess.TimeoutExpired:
        return CompileResult(
            success=False,
            tex_path=str(tex_path),
            error="pdflatex timed out after 30 seconds",
        )


def _render_section(section_data: dict, section_type: str) -> str:
    """Render a resolved section to LaTeX."""
    if section_type == SectionType.HEADING.value:
        return _render_heading(section_data)
    elif section_type == SectionType.SKILLS.value:
        return _render_skills(section_data)
    elif section_type == SectionType.INTRO.value:
        return _render_intro(section_data)
    else:
        return _render_standard(section_data)


def _render_heading(section_data: dict) -> str:
    """Render heading section (centered contact block)."""
    # If we have raw_content stored, check for resolved titles
    titles = section_data.get("titles", [])
    if not titles:
        return section_data.get("raw_content", "")

    title = titles[0]
    lines = []
    lines.append("\\begin{center}")
    lines.append(
        f"\t\\textbf{{\\Huge \\scshape {title['arg1']}}} \\\\ \\vspace{{1pt}}"
    )

    for item in title.get("items", []):
        lines.append(f"\t{item['text']}")

    lines.append("\\end{center}")
    return "\n".join(lines)


def _render_skills(section_data: dict) -> str:
    """Render skills section (flat comma list)."""
    lines = []
    lines.append(f"\\section{{{section_data['name']}}}")
    lines.append("    \\begin{itemize}[leftmargin=0.15in, label={}]")
    lines.append("\t\\small{\\item{")

    for title in section_data.get("titles", []):
        for item in title.get("items", []):
            lines.append(f"\t\t{item['text']}")

    lines.append("\t}}")
    lines.append("    \\end{itemize}")
    return "\n".join(lines)


def _render_intro(section_data: dict) -> str:
    """Render intro section (no header, direct bullets)."""
    lines = []
    name = section_data["name"]
    lines.append(f"\\section{{{name}}}")
    lines.append("")
    lines.append("\\resumeItemListStart")

    for title in section_data.get("titles", []):
        for item in title.get("items", []):
            lines.append(f"\\resumeItem{{{item['text']}}}")

    lines.append("\\resumeItemListEnd")
    return "\n".join(lines)


def _render_standard(section_data: dict) -> str:
    """Render standard section with subheadings and items."""
    lines = []
    lines.append(f"\\section{{{section_data['name']}}}")
    lines.append("\\resumeSubHeadingListStart")
    lines.append("")

    for title in section_data.get("titles", []):
        # Determine if it's a 2-arg (project heading) or 4-arg (subheading)
        has_arg3_or_4 = title.get("arg3") or title.get("arg4")
        if has_arg3_or_4:
            arg4 = title.get("arg4", "")
            lines.append("\\resumeSubheading")
            lines.append(f"{{{title['arg1']}}}")
            lines.append(f"{{{title['arg2']}}}")
            lines.append(f"{{{title['arg3']}}}")
            if len(arg4) > 45:
                lines.append(f"{{\\scriptsize {arg4}}}")
            else:
                lines.append(f"{{{arg4}}}")
        else:
            lines.append("\\resumeProjectHeading")
            lines.append(f"{{{title['arg1']}}}{{{title['arg2']}}}")

        items = title.get("items", [])
        if items:
            lines.append("\\resumeItemListStart")
            for item in items:
                lines.append(f"    \\resumeItem{{{item['text']}}}")
            lines.append("\\resumeItemListEnd")

        trailing = title.get("trailing_text", "")
        if trailing:
            lines.append(f"    {{\\small {trailing}}}")

        lines.append("")

    lines.append("\\resumeSubHeadingListEnd")
    return "\n".join(lines)
