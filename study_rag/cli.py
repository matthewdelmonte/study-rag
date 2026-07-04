"""CLI: ingest / query / eval.

Thin orchestration over the modules. Phase 1 wires `ingest`; `query` becomes
live once chunker + generator are filled in.
"""

from __future__ import annotations

import typer

from .chunker import chunk_note
from .embedder import Embedder
from .generator import answer
from .loaders import load_vault
from .retriever import retrieve
from .store import DEFAULT_DSN, Store

app = typer.Typer(help="study-rag — local RAG over your study notes.")


@app.command()
def ingest(vault: str, dsn: str = DEFAULT_DSN):
    """Load a markdown vault, chunk, embed, and store."""
    notes = load_vault(vault)
    typer.echo(f"Loaded {len(notes)} notes from {vault}")

    embedder = Embedder()
    store = Store(dsn=dsn)

    total = 0
    for note in notes:
        store.upsert_note(note)
        chunks = chunk_note(note)
        texts = [c.text for c in chunks]
        embeddings = embedder.embed_documents(texts) if texts else []
        store.add_chunks(note.note_id, chunks, embeddings)
        total += len(chunks)

    typer.echo(f"Stored {total} chunks. Store now holds {store.count()}.")


@app.command()
def query(question: str, dsn: str = DEFAULT_DSN, k: int = 4):
    """Retrieve and answer a question from the store."""
    embedder = Embedder()
    store = Store(dsn=dsn)
    hits = retrieve(question, store, embedder, k=k)
    typer.echo(answer(question, hits))
    typer.echo("\nSources: " + ", ".join(sorted({h.title for h in hits})))


@app.command()
def eval(dsn: str = DEFAULT_DSN, golden: str = "eval/golden.yaml"):
    """Run the golden-question hit-rate (Phase 5)."""
    raise typer.Exit("Eval harness arrives in Phase 5.")


if __name__ == "__main__":
    app()
