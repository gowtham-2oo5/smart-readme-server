"""
RepoCache
=========
In-memory cache for ingestion results keyed by ``owner/repo``.

Stores chunks, features, and the commit SHA at ingestion time.
On subsequent requests for the same repo, compares the latest commit SHA
from GitHub — if unchanged, returns cached data instantly.

The cache also tracks which ChromaDB session already has embeddings for
a repo, so we can clone the collection instead of re-embedding.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

import httpx

from config import settings
from models import Chunk

log = logging.getLogger(__name__)


@dataclass
class CachedRepo:
    """Snapshot of a repo's ingestion results."""
    owner: str
    repo: str
    commit_sha: str
    chunks: list[Chunk]
    features: list[str]
    embedded_session_id: str | None = None  # session that has the ChromaDB collection
    cached_at: float = field(default_factory=time.time)


class RepoCache:
    """In-memory repo ingestion cache with SHA-based invalidation."""

    def __init__(self):
        self._cache: dict[str, CachedRepo] = {}  # key: "owner/repo"

    def _key(self, owner: str, repo: str) -> str:
        return f"{owner}/{repo}".lower()

    def get(self, owner: str, repo: str) -> CachedRepo | None:
        return self._cache.get(self._key(owner, repo))

    def put(
        self,
        owner: str,
        repo: str,
        commit_sha: str,
        chunks: list[Chunk],
        features: list[str],
        embedded_session_id: str | None = None,
    ) -> CachedRepo:
        entry = CachedRepo(
            owner=owner,
            repo=repo,
            commit_sha=commit_sha,
            chunks=chunks,
            features=features,
            embedded_session_id=embedded_session_id,
        )
        self._cache[self._key(owner, repo)] = entry
        log.info(
            "Cached ingestion for %s/%s (sha=%s, %d chunks, %d features)",
            owner, repo, commit_sha[:8], len(chunks), len(features),
        )
        return entry

    def invalidate(self, owner: str, repo: str) -> None:
        self._cache.pop(self._key(owner, repo), None)

    @property
    def size(self) -> int:
        return len(self._cache)


async def get_latest_commit_sha(owner: str, repo: str) -> str | None:
    """Fetch the latest commit SHA from the default branch via GitHub API.

    Returns None if the request fails (network error, rate limit, etc.)
    so callers can fall back to a full re-ingestion.
    """
    headers: dict[str, str] = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if settings.github_token:
        headers["Authorization"] = f"token {settings.github_token}"

    try:
        async with httpx.AsyncClient(headers=headers, timeout=15) as client:
            resp = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/commits",
                params={"per_page": 1},
            )
            if resp.status_code == 200:
                commits = resp.json()
                if commits:
                    return commits[0]["sha"]
    except Exception as exc:
        log.warning("Could not fetch latest commit SHA for %s/%s: %s", owner, repo, exc)

    return None


# Module-level singleton
repo_cache = RepoCache()
