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

import asyncio
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
    "application.yml", "application.yaml", "application.properties",
    "application-dev.yml", "application-prod.yml", "buildspec.yml",
}

# ── max chars per chunk before we split further ─────────────────────────────
# bge-large-en-v1.5 supports 512 tokens ≈ ~2000 chars.
# We target ~400 tokens ≈ 800 chars to stay safely within the limit
# and leave room for the embedding model's [CLS]/[SEP] overhead.
_MAX_CHUNK_CHARS = 800


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
        skip_embedding: bool = False,
    ) -> AsyncIterator[str]:
        """
        Main entry point.  An async generator that yields progress strings and
        then a final JSON-serialisable summary dict.

        Uses a SHA-based cache: if the repo hasn't changed since last ingestion,
        reuses cached chunks/features and only re-embeds into the new session's
        ChromaDB collection if needed.
        """
        from services.repo_cache import repo_cache, get_latest_commit_sha

        yield f"Starting ingestion for {owner}/{repo}…"

        # ── Check cache ────────────────────────────────────────────────────
        cached = repo_cache.get(owner, repo)
        latest_sha = await get_latest_commit_sha(owner, repo)

        if cached and latest_sha and cached.commit_sha == latest_sha:
            yield "Repository unchanged since last analysis — using cache ⚡"

            all_chunks = cached.chunks
            features = cached.features

            # Re-embed into this session's collection if needed
            if not skip_embedding:
                if cached.embedded_session_id:
                    # Copy embeddings from the cached session's collection
                    yield "Copying embeddings from cache…"
                    await self._clone_embeddings(
                        cached.embedded_session_id, session_id, all_chunks,
                    )
                else:
                    embed_chunks = _select_chunks_for_embedding(all_chunks, max_chunks=150)
                    yield f"Embedding {len(embed_chunks)} chunks…"
                    await self._rag.upsert_chunks(session_id, embed_chunks)

                yield "Embeddings ready ✓"
            else:
                yield "Skipping embedding (not needed for this content type)"

            yield f"__features_identified__:{','.join(features)}"
            return

        # ── Full ingestion (no cache or repo changed) ──────────────────────
        url = f"https://github.com/{owner}/{repo}"

        log.info("gitingest: fetching %s", url)
        try:
            summary, tree, content = await asyncio.to_thread(ingest, url)
        except Exception as exc:
            raise RuntimeError(f"gitingest failed: {exc}") from exc

        yield "Repository fetched ✓"

        # Split into file blocks
        blocks = _split_into_file_blocks(content)
        yield f"Found {len(blocks)} files to analyse"

        # Chunk each file
        all_chunks: list[Chunk] = []
        for i, (file_path, file_text) in enumerate(blocks):
            chunks = _chunk_file(file_path, file_text)
            all_chunks.extend(chunks)
            if (i + 1) % 10 == 0 or i == len(blocks) - 1:
                yield f"Chunked {i + 1}/{len(blocks)} files ({len(all_chunks)} chunks so far)"

        yield f"Chunking complete → {len(all_chunks)} total chunks"

        # Embed into ChromaDB
        embedded_session_id: str | None = None
        if skip_embedding:
            yield "Skipping embedding (not needed for this content type)"
        else:
            embed_chunks = _select_chunks_for_embedding(all_chunks, max_chunks=150)
            yield f"Embedding {len(embed_chunks)} representative chunks…"
            await self._rag.upsert_chunks(session_id, embed_chunks)
            embedded_session_id = session_id
            yield "Chunks embedded into vector store ✓"

        # Identify features via Qwen
        yield "Identifying core features…"
        features = await self._identify_features(all_chunks, owner, repo)

        # ── Store in cache ─────────────────────────────────────────────────
        if latest_sha:
            repo_cache.put(
                owner, repo,
                commit_sha=latest_sha,
                chunks=all_chunks,
                features=features,
                embedded_session_id=embedded_session_id,
            )

        yield f"__features_identified__:{','.join(features)}"


    # ── Feature identification ────────────────────────────────────────────────

    async def _identify_features(
        self,
        chunks: list[Chunk],
        owner: str,
        repo: str,
    ) -> list[str]:
        """Use structural signals + AI to extract core features."""
        import os

        # 1. Structural signals from file paths
        file_paths = [c.file_path for c in chunks]
        structural_hints = _extract_structural_hints(file_paths)

        # 2. Build a concise file name inventory grouped by directory
        dir_files: dict[str, list[str]] = {}
        for p in file_paths:
            d = os.path.dirname(p)
            base = os.path.basename(p)
            dir_files.setdefault(d, []).append(base)

        # Compact inventory: "controller/ → AuthController.java, AttendanceController.java, ..."
        inventory_lines: list[str] = []
        for d in sorted(dir_files):
            short_dir = "/".join(d.replace("\\", "/").split("/")[-2:]) or d
            names = ", ".join(sorted(dir_files[d])[:15])
            if len(dir_files[d]) > 15:
                names += f", ... (+{len(dir_files[d]) - 15} more)"
            inventory_lines.append(f"{short_dir}/ → {names}")
        inventory = "\n".join(inventory_lines)[:4000]

        # 3. Prioritize high-signal chunks with directory diversity
        priority = [c for c in chunks if c.chunk_type in ("config", "class")]
        priority += [c for c in chunks if c.chunk_type == "function" and c not in priority]

        seen_dirs: set[str] = set()
        sample: list[Chunk] = []
        for c in priority:
            d = os.path.dirname(c.file_path)
            is_new_dir = d not in seen_dirs
            if is_new_dir:
                seen_dirs.add(d)
            if is_new_dir or len(sample) < 30:
                sample.append(c)
            if len(sample) >= 40:
                break

        context = "\n\n".join(
            f"[{c.file_path} | {c.chunk_type}]\n{c.text[:600]}" for c in sample
        )

        prompt = (
            f"You are analysing the GitHub repository `{owner}/{repo}`.\n\n"
            f"## File inventory (every file in the project):\n{inventory}\n\n"
        )

        if structural_hints:
            prompt += f"## Structural signals:\n{chr(10).join(structural_hints)}\n\n"

        prompt += (
            f"## Code samples:\n{context}\n\n"
            "## CRITICAL RULES:\n"
            "- ONLY list features that are DIRECTLY EVIDENCED by the file names and code above\n"
            "- NEVER invent or assume features not shown (no Stripe, no Kafka, no Redis unless you SEE them)\n"
            "- If a file is named AttendanceController.java, that's evidence of attendance management\n"
            "- If there's no payment-related file, do NOT mention payments\n\n"
            "Based on the file inventory and code samples, list 8-12 core features.\n"
            "Be SPECIFIC to what this project actually does. Examples of good specificity:\n"
            "- 'Attendance tracking with batch marking and session management'\n"
            "- 'Faculty timetable scheduling with time slot templates'\n"
            "- 'JWT authentication with OTP verification'\n\n"
            "Reply ONLY with a newline-separated list, no numbering, no preamble."
        )

        raw = await self._ai.generate_readme(prompt)
        features = [
            line.strip().lstrip("-•*").strip()
            for line in raw.strip().splitlines()
            if line.strip() and len(line.strip()) > 3
        ]
        return features[:12]
    async def _clone_embeddings(
        self,
        source_session_id: str,
        target_session_id: str,
        chunks: list[Chunk],
    ) -> None:
        """Copy embeddings from a cached session's ChromaDB collection to a new one.

        ChromaDB doesn't support collection cloning, so we re-embed the chunks.
        But since the chunks are already in memory (from cache), this skips
        the expensive gitingest + chunking + feature ID steps.
        """
        embed_chunks = _select_chunks_for_embedding(chunks, max_chunks=150)
        await self._rag.upsert_chunks(target_session_id, embed_chunks)




