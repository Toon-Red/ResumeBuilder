"""LaTeX to JSON parser for importing resume .tex files.

State-machine line-by-line parser that handles:
- \\input{} directives
- \\section{} headers
- \\resumeSubheading{4 args} (possibly multi-line)
- \\resumeItem{text}
- Commented-out entries (%-prefixed)
- Special sections: heading (center block), skills (flat list), intro (no titles)
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from .models import (
    Repertoire,
    ResumeItem,
    ResumeSection,
    ResumeTitle,
    SectionType,
    new_id,
)


def import_tex(main_tex_path: Path) -> Repertoire:
    """Parse a main resume.tex and all its \\input files into a Repertoire.

    Args:
        main_tex_path: Path to the main resume.tex file.

    Returns:
        Populated Repertoire with all sections, titles, and items.
    """
    base_dir = main_tex_path.parent
    lines = main_tex_path.read_text(encoding="utf-8").splitlines()
    repertoire = Repertoire()

    for line in lines:
        stripped = line.strip()
        # Check for \input{src/something} directives
        match = re.match(r"(%?)\\input\{(.+?)\}", stripped)
        if match:
            commented_input = bool(match.group(1))
            input_path = match.group(2)
            # Normalize path (add .tex if missing)
            if not input_path.endswith(".tex"):
                input_path += ".tex"
            full_path = base_dir / input_path
            if full_path.exists():
                section = _parse_section_file(full_path, commented_input)
                if section:
                    repertoire.sections.append(section)

    return repertoire


def _detect_section_type(name: str, content: str) -> SectionType:
    """Detect the section type from its name and content."""
    name_lower = name.lower()
    if "heading" in name_lower or "\\begin{center}" in content:
        return SectionType.HEADING
    if "skill" in name_lower:
        return SectionType.SKILLS
    if "intro" in name_lower:
        return SectionType.INTRO
    return SectionType.STANDARD


def _parse_section_file(
    file_path: Path, commented_from_main: bool = False
) -> Optional[ResumeSection]:
    """Parse a single section .tex file.

    Args:
        file_path: Path to the section .tex file.
        commented_from_main: Whether the \\input line was commented out.

    Returns:
        ResumeSection or None if file is empty/unparseable.
    """
    content = file_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    # Detect section name from \section{Name}
    section_name = file_path.stem.capitalize()
    for line in lines:
        stripped = line.strip().lstrip("%").strip()
        match = re.match(r"\\section\{(.*?)\}", stripped)
        if match:
            section_name = match.group(1)
            if not section_name:
                # Empty section name (like intro)
                section_name = file_path.stem.capitalize()
            break

    section_type = _detect_section_type(section_name, content)

    section = ResumeSection(
        id=new_id(),
        name=section_name,
        section_type=section_type,
        commented=commented_from_main,
    )

    if section_type == SectionType.HEADING:
        section.raw_content = content
        _parse_heading(lines, section)
    elif section_type == SectionType.SKILLS:
        section.raw_content = content
        _parse_skills(lines, section)
    elif section_type == SectionType.INTRO:
        _parse_intro(lines, section)
    else:
        _parse_standard(lines, section)

    return section


def _parse_heading(lines: list[str], section: ResumeSection) -> None:
    """Parse heading section - store as raw content with a single title."""
    # Extract the structured parts from the heading
    title = ResumeTitle(id=new_id())
    for line in lines:
        stripped = line.strip()
        # Get the name
        match = re.search(
            r"\\textbf\{\\Huge\s*\\scshape\s+(.+?)\}", stripped
        )
        if match:
            title.arg1 = match.group(1)

        # Check for commented lines in heading
        if stripped.startswith("%") and "\\href" in stripped:
            text = stripped.lstrip("% \t")
            item = ResumeItem(id=new_id(), text=text, commented=True)
            title.items.append(item)
        elif "\\href" in stripped or "\\underline" in stripped:
            if not stripped.startswith("%"):
                item = ResumeItem(id=new_id(), text=stripped.strip())
                title.items.append(item)

    if title.arg1 or title.items:
        section.titles.append(title)


def _parse_skills(lines: list[str], section: ResumeSection) -> None:
    """Parse skills section - flat list of skills."""
    title = ResumeTitle(id=new_id(), arg1="Technical Skills")
    for line in lines:
        stripped = line.strip()
        is_commented = stripped.startswith("%")
        clean = stripped.lstrip("% \t")

        # Look for \textbf{Category}{: items} pattern
        match = re.match(r"\\textbf\{(.+?)\}\{:\s*(.+?)\}", clean)
        if match:
            item = ResumeItem(
                id=new_id(),
                text=f"\\textbf{{{match.group(1)}}}{{: {match.group(2)}}}",
                commented=is_commented,
            )
            title.items.append(item)
        elif clean and not clean.startswith("\\") and not clean.startswith("{"):
            # Plain text skills line like "Python, C, Java, UML Diagrams"
            if any(c.isalpha() for c in clean):
                # Skip lines that are just closing braces or LaTeX commands
                if not re.match(r"^[}\]]+$", clean) and "begin{" not in clean:
                    item = ResumeItem(
                        id=new_id(), text=clean, commented=is_commented
                    )
                    title.items.append(item)

    if title.items:
        section.titles.append(title)


def _parse_intro(lines: list[str], section: ResumeSection) -> None:
    """Parse intro section - direct bullet items, no subheadings."""
    title = ResumeTitle(id=new_id(), arg1="Introduction")
    in_item_list = False

    for line in lines:
        stripped = line.strip()
        is_commented = stripped.startswith("%")
        clean = stripped.lstrip("% \t")

        if "\\resumeItemListStart" in clean:
            in_item_list = True
            continue
        if "\\resumeItemListEnd" in clean:
            in_item_list = False
            continue

        if in_item_list:
            item = _try_parse_resume_item(clean, is_commented)
            if item:
                title.items.append(item)

    if title.items:
        section.titles.append(title)


def _parse_standard(lines: list[str], section: ResumeSection) -> None:
    """Parse standard section with subheadings and items.

    Handles multi-line \\resumeSubheading by tracking brace depth.
    """
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        is_commented = stripped.startswith("%")
        clean = stripped.lstrip("% \t")

        # Check for \resumeSubheading
        if "\\resumeSubheading" in clean:
            title, i = _parse_subheading(lines, i)
            if title:
                section.titles.append(title)
            continue

        # Check for \resumeProjectHeading
        if "\\resumeProjectHeading" in clean:
            title, i = _parse_project_heading(lines, i)
            if title:
                section.titles.append(title)
            continue

        i += 1


def _parse_subheading(
    lines: list[str], start: int
) -> tuple[Optional[ResumeTitle], int]:
    """Parse a \\resumeSubheading{4 args} which may span multiple lines.

    Returns (title, next_line_index).
    """
    # Determine if the subheading line is commented
    first_line = lines[start].strip()
    is_commented = first_line.startswith("%")

    # Collect all the text for the subheading args
    # Accumulate lines until we have 4 balanced brace groups after \resumeSubheading
    combined = ""
    i = start
    while i < len(lines):
        stripped = lines[i].strip().lstrip("% \t")
        combined += stripped + " "
        # Check if we have enough closing braces
        args = _extract_brace_args(combined, "\\resumeSubheading")
        if args and len(args) >= 4:
            break
        i += 1
    i += 1  # Move past the last subheading line

    args = _extract_brace_args(combined, "\\resumeSubheading")
    if not args or len(args) < 4:
        return None, i

    title = ResumeTitle(
        id=new_id(),
        arg1=args[0],
        arg2=args[1],
        arg3=args[2],
        arg4=args[3],
        commented=is_commented,
    )

    # Now parse items that follow
    in_item_list = False
    while i < len(lines):
        stripped = lines[i].strip()
        is_item_commented = stripped.startswith("%")
        clean = stripped.lstrip("% \t")

        # Hit next subheading or end of list
        if "\\resumeSubheading" in clean and in_item_list is False:
            if "\\resumeSubheading" in clean:
                break
        if "\\resumeProjectHeading" in clean:
            break
        if "\\resumeSubHeadingListEnd" in clean:
            i += 1
            break

        if "\\resumeItemListStart" in clean:
            in_item_list = True
            i += 1
            continue
        if "\\resumeItemListEnd" in clean:
            in_item_list = False
            i += 1
            # Check for trailing text (like "Related Courses: ...")
            while i < len(lines):
                next_stripped = lines[i].strip()
                next_clean = next_stripped.lstrip("% \t")
                if next_clean.startswith("{\\small"):
                    # Trailing text like related courses
                    text = next_clean.strip("{}")
                    if text.startswith("\\small "):
                        text = text[7:]
                    title.trailing_text = text.rstrip("}")
                    i += 1
                elif next_clean and not next_clean.startswith("\\") and not next_clean.startswith("%"):
                    break
                else:
                    break
            continue

        if in_item_list:
            item = _try_parse_resume_item(clean, is_item_commented)
            if item:
                title.items.append(item)

        i += 1

    return title, i


def _parse_project_heading(
    lines: list[str], start: int
) -> tuple[Optional[ResumeTitle], int]:
    """Parse a \\resumeProjectHeading{2 args}."""
    first_line = lines[start].strip()
    is_commented = first_line.startswith("%")

    combined = ""
    i = start
    while i < len(lines):
        stripped = lines[i].strip().lstrip("% \t")
        combined += stripped + " "
        args = _extract_brace_args(combined, "\\resumeProjectHeading")
        if args and len(args) >= 2:
            break
        i += 1
    i += 1

    args = _extract_brace_args(combined, "\\resumeProjectHeading")
    if not args or len(args) < 2:
        return None, i

    title = ResumeTitle(
        id=new_id(),
        arg1=args[0],
        arg2=args[1],
        commented=is_commented,
    )

    # Parse following items
    in_item_list = False
    while i < len(lines):
        stripped = lines[i].strip()
        is_item_commented = stripped.startswith("%")
        clean = stripped.lstrip("% \t")

        if "\\resumeSubheading" in clean or "\\resumeProjectHeading" in clean:
            break
        if "\\resumeSubHeadingListEnd" in clean:
            i += 1
            break

        if "\\resumeItemListStart" in clean:
            in_item_list = True
            i += 1
            continue
        if "\\resumeItemListEnd" in clean:
            in_item_list = False
            i += 1
            continue

        if in_item_list:
            item = _try_parse_resume_item(clean, is_item_commented)
            if item:
                title.items.append(item)

        i += 1

    return title, i


def _extract_brace_args(text: str, command: str) -> Optional[list[str]]:
    """Extract brace-delimited arguments from a LaTeX command.

    Handles nested braces properly via depth tracking.

    Args:
        text: The full text containing the command.
        command: The command name to find (e.g. '\\resumeSubheading').

    Returns:
        List of argument strings, or None if parsing incomplete.
    """
    idx = text.find(command)
    if idx == -1:
        return None

    pos = idx + len(command)
    args = []
    while pos < len(text):
        # Skip whitespace
        while pos < len(text) and text[pos] in " \t\n\r":
            pos += 1
        if pos >= len(text) or text[pos] != "{":
            break

        # Extract balanced braces
        depth = 0
        start = pos + 1
        while pos < len(text):
            if text[pos] == "{":
                depth += 1
            elif text[pos] == "}":
                depth -= 1
                if depth == 0:
                    args.append(text[start:pos].strip())
                    pos += 1
                    break
            pos += 1
        else:
            # Incomplete - brace not closed
            return None

    return args if args else None


def _try_parse_resume_item(
    clean_line: str, is_commented: bool
) -> Optional[ResumeItem]:
    """Try to parse a \\resumeItem{text} from a cleaned line.

    Args:
        clean_line: Line with leading %/whitespace already stripped.
        is_commented: Whether the original line was commented out.

    Returns:
        ResumeItem or None if not a resumeItem line.
    """
    # Match \resumeItem{...} or \resumeItem {..}
    if "\\resumeItem" not in clean_line:
        return None

    args = _extract_brace_args(clean_line, "\\resumeItem")
    if args and args[0]:
        return ResumeItem(id=new_id(), text=args[0], commented=is_commented)
    return None
