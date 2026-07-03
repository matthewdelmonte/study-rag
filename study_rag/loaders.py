"""Source loaders: each source type -> (markdown_text, note_metadata).

Phase 1 implements markdown. PDF and article loaders are stubbed for Phase 3;
they must ultimately return the SAME shape so everything flows through one pipeline.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Note:
    note_id: str            # stable id, e.g. "note::kv-cache"
    title: str
    text: str               # clean markdown body
    source_type: str        # "note" | "pdf" | "article"
    source_path: str
    tags: list[str] = field(default_factory=list)


_FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
_TAGS_LINE = re.compile(r"^tags:\s*\[(.*?)\]", re.MULTILINE)


def load_markdown(path: str) -> Note:
    """Load one Obsidian markdown note into a Note."""
    p = Path(path)
    raw = p.read_text(encoding="utf-8")

    tags: list[str] = []
    m = _FRONTMATTER.match(raw)
    body = raw
    if m:
        fm = m.group(1)
        tm = _TAGS_LINE.search(fm)
        if tm:
            tags = [t.strip().strip("'\"") for t in tm.group(1).split(",") if t.strip()]
        body = raw[m.end():]

    title = p.stem
    return Note(
        note_id=f"note::{p.stem}",
        title=title,
        text=body.strip(),
        source_type="note",
        source_path=str(p),
        tags=tags,
    )


def load_vault(vault_dir: str) -> list[Note]:
    """Load every .md file under a directory."""
    return [load_markdown(str(p)) for p in Path(vault_dir).rglob("*.md")]


# --- Phase 3 stubs ---------------------------------------------------------

def load_pdf(path: str) -> Note:  # TODO Phase 3: pymupdf -> markdown-ish text
    raise NotImplementedError("PDF loading arrives in Phase 3.")


def load_article(url: str) -> Note:  # TODO Phase 3: normalize clipped article to markdown
    raise NotImplementedError("Article loading arrives in Phase 3.")
