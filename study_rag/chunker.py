"""Chunking: split a Note into discrete, embeddable chunks.

DESIGN (see DECISIONS.md):
  - Embed SECTION-level chunks (one idea per vector) for precise matching.
  - Every chunk carries parent_id = the note id, so the retriever can do
    parent-document retrieval (match on section, return the whole note).

>>> PAIR-PROGRAMMING SPOT <<<
This is the piece we reasoned through together — the first thing we build.
Fill in `chunk_note` per the spec below.
"""

from __future__ import annotations

from dataclasses import dataclass

from .loaders import Note


@dataclass
class Chunk:
    chunk_id: str           # e.g. "note::kv-cache::2"
    text: str               # the section text (what we embed)
    parent_id: str          # the note id (what we return to the LLM)
    metadata: dict          # title, source_type, source_path, tags, section


def chunk_note(note: Note) -> list[Chunk]:
    """Split a note into section-level chunks.

    Spec to implement:
      1. Split `note.text` on markdown section headings (`##`, `###`).
         - Text before the first heading is its own chunk (intro).
      2. For each section, build a Chunk with:
           chunk_id  = f"{note.note_id}::{i}"
           text      = the section body (optionally prefixed with the heading,
                       so the embedding knows what the section is about)
           parent_id = note.note_id
           metadata  = {title, source_type, source_path, tags, section}
      3. Return the list of chunks.

    Open question for us to decide while coding:
      - Do we prepend the note title to each section's text so short sections
        keep topical context in their embedding? (Recommended — test both.)
    """
    raise NotImplementedError("Let's build this together — Phase 1 core.")
