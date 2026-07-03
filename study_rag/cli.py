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
from .store import Store

app = typer.Typer(help="study-rag — local RAG over your study notes.")


@app.command()
def ingest(vault: str, db: str = "data"):
    """Load a markdown vault, chunk, embed, and store."""
    notes = load_vault(vault)
    typer.echo(f"Loaded {len(notes)} notes from {vault}")

    embedder = Embedder()
    store = Store(path=db)

    total = 0
    for note in notes:
        chunks = chunk_note(note)
        if not chunks:
            continue
        embeddings = embedder.embed([c.text for c in chunks])
        store.add(
            ids=[c.chunk_id for c in chunks],
            documents=[c.text for c in chunks],
            embeddings=embeddings,
            metadatas=[c.metadata for c in chunks],
        )
        total += len(chunks)

    typer.echo(f"Stored {total} chunks. Collection now holds {store.count()}.")


@app.command()
def query(question: str, db: str = "data", k: int = 4):
    """Retrieve and answer a question from the store."""
    embedder = Embedder()
    store = Store(path=db)
    hits = retrieve(question, store, embedder, k=k)
    typer.echo(answer(question, hits))
    typer.echo("\nSources: " + ", ".join(sorted({h.title for h in hits})))


@app.command()
def eval(db: str = "data", golden: str = "eval/golden.yaml"):
    """Run the golden-question hit-rate (Phase 5)."""
    raise typer.Exit("Eval harness arrives in Phase 5.")


if __name__ == "__main__":
    app()
