"""
IngestionService
================
Fetches a GitHub repo via gitingest, splits it into semantic chunks,
embeds them into ChromaDB, and uses Qwen to identify core features.

Chunk types:
  config   — package.json, requirements.txt, pyproject.toml, etc.
  function — individual function definitions
  class    — class blocks
  doc      — README, docstrings, markdown files
  other    — everything else (imports, constants, loose code)
"""

from __future__ import annotations

import logging
import re
from typing import AsyncIterator, List

from gitingest import ingest

from models import Chunk
from services.ai_service import AIService
from services.rag_service import RAGService

log = logging.getLogger(__name__)

# ── extension → language label ──────────────────────────────────────────────
_LANG_MAP: dict[str, str] = {
    ".py": "python", ".js": "javascript", ".ts": "typescript",
    ".jsx": "javascript", ".tsx": "typescript", ".java": "java",
    ".go": "go", ".rs": "rust", ".rb": "ruby", ".php": "php",
    ".cpp": "cpp", ".c": "c", ".cs": "csharp", ".swift": "swift",
    ".kt": "kotlin", ".dart": "dart", ".md": "markdown",
    ".json": "json", ".yaml": "yaml", ".yml": "yaml", ".toml": "toml",
}

# ── config file basenames (kept as one chunk each) ──────────────────────────
_CONFIG_NAMES = {
    "package.json", "requirements.txt", "pyproject.toml", "setup.py",
    "cargo.toml", "go.mod", "pom.xml", "composer.json", "gemfile",
    "dockerfile", "docker-compose.yml", "docker-compose.yaml",
    "pubspec.yaml", "build.gradle", "androidmanifest.xml", ".env.example",
}

# ── max chars per chunk before we split further ─────────────────────────────
_MAX_CHUNK_CHARS = 1_200


class IngestionService:
    """Orchestrates repo ingestion → chunking → embedding → feature ID."""

    def __init__(self, ai_service: AIService, rag_service: RAGService):
        self._ai = ai_service
        self._rag = rag_service

    # ── Public API ────────────────────────────────────────────────────────────

    async def ingest_repo(
        self,
        owner: str,
        repo: str,
        session_id: str,
    ) -> AsyncIterator[str]:
        """
        Main entry point.  An async generator that yields progress strings and
        then a final JSON-serialisable summary dict.

        Callers should iterate and push each yielded string to the WebSocket
        as a ``progress`` event.
        """
        url = f"https://github.com/{owner}/{repo}"
        yield f"Starting ingestion for {owner}/{repo}…"

        # 1. Fetch via gitingest ────────────────────────────────────────────
        log.info("gitingest: fetching %s", url)
        try:
            summary, tree, content = ingest(url)
        except Exception as exc:
            raise RuntimeError(f"gitingest failed: {exc}") from exc

        yield "Repository fetched ✓"

        # 2. Split into file blocks ─────────────────────────────────────────
        blocks = _split_into_file_blocks(content)
        yield f"Found {len(blocks)} files to analyse"

        # 3. Chunk each file ────────────────────────────────────────────────
        all_chunks: list[Chunk] = []
        for i, (file_path, file_text) in enumerate(blocks):
            chunks = _chunk_file(file_path, file_text)
            all_chunks.extend(chunks)
            if (i + 1) % 10 == 0 or i == len(blocks) - 1:
                yield f"Chunked {i + 1}/{len(blocks)} files ({len(all_chunks)} chunks so far)"

        yield f"Chunking complete → {len(all_chunks)} total chunks"

        # 4. Embed into ChromaDB ────────────────────────────────────────────
        await self._rag.upsert_chunks(session_id, all_chunks)
        yield "Chunks embedded into vector store ✓"

        # 5. Identify features via Qwen ─────────────────────────────────────
        yield "Asking Qwen to identify core features…"
        features = await self._identify_features(all_chunks, owner, repo)
        yield f"__features_identified__:{','.join(features)}"   # sentinel

    # ── Feature identification ────────────────────────────────────────────────

    async def _identify_features(
        self,
        chunks: list[Chunk],
        owner: str,
        repo: str,
    ) -> list[str]:
        """Use Qwen to extract 5-8 core features from a representative sample."""
        # Take config + function/class chunks for context (≤ 6 000 chars)
        priority = [c for c in chunks if c.chunk_type in ("config", "function", "class")]
        sample = priority[:20]
        context = "\n\n".join(
            f"[{c.file_path} | {c.chunk_type}]\n{c.text[:300]}" for c in sample
        )

        prompt = (
            f"You are analysing the GitHub repository `{owner}/{repo}`.\n\n"
            f"Here is a representative sample of its code and config:\n\n"
            f"{context}\n\n"
            "List the 5-8 core features or capabilities of this project. "
            "Be concise — one line per feature. "
            "Reply ONLY with a newline-separated list, no numbering, no preamble."
        )

        raw = await self._ai.generate_readme(prompt)
        features = [
            line.strip().lstrip("-•*").strip()
            for line in raw.strip().splitlines()
            if line.strip()
        ]
        return features[:8]


