"""Store: a single Postgres + pgvector database for both the relational data
(notes, chunks, metadata) and the embedding vectors.

Keeps all storage in one module so the retriever/CLI stay storage-agnostic.
Schema lives in `schema.sql` (applied on container init); see DECISIONS.md.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

import psycopg
from pgvector.psycopg import register_vector

if TYPE_CHECKING:  # avoid import cycles at runtime
    from .chunker import Chunk
    from .loaders import Note

# Host port 5433 (see docker-compose.yml) avoids clashing with a native
# Postgres commonly bound to 5432. Override with STUDY_RAG_DSN if needed.
DEFAULT_DSN = "postgresql://study:study@localhost:5433/study_rag"


class Store:
    def __init__(self, dsn: str | None = None):
        self.dsn = dsn or os.environ.get("STUDY_RAG_DSN", DEFAULT_DSN)
        self.conn = psycopg.connect(self.dsn, autocommit=True)
        register_vector(self.conn)

    def upsert_note(self, note: Note) -> None:
        """Insert (or update) the system-of-record row for a note."""
        self.conn.execute(
            """
            INSERT INTO notes (note_id, title, source_type, source_path, tags)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (note_id) DO UPDATE SET
                title       = EXCLUDED.title,
                source_type = EXCLUDED.source_type,
                source_path = EXCLUDED.source_path,
                tags        = EXCLUDED.tags
            """,
            (note.note_id, note.title, note.source_type, note.source_path, note.tags),
        )

    def add_chunks(
        self, note_id: str, chunks: list[Chunk], embeddings: list[list[float]]
    ) -> None:
        """Replace all of a note's section rows with the given chunks + embeddings.

        Deletes the note's existing chunks first, so re-ingesting an edited note
        can't leave stale sections behind: chunk_ids are positional, so a note
        that shrank or had a section reordered would otherwise orphan old rows.
        Delete + inserts run in one transaction. The parent note must already
        exist (call `upsert_note` first) so the chunks.note_id foreign key
        resolves.
        """
        with self.conn.transaction(), self.conn.cursor() as cur:
            cur.execute("DELETE FROM chunks WHERE note_id = %s", (note_id,))
            for chunk, embedding in zip(chunks, embeddings):
                cur.execute(
                    """
                    INSERT INTO chunks (chunk_id, note_id, section, chunk_text, embedding)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        chunk.chunk_id,
                        chunk.parent_id,
                        chunk.metadata.get("section"),
                        chunk.text,
                        embedding,
                    ),
                )

    def query(
        self,
        embedding: list[float],
        k: int = 4,
        tags: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Return the top-k chunks nearest the query embedding (cosine distance).

        `tags` optionally restricts to notes overlapping any of the given tags.
        Returns clean rows: {text, title, source_path, note_id, section, distance}.
        """
        # Cast the query list to `vector`: the <=> operator has no implicit
        # cast from double precision[] (unlike inserting into a vector column).
        sql = """
            SELECT c.chunk_text, n.title, n.source_path, c.note_id, c.section,
                   c.embedding <=> %(q)s::vector AS distance
            FROM chunks c
            JOIN notes n ON n.note_id = c.note_id
            {where}
            ORDER BY c.embedding <=> %(q)s::vector
            LIMIT %(k)s
        """
        params: dict[str, Any] = {"q": embedding, "k": k}
        where = ""
        if tags:
            where = "WHERE n.tags && %(tags)s"
            params["tags"] = tags

        with self.conn.cursor() as cur:
            cur.execute(sql.format(where=where), params)
            rows = cur.fetchall()

        return [
            {
                "text": text,
                "title": title,
                "source_path": source_path,
                "note_id": note_id,
                "section": section,
                "distance": distance,
            }
            for text, title, source_path, note_id, section, distance in rows
        ]

    def count(self) -> int:
        row = self.conn.execute("SELECT count(*) FROM chunks").fetchone()
        return row[0] if row else 0