# ── Chunking helpers (pure functions) ─────────────────────────────────────────

def _select_chunks_for_embedding(chunks: list[Chunk], max_chunks: int = 300) -> list[Chunk]:
    """Pick the most valuable chunks for RAG embedding, capped at max_chunks."""
    import os
    # Priority: config > class (annotated) > function > other
    priority = {"config": 0, "class": 1, "function": 2, "doc": 3, "other": 4}
    scored = sorted(chunks, key=lambda c: priority.get(c.chunk_type, 4))

    # Ensure directory diversity
    seen_dirs: dict[str, int] = {}
    selected: list[Chunk] = []
    for c in scored:
        d = os.path.dirname(c.file_path)
        count = seen_dirs.get(d, 0)
        if count < 10 or len(selected) < max_chunks // 2:
            selected.append(c)
            seen_dirs[d] = count + 1
        if len(selected) >= max_chunks:
            break
    return selected


def _extract_structural_hints(file_paths: list[str]) -> list[str]:
    """Extract feature hints from file/directory naming patterns."""
    import os
    hints: list[str] = []
    all_dirs = set()
    all_basenames = set()

    for p in file_paths:
        parts = p.lower().replace("\\", "/").split("/")
        all_dirs.update(parts[:-1])
        all_basenames.add(os.path.basename(p).lower())

    # Spring Boot / Java patterns
    spring_markers = {
        "controller": "REST API controllers",
        "service": "Business logic services",
        "repository": "Data access layer",
        "entity": "Database entities/models",
        "model": "Domain models/entities",
        "dto": "Data transfer objects",
        "config": "Configuration classes",
        "security": "Security/authentication",
        "filter": "Request filters/interceptors",
        "handler": "Event/exception handlers",
        "scheduler": "Scheduled tasks",
        "listener": "Event listeners",
        "middleware": "Middleware layer",
        "migration": "Database migrations",
        "seed": "Data seeding",
        "gateway": "API gateway",
        "interceptor": "Request interceptors",
        "websocket": "WebSocket real-time communication",
        "exception": "Custom exception handling",
    }

    for keyword, desc in spring_markers.items():
        matching = [d for d in all_dirs if keyword in d]
        if matching:
            hints.append(f"Found `{matching[0]}/` directory → {desc}")

    # Config file signals
    config_signals = {
        "application.yml": "Spring Boot application config",
        "application.properties": "Spring Boot application config",
        "docker-compose.yml": "Docker multi-container setup",
        "kafka": "Kafka messaging integration",
        "redis": "Redis caching",
        "elasticsearch": "Elasticsearch integration",
        "graphql": "GraphQL API",
        "grpc": "gRPC services",
        "swagger": "API documentation (Swagger/OpenAPI)",
        "openapi": "OpenAPI specification",
        "liquibase": "Liquibase database migrations",
        "flyway": "Flyway database migrations",
    }

    all_text = " ".join(all_dirs) + " " + " ".join(all_basenames)
    for keyword, desc in config_signals.items():
        if keyword in all_text:
            hints.append(f"Detected {desc}")

    return hints