# ── Chunking helpers (pure functions) ─────────────────────────────────────────

def _split_into_file_blocks(content: str) -> list[tuple[str, str]]:
    """
    gitingest separates files with a line of 48+ '=' chars followed by
    the file path.  This function splits on those boundaries.
    """
    pattern = re.compile(r"={40,}\nFile: (.+?)\n={40,}", re.MULTILINE)
    parts: list[tuple[str, str]] = []
    matches = list(pattern.finditer(content))
    for i, m in enumerate(matches):
        file_path = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        text = content[start:end].strip()
        if text:
            parts.append((file_path, text))
    return parts


def _chunk_file(file_path: str, text: str) -> list[Chunk]:
    """Split a single file's text into semantic chunks."""
    import os
    basename = os.path.basename(file_path).lower()
    ext = os.path.splitext(file_path)[1].lower()
    language = _LANG_MAP.get(ext, "other")

    # Config files → single chunk, no splitting
    if basename in _CONFIG_NAMES:
        return [Chunk(text=text[:_MAX_CHUNK_CHARS * 2], file_path=file_path,
                      chunk_type="config", language=language)]

    # Markdown / plain text → split by headings
    if ext in (".md", ".txt", ".rst"):
        return _split_doc(file_path, text, language)

    # Python → split by def / class
    if ext == ".py":
        return _split_python(file_path, text)

    # JS/TS → split by function/class keywords
    if ext in (".js", ".ts", ".jsx", ".tsx"):
        return _split_js(file_path, text, language)

    # Fallback → fixed-size with small overlap
    return _split_fixed(file_path, text, language)


def _split_python(file_path: str, text: str) -> list[Chunk]:
    """Split Python source by top-level def/class boundaries."""
    pattern = re.compile(r"^(def |class |async def )", re.MULTILINE)
    return _split_by_pattern(file_path, text, pattern, "python")


def _split_js(file_path: str, text: str, language: str) -> list[Chunk]:
    """Split JS/TS source by function/class boundaries."""
    pattern = re.compile(
        r"^(export |async )?(function |class |const \w+ = |const \w+ = async )",
        re.MULTILINE,
    )
    return _split_by_pattern(file_path, text, pattern, language)


def _split_by_pattern(
    file_path: str,
    text: str,
    pattern: re.Pattern,
    language: str,
) -> list[Chunk]:
    splits = [m.start() for m in pattern.finditer(text)]
    if not splits:
        return _split_fixed(file_path, text, language)

    chunks: list[Chunk] = []
    for i, start in enumerate(splits):
        end = splits[i + 1] if i + 1 < len(splits) else len(text)
        block = text[start:end].strip()
        if not block:
            continue
        ctype = "class" if block.startswith("class ") else "function"
        # If block is huge, split further
        for part in _fixed_split(block):
            chunks.append(Chunk(text=part, file_path=file_path,
                                chunk_type=ctype, language=language))
    return chunks or _split_fixed(file_path, text, language)


def _split_doc(file_path: str, text: str, language: str) -> list[Chunk]:
    """Split markdown/text by headings."""
    pattern = re.compile(r"^#{1,3} .+", re.MULTILINE)
    return _split_by_pattern(file_path, text, pattern, language) or \
           _split_fixed(file_path, text, language)


def _split_fixed(file_path: str, text: str, language: str) -> list[Chunk]:
    return [
        Chunk(text=part, file_path=file_path, chunk_type="other", language=language)
        for part in _fixed_split(text)
    ]


def _fixed_split(text: str, size: int = _MAX_CHUNK_CHARS, overlap: int = 120) -> list[str]:
    parts: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        parts.append(text[start:end])
        start = end - overlap if end < len(text) else end
    return [p for p in parts if p.strip()]
