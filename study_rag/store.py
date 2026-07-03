"""Persistent vector store wrapper around ChromaDB.

Keeps Chroma's API in one place so the retriever/CLI stay storage-agnostic.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import chromadb

DEFAULT_PATH = "data"
DEFAULT_COLLECTION = "study"


class Store:
    def __init__(self, path: str = DEFAULT_PATH, collection: str = DEFAULT_COLLECTION):
        Path(path).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(collection)

    def add(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def query(
        self,
        embedding: list[float],
        n_results: int = 4,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.collection.query(
            query_embeddings=[embedding],
            n_results=n_results,
            where=where,
        )

    def count(self) -> int:
        return self.collection.count()
