"""
RAGService
==========
Thin wrapper around ChromaDB for per-session vector storage and retrieval.

Each session gets its own ChromaDB collection so sessions are isolated and
can be cleaned up independently.  ChromaDB's built-in ``DefaultEmbeddingFunction``
(all-MiniLM-L6-v2 from sentence-transformers) is used — no extra API key needed.
"""

from __future__ import annotations

import logging
from typing import List

import chromadb
from chromadb.utils import embedding_functions

from config import settings
from models import Chunk

log = logging.getLogger(__name__)

# Module-level client — shared across all service instances
_client: chromadb.ClientAPI | None = None


def _get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    return _client


class RAGService:
    """ChromaDB-backed vector store with per-session isolation."""

    def __init__(self):
        self._ef = embedding_functions.DefaultEmbeddingFunction()

    def _collection(self, session_id: str) -> chromadb.Collection:
        return _get_client().get_or_create_collection(
            name=f"session_{session_id}",
            embedding_function=self._ef,
            metadata={"hnsw:space": "cosine"},
        )

    # ── Write ─────────────────────────────────────────────────────────────────

    async def upsert_chunks(self, session_id: str, chunks: list[Chunk]) -> None:
        """Embed and store chunks.  Idempotent — safe to call multiple times."""
        if not chunks:
            return

        col = self._collection(session_id)
        ids = [f"{session_id}_{i}" for i in range(len(chunks))]
        documents = [c.text for c in chunks]
        metadatas = [
            {"file_path": c.file_path, "chunk_type": c.chunk_type, "language": c.language}
            for c in chunks
        ]

        # ChromaDB upsert is synchronous — runs fast enough in background tasks
        col.upsert(ids=ids, documents=documents, metadatas=metadatas)
        log.info("Upserted %d chunks into collection session_%s", len(chunks), session_id)

    # ── Read ──────────────────────────────────────────────────────────────────

    async def retrieve(
        self,
        session_id: str,
        query: str,
        k: int = 8,
        chunk_types: list[str] | None = None,
    ) -> list[str]:
        """
        Return the top-k most relevant chunk texts for ``query``.
        Optionally filter by ``chunk_type`` (e.g. only 'function' chunks).
        """
        col = self._collection(session_id)

        where: dict | None = None
        if chunk_types:
            where = {"chunk_type": {"$in": chunk_types}}

        results = col.query(
            query_texts=[query],
            n_results=min(k, col.count()),
            where=where,
        )
        docs: list[list[str]] = results.get("documents", [[]])
        return docs[0] if docs else []

    # ── Cleanup ───────────────────────────────────────────────────────────────

    async def clear_session(self, session_id: str) -> None:
        """Delete the ChromaDB collection for a session."""
        try:
            _get_client().delete_collection(f"session_{session_id}")
            log.info("Deleted collection for session %s", session_id)
        except Exception as exc:
            log.warning("Could not delete collection for session %s: %s", session_id, exc)
