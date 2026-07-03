"""Chunking: split a Note into discrete, embeddable chunks.

DESIGN (see DECISIONS.md):
  - Embed SECTION-level chunks (one idea per vector) for precise matching.
  - Every chunk carries parent_id = the note id, so the retriever can do
    parent-document retrieval (match on section, return the whole note).

Decisions made while building this together:
  - Split on `##` and `###` markdown headings; text before the first heading is
    its own "intro" chunk.
  - Embed each section prefixed with context ("Title > Heading\n\n<body>") so
    short sections keep topical anchoring in their vector. The intro chunk is
    prefixed with just the title.
  - Sections with an empty body are skipped. Chunk indices are contiguous over
    the kept chunks.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .loaders import Note


@dataclass
class Chunk:
    chunk_id: str           # e.g. "note::kv-cache::2"
    text: str               # the section text (what we embed)
    parent_id: str          # the note id (what we return to the LLM)
    metadata: dict          # title, source_type, source_path, tags, section


_HEADING = re.compile(r"^(#{2,3})\s+(.*\S)\s*$")


def chunk_note(note: Note) -> list[Chunk]:
    """Split a note into section-level chunks (see module docstring for rules)."""
    # Bucket lines into sections. The leading (None) bucket holds intro text
    # that appears before the first heading.
    sections: list[tuple[str | None, list[str]]] = [(None, [])]
    for line in note.text.splitlines():
        m = _HEADING.match(line)
        if m:
            sections.append((m.group(2).strip(), []))
        else:
            sections[-1][1].append(line)

    base_meta = {
        "title": note.title,
        "source_type": note.source_type,
        "source_path": note.source_path,
        "tags": note.tags,
    }

    chunks: list[Chunk] = []
    for heading, body_lines in sections:
        body = "\n".join(body_lines).strip()
        if not body:
            continue  # skip empty sections (e.g. a heading with no content)

        if heading:
            section = heading
            text = f"{note.title} > {heading}\n\n{body}"
        else:
            section = note.title  # intro chunk
            text = f"{note.title}\n\n{body}"

        chunks.append(
            Chunk(
                chunk_id=f"{note.note_id}::{len(chunks)}",
                text=text,
                parent_id=note.note_id,
                metadata={**base_meta, "section": section},
            )
        )
    return chunks