def _split_into_file_blocks(content: str) -> list[tuple[str, str]]:
    """
    gitingest separates files with a line of 48+ '=' chars followed by
    the file path.  This function splits on those boundaries.
    """
    pattern = re.compile(r"={40,}\n(?:File|FILE): (.+?)\n={40,}", re.MULTILINE)
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

    # Java / Kotlin → split by class / method boundaries
    if ext in (".java", ".kt"):
        return _split_java(file_path, text, language)

    # Fallback → fixed-size with small overlap
    return _split_fixed(file_path, text, language)


def _split_python(file_path: str, text: str) -> list[Chunk]:
    """Split Python source by top-level def/class boundaries."""
    pattern = re.compile(r"^(def |class |async def )", re.MULTILINE)
    return _split_by_pattern(file_path, text, pattern, "python")


def _split_java(file_path: str, text: str, language: str) -> list[Chunk]:
    """Split Java/Kotlin source by class/method/annotation boundaries."""
    pattern = re.compile(
        r"^(\s*@\w+|\s*public |\s*private |\s*protected |\s*class |\s*interface |\s*enum |\s*abstract |\s*fun |\s*data class )",
        re.MULTILINE,
    )
    chunks = _split_by_pattern(file_path, text, pattern, language)
    # Tag chunks containing Spring/JPA annotations for better feature detection
    for c in chunks:
        annotations = re.findall(r"@(\w+)", c.text)
        spring_markers = {"RestController", "Controller", "Service", "Repository",
                          "Entity", "Configuration", "Component", "RequestMapping",
                          "GetMapping", "PostMapping", "PutMapping", "DeleteMapping",
                          "Autowired", "Bean", "EnableWebSecurity", "Scheduled",
                          "KafkaListener", "Cacheable", "Transactional"}
        if spring_markers & set(annotations):
            c.chunk_type = "class"  # promote so feature detection picks it up
    return chunks


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


def _fixed_split(text: str, size: int = _MAX_CHUNK_CHARS, overlap: int = 160) -> list[str]:
    """Split text into chunks, preferring sentence boundaries over hard cuts.

    Overlap is ~20% of chunk size to preserve context across boundaries.
    """
    if len(text) <= size:
        return [text] if text.strip() else []

    parts: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))

        # Try to break at a sentence boundary (. ! ? followed by space/newline)
        if end < len(text):
            # Search backwards from `end` for a sentence-ending punctuation
            search_region = text[start + size // 2 : end]  # only look in the back half
            for marker in ("\n\n", ".\n", ". ", "!\n", "! ", "?\n", "? "):
                last = search_region.rfind(marker)
                if last != -1:
                    end = start + size // 2 + last + len(marker)
                    break

        parts.append(text[start:end])
        start = end - overlap if end < len(text) else end

    return [p for p in parts if p.strip()]
