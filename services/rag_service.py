"""
RAGService
==========
ChromaDB-backed vector store with per-session isolation.

Uses BAAI/bge-small-en-v1.5 (384-dim, 512 token limit, Apache 2.0) for
embeddings — same training as bge-large but 33MB vs 1.34GB, fast on CPU.
Retrieval quality is driven by the cross-encoder reranker (ms-marco-MiniLM-L-6-v2)
which scores candidates after the initial vector search.
"""

from __future__ import annotations

import logging
from typing import List

import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import CrossEncoder

from config import settings
from models import Chunk

log = logging.getLogger(__name__)

# Module-level singletons
_client: chromadb.ClientAPI | None = None
_reranker: CrossEncoder | None = None

_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
_RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


def _get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    return _client


def _get_reranker() -> CrossEncoder:
    global _reranker
    if _reranker is None:
        log.info("Loading reranker model: %s", _RERANKER_MODEL)
        _reranker = CrossEncoder(_RERANKER_MODEL)
    return _reranker


class RAGService:
    """ChromaDB-backed vector store with per-session isolation."""

    def __init__(self):
        self._ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=_EMBEDDING_MODEL,
        )

    def _collection(self, session_id: str) -> chromadb.Collection:
        return _get_client().get_or_create_collection(
            name=f"session_{session_id}",
            embedding_function=self._ef,
            metadata={"hnsw:space": "cosine"},
        )

    # ── Write ─────────────────────────────────────────────────────────────────

    async def upsert_chunks(self, session_id: str, chunks: list[Chunk]) -> None:
        """Embed and store chunks in batches. Idempotent.

        Runs each batch in a thread to avoid blocking the async event loop
        (bge-large embedding on CPU is slow).
        """
        if not chunks:
            return

        import asyncio

        col = self._collection(session_id)
        batch_size = 50  # smaller batches to avoid long blocking periods

        for start in range(0, len(chunks), batch_size):
            batch = chunks[start:start + batch_size]
            ids = [f"{session_id}_{start + i}" for i in range(len(batch))]
            documents = [c.text for c in batch]
            metadatas = [
                {"file_path": c.file_path, "chunk_type": c.chunk_type, "language": c.language}
                for c in batch
            ]
            # Run in thread so the event loop stays responsive
            await asyncio.to_thread(col.upsert, ids=ids, documents=documents, metadatas=metadatas)

        log.info("Upserted %d chunks into collection session_%s", len(chunks), session_id)

    # ── Read ──────────────────────────────────────────────────────────────────

    async def retrieve(
        self,
        session_id: str,
        query: str,
        k: int = 8,
        chunk_types: list[str] | None = None,
        rerank: bool = True,
    ) -> list[str]:
        """
        Return the top-k most relevant chunk texts for ``query``.

        When ``rerank=True`` (default), fetches 3×k candidates from ChromaDB
        then reranks with a cross-encoder to pick the best k.

        All CPU-bound work (embedding query, cross-encoder scoring) runs in
        threads to keep the async event loop responsive.
        """
        import asyncio

        col = self._collection(session_id)
        count = col.count()
        if count == 0:
            return []

        where: dict | None = None
        if chunk_types:
            where = {"chunk_type": {"$in": chunk_types}}

        # Fetch more candidates when reranking
        fetch_k = min(k * 3, count) if rerank else min(k, count)

        # Run query in thread — embedding the query text is CPU-bound
        results = await asyncio.to_thread(
            col.query,
            query_texts=[query],
            n_results=fetch_k,
            where=where,
        )
        docs: list[list[str]] = results.get("documents", [[]])
        candidates = docs[0] if docs else []

        if not candidates:
            return []

        # Rerank with cross-encoder (CPU-bound, run in thread)
        if rerank and len(candidates) > k:
            candidates = await asyncio.to_thread(self._rerank, query, candidates, k)

        return candidates

    def _rerank(self, query: str, documents: list[str], k: int) -> list[str]:
        """Score each document against the query with a cross-encoder and return top-k."""
        reranker = _get_reranker()
        pairs = [[query, doc] for doc in documents]
        scores = reranker.predict(pairs)
        ranked = sorted(zip(scores, documents), key=lambda x: x[0], reverse=True)
        return [doc for _, doc in ranked[:k]]

    # ── Cleanup ───────────────────────────────────────────────────────────────

    async def clear_session(self, session_id: str) -> None:
        """Delete the ChromaDB collection for a session."""
        try:
            _get_client().delete_collection(f"session_{session_id}")
            log.info("Deleted collection for session %s", session_id)
        except Exception as exc:
            log.warning("Could not delete collection for session %s: %s", session_id, exc)
