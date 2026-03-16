import asyncio
import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional

from config import settings
from models import BannerConfig, ContentType, ProjectMetadata
from services.ai_service import AIService
from services.banner_service import BannerService
from services.file_service import FileService
from services.github_service import GitHubService
from services.prompt_templates import (
    build_article_prompt,
    build_linkedin_prompt,
    build_resume_prompt,
)

log = logging.getLogger(__name__)


class ReadmeService:
    """Orchestrates the full README generation pipeline."""

    def __init__(self):
        self.github_service = GitHubService()
        self.ai_service = AIService()
        self.file_service = FileService()
        self.banner_service = BannerService()
        self._gitingest_cache: Dict[str, Dict] = {}  # key: "owner/repo" → {sha, data}

    # ------------------------------------------------------------------
    # Shared retrieval pipeline
    # ------------------------------------------------------------------

    async def _retrieve_repo_context(self, owner: str, repo: str) -> Dict[str, Any]:
        """Shared retrieval pipeline — gitingest + metadata analysis.

        Caches gitingest results keyed by owner/repo with SHA-based invalidation.
        If the repo hasn't changed since last call, skips the expensive gitingest step.
        """
        from services.repo_cache import get_latest_commit_sha

        repo_info = self.github_service.get_repo_info(owner, repo)
        default_branch = await self.github_service.get_default_branch(owner, repo)
        log.info("📋 Using branch: %s", default_branch)

        # ── Check gitingest cache ──────────────────────────────────────────
        cache_key = f"{owner}/{repo}".lower()
        latest_sha = await get_latest_commit_sha(owner, repo)
        cached = self._gitingest_cache.get(cache_key)

        if cached and latest_sha and cached["sha"] == latest_sha:
            log.info("⚡ Using cached gitingest result for %s/%s", owner, repo)
            return {
                "repo_info": repo_info,
                "default_branch": default_branch,
                **cached["data"],
            }

        # ── Full gitingest ─────────────────────────────────────────────────
        log.info("📥 Ingesting repository using gitingest...")
        from gitingest import ingest

        url = f"https://github.com/{owner}/{repo}"

        try:
            summary_str, tree_str, gitingest_content = await asyncio.to_thread(
                ingest,
                url,
                exclude_patterns={
                    "test", "tests", "docs", "assets", "public",
                    ".idea", "node_modules", ".git", "migrations", "alembic",
                },
                token=settings.github_token,
            )
            log.info(
                "✅ Gitingest completed! Tree size: %d, Content size: %d",
                len(tree_str),
                len(gitingest_content),
            )
        except Exception as e:
            import traceback

            with open("gitingest_error.log", "w") as f:
                traceback.print_exc(file=f)
            log.error("❌ Gitingest failed: %r", e)
            raise ValueError(f"Failed to ingest repository: {repr(e)}")

        if not gitingest_content:
            raise ValueError("No analysable source files found in this repository.")

        source_files = self._parse_gitingest_content(gitingest_content)
        metadata = self._analyze_project_metadata(source_files, [])

        result_data = {
            "summary_str": summary_str,
            "tree_str": tree_str,
            "gitingest_content": gitingest_content,
            "source_files": source_files,
            "metadata": metadata,
        }

        # Store in cache
        if latest_sha:
            self._gitingest_cache[cache_key] = {"sha": latest_sha, "data": result_data}
            log.info("⚡ Cached gitingest result for %s/%s (sha=%s)", owner, repo, latest_sha[:8])

        return {
            "repo_info": repo_info,
            "default_branch": default_branch,
            **result_data,
        }


    # Files critical for metadata detection — allow more content
    _METADATA_FILES = frozenset({
        "pom.xml", "build.gradle", "build.gradle.kts",
        "package.json", "requirements.txt", "pyproject.toml",
        "setup.py", "pipfile", "cargo.toml", "go.mod", "go.sum",
        "application.yaml", "application.yml", "application.properties",
        ".env", ".env.example", "docker-compose.yml", "docker-compose.yaml",
    })

    @classmethod
    def _parse_gitingest_content(cls, gitingest_content: str) -> Dict[str, str]:
        """Parse the flat gitingest blob into a {filepath: content} dict.

        Dependency/config files get a higher truncation limit (8 000 chars)
        so framework detection doesn't miss markers buried deep in pom.xml etc.
        """
        source_files: Dict[str, str] = {}
        for block in re.split(r"={48}\n[Ff][Ii][Ll][Ee]: ", gitingest_content):
            if not block.strip():
                continue
            parts = block.split("\n" + "=" * 48 + "\n", 1)
            if len(parts) == 2:
                file_path = parts[0].strip()
                file_body = parts[1].strip()
                basename = os.path.basename(file_path).lower()
                limit = 8_000 if basename in cls._METADATA_FILES else 2_000
                source_files[file_path] = file_body[:limit]
        return source_files

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate_readme(
        self, owner: str, repo: str, banner_config: Optional[BannerConfig] = None, tone: str = "professional",
        user_preferences: str = "",
    ) -> Dict:
        """Generate a README for a GitHub repository using gitingest."""
        start_time = time.time()
        log.info("🚀 Starting README generation for %s/%s", owner, repo)

        # 1. Shared retrieval
        ctx = await self._retrieve_repo_context(owner, repo)
        repo_info = ctx["repo_info"]
        default_branch = ctx["default_branch"]
        metadata = ctx["metadata"]

        # 2. Generate dual banners (URLs only — no HTTP calls)
        header_banner_url: Optional[str] = None
        conclusion_banner_url: Optional[str] = None

        if banner_config and banner_config.include_banner:
            try:
                log.info("🎨 Generating dual banners…")
                header_banner_url, conclusion_banner_url = self.banner_service.generate_dual_banners(
                    repo_info=repo_info,
                    metadata=metadata,
                    font=banner_config.font,
                    theme=banner_config.theme,
                    style=banner_config.style,
                )
                log.info("✅ Dual banners generated successfully")
            except Exception as exc:
                log.warning("⚠️ Banner generation failed — continuing without banners: %s", exc)

        # 3. Generate README content via AI
        readme_content = await self._generate_readme_content(
            repo_info,
            ctx["summary_str"],
            ctx["tree_str"],
            ctx["gitingest_content"],
            metadata,
            header_banner_url,
            conclusion_banner_url,
            tone,
            user_preferences,
        )

        # 4. Strip the AI-appended metadata block and persist
        clean_content = self._clean_readme_content(readme_content)
        file_path = self.file_service.save_readme(owner, repo, clean_content)

        processing_time = round(time.time() - start_time, 2)
        log.info("✅ README generation complete in %ss", processing_time)

        return {
            "readme_content": clean_content,
            "readme_length": len(clean_content),
            "local_file_path": file_path,
            "processing_time": processing_time,
            "files_analyzed": len(ctx["source_files"]),
            "ai_model_used": settings.ai_model,
            "branch_used": default_branch,
            "metadata": metadata.__dict__,
            "repo_info": repo_info,
            "header_banner_url": header_banner_url if banner_config and banner_config.include_banner else None,
            "conclusion_banner_url": conclusion_banner_url if banner_config and banner_config.include_banner else None,
            "dual_banners_enabled": banner_config.include_banner if banner_config else False,
        }

    async def generate_content(
        self,
        owner: str,
        repo: str,
        content_type: ContentType,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Unified content generation dispatcher for LinkedIn, Article, and Resume."""
        start_time = time.time()
        log.info("🚀 Starting %s generation for %s/%s", content_type.value, owner, repo)

        # 1. Shared retrieval
        ctx = await self._retrieve_repo_context(owner, repo)
        repo_info = ctx["repo_info"]
        metadata: ProjectMetadata = ctx["metadata"]

        # 2. Prepare file contents for prompt
        file_contents = self._prepare_file_contents(
            ctx["summary_str"], ctx["tree_str"], ctx["gitingest_content"]
        )
        existing_readme = self._extract_existing_readme(ctx["gitingest_content"])

        # 3. Route to content-specific prompt builder
        project_name = repo_info["repo"]
        github_url = repo_info["url"]

        if content_type == ContentType.LINKEDIN:
            prompt = build_linkedin_prompt(
                project_name=project_name,
                github_url=github_url,
                file_contents=file_contents,
                existing_readme=existing_readme,
                metadata=metadata,
                tone=kwargs.get("tone", "thought_leader"),
                focus=kwargs.get("focus", "business_value"),
                user_preferences=kwargs.get("user_preferences", ""),
            )
        elif content_type == ContentType.ARTICLE:
            prompt = build_article_prompt(
                project_name=project_name,
                github_url=github_url,
                file_contents=file_contents,
                existing_readme=existing_readme,
                metadata=metadata,
                tone=kwargs.get("tone", "professional"),
                article_style=kwargs.get("article_style", "deep_dive"),
                target_length=kwargs.get("target_length", "medium"),
                user_preferences=kwargs.get("user_preferences", ""),
            )
        elif content_type == ContentType.RESUME:
            prompt = build_resume_prompt(
                project_name=project_name,
                github_url=github_url,
                file_contents=file_contents,
                existing_readme=existing_readme,
                metadata=metadata,
                role_target=kwargs.get("role_target", "Software Engineer"),
                seniority=kwargs.get("seniority", "mid"),
                num_bullets=kwargs.get("num_bullets", 5),
                include_metrics=kwargs.get("include_metrics", True),
                user_preferences=kwargs.get("user_preferences", ""),
            )
        else:
            raise ValueError(f"Unsupported content type: {content_type}")

        # 4. Generate via AI
        log.info("🤖 Sending %s prompt to AI (%d chars)…", content_type.value, len(prompt))
        try:
            raw_result = await self.ai_service.generate_readme(prompt)
        except Exception as exc:
            log.error("❌ AI generation failed for %s: %s", content_type.value, exc)
            raise ValueError(f"AI generation failed: {exc}")

        # 5. Clean output
        cleaned = self._clean_generated_content(raw_result, content_type)

        processing_time = round(time.time() - start_time, 2)
        log.info("✅ %s generation complete in %ss", content_type.value, processing_time)

        return {
            "content": cleaned,
            "content_type": content_type.value,
            "processing_time": processing_time,
            "files_analyzed": len(ctx["source_files"]),
            "ai_model_used": settings.ai_model,
            "metadata": metadata.__dict__,
            "repo_info": repo_info,
        }

    def get_supported_models(self) -> list[str]:
        return self.ai_service.get_supported_models()

    # ------------------------------------------------------------------
    # Private — shared helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _prepare_file_contents(
        summary_str: str, tree_str: str, gitingest_content: str, max_chars: int = 60_000
    ) -> str:
        """Format repo content for inclusion in a prompt."""
        truncated = gitingest_content[:max_chars]
        if len(gitingest_content) > max_chars:
            truncated += "\n\n... [TRUNCATED] ..."
        return (
            f"--- REPOSITORY SUMMARY ---\n{summary_str}\n\n"
            f"--- DIRECTORY TREE ---\n{tree_str}\n\n"
            f"--- FILE CONTENTS ---\n{truncated}"
        )

    @staticmethod
    def _extract_existing_readme(gitingest_content: str) -> str:
        """Pull out the existing README.md from gitingest content."""
        for block in re.split(r"={48}\n[Ff][Ii][Ll][Ee]: ", gitingest_content):
            if not block.strip():
                continue
            parts = block.split("\n" + "=" * 48 + "\n", 1)
            if len(parts) == 2:
                file_path, file_body = parts[0].strip(), parts[1].strip()
                if os.path.basename(file_path).lower() in ("readme.md", "readme.txt", "readme"):
                    return file_body[:2000]
        return ""

    def _clean_generated_content(self, raw: str, content_type: ContentType) -> str:
        """Content-type-aware cleaning of AI output."""
        content = raw.strip()

        if content_type == ContentType.RESUME:
            # Extract JSON from possible markdown wrapping
            if "```json" in content:
                start = content.find("```json") + len("```json")
                end = content.find("```", start)
                if end != -1:
                    content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                if end != -1:
                    content = content[start:end].strip()
            # Validate it's valid JSON
            try:
                json.loads(content)
            except json.JSONDecodeError:
                log.warning("⚠️ Resume output is not valid JSON, returning raw")
            return content

        # For LinkedIn and Article — strip markdown fences and scratchpad
        if "<scratchpad>" in content:
            start = content.find("<scratchpad>")
            end_tag = "</scratchpad>"
            if end_tag in content:
                end = content.find(end_tag) + len(end_tag)
            else:
                end = min(start + 500, len(content))
            content = content[:start] + content[end:]
            content = content.strip()

        if content.startswith("```markdown") and content.endswith("```"):
            content = content[len("```markdown"):].strip()
            content = content[:-3].strip()
        elif content.startswith("```") and content.endswith("```"):
            first_newline = content.find("\n")
            if first_newline != -1:
                content = content[first_newline + 1:].strip()
            content = content[:-3].strip()

        return content

    # ------------------------------------------------------------------
    # Private — README content generation
    # ------------------------------------------------------------------

    async def _generate_readme_content(
        self,
        repo_info: Dict,
        summary_str: str,
        tree_str: str,
        gitingest_content: str,
        metadata: ProjectMetadata,
        header_banner_url: Optional[str] = None,
        conclusion_banner_url: Optional[str] = None,
        tone: str = "professional",
        user_preferences: str = "",
    ) -> str:
        """Build the AI prompt and call the AI service."""
        project_name = repo_info["repo"]
        github_url = repo_info["url"]

        log.info("📝 Preparing content for AI prompt…")
        prep_start = time.time()

        existing_readme_content = self._extract_existing_readme(gitingest_content)
        file_contents = self._prepare_file_contents(summary_str, tree_str, gitingest_content)

        ai_prompt = self._build_prompt(
            project_name,
            github_url,
            file_contents,
            existing_readme_content,
            metadata,
            header_banner_url,
            conclusion_banner_url,
            tone,
            user_preferences,
        )

        log.info(
            "✅ Prompt ready in %.2fs  (%d chars)",
            time.time() - prep_start,
            len(ai_prompt),
        )

        try:
            log.info("🤖 Sending prompt to %s…", self.ai_service.get_supported_models()[0])
            gen_start = time.time()
            result = await self.ai_service.generate_readme(ai_prompt)
            log.info(
                "✅ README generated in %.2fs  (%d chars)",
                time.time() - gen_start,
                len(result),
            )
            return result
        except Exception as exc:
            log.error("❌ AI generation failed: %s", exc)
            return self._create_fallback_readme(
                project_name, github_url, header_banner_url, conclusion_banner_url
            )

    # ------------------------------------------------------------------
    # Private — prompt construction
    # ------------------------------------------------------------------

    def _extract_api_endpoints(self, file_contents: str) -> str:
        """Extract API endpoints as supplementary context (not the main content driver)."""
        endpoints = []
        # Python (FastAPI / Flask)
        py_patterns = [
            (r'@app\.post\(["\']([^"\']+)["\']', 'POST'),
            (r'@app\.get\(["\']([^"\']+)["\']', 'GET'),
            (r'@app\.put\(["\']([^"\']+)["\']', 'PUT'),
            (r'@app\.delete\(["\']([^"\']+)["\']', 'DELETE'),
            (r'@app\.patch\(["\']([^"\']+)["\']', 'PATCH'),
            (r'@app\.websocket\(["\']([^"\']+)["\']', 'WebSocket'),
            (r'@router\.post\(["\']([^"\']+)["\']', 'POST'),
            (r'@router\.get\(["\']([^"\']+)["\']', 'GET'),
            (r'@router\.put\(["\']([^"\']+)["\']', 'PUT'),
            (r'@router\.delete\(["\']([^"\']+)["\']', 'DELETE'),
        ]
        # Java (Spring Boot)
        java_patterns = [
            (r'@PostMapping\(["\']?([^"\')\s]+)', 'POST'),
            (r'@GetMapping\(["\']?([^"\')\s]+)', 'GET'),
            (r'@PutMapping\(["\']?([^"\')\s]+)', 'PUT'),
            (r'@DeleteMapping\(["\']?([^"\')\s]+)', 'DELETE'),
            (r'@PatchMapping\(["\']?([^"\')\s]+)', 'PATCH'),
            (r'@RequestMapping\(\s*value\s*=\s*["\']([^"\']+)["\'].*method\s*=\s*RequestMethod\.(\w+)', None),
        ]
        # Express.js / Node
        node_patterns = [
            (r'(?:app|router)\.post\(["\']([^"\']+)["\']', 'POST'),
            (r'(?:app|router)\.get\(["\']([^"\']+)["\']', 'GET'),
            (r'(?:app|router)\.put\(["\']([^"\']+)["\']', 'PUT'),
            (r'(?:app|router)\.delete\(["\']([^"\']+)["\']', 'DELETE'),
        ]

        for pattern, method in py_patterns + java_patterns + node_patterns:
            if method is None:
                # Special case: @RequestMapping with method in capture group 2
                for match in re.finditer(pattern, file_contents):
                    endpoints.append(f"  - {match.group(2)} {match.group(1)}")
            else:
                for match in re.findall(pattern, file_contents):
                    endpoints.append(f"  - {method} {match}")

        if endpoints:
            return (
                "**API endpoints found** (use these to build an API overview table in the README — "
                "do NOT list them verbatim as features):\n"
                + "\n".join(sorted(set(endpoints))) + "\n"
            )
        return ""

    def _build_prompt(
        self,
        project_name: str,
        github_url: str,
        file_contents: str,
        existing_readme: str,
        metadata: ProjectMetadata,
        header_banner_url: Optional[str] = None,
        conclusion_banner_url: Optional[str] = None,
        tone: str = "professional",
        user_preferences: str = "",
    ) -> str:
        """Construct the AI prompt using proper instruction hierarchy and self-verification."""

        # ── 1. System Context ──────────────────────────────────────────────
        system_context = (
            f"You are a senior developer-experience engineer writing a {tone} README. "
            "You write READMEs that developers actually read — clear, scannable, and "
            "immediately useful. You never invent features or pad with filler."
        )

        # ── 2. Task Instruction ────────────────────────────────────────────
        task = (
            "Write a complete README.md for the project described below. "
            "Output raw markdown only — no wrapping fences, no preamble, no commentary."
        )

        # ── 3. Few-Shot Example (condensed) ────────────────────────────────
        example = f"""
    ### EXAMPLE OF GOOD README OPENING:

    ```
    # TaskFlow

    A distributed task queue for Python that handles millions of jobs without breaking a sweat.

    ![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
    ![Redis](https://img.shields.io/badge/Redis-7.0+-DC382D?style=for-the-badge&logo=redis&logoColor=white)
    ![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
    ![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
    ```

    Note how badges use `style=for-the-badge` with `logo=<tech>&logoColor=white` for consistency.
    Badges go directly under the tagline — NOT in a separate "Badges" section.

    ### EXAMPLE OF GOOD FEATURES SECTION:

    ```
    ## Features

    - **Smart Retry Engine** — Automatically retries failed tasks with exponential backoff and circuit-breaker patterns. Configurable per-task with decorator syntax.
    - **Priority Queues** — Route urgent tasks to dedicated workers with configurable priority levels and fair scheduling.
    - **Real-Time Dashboard** — Monitor queue depth, worker health, and throughput via a built-in web UI with WebSocket updates.
    - **Dead Letter Queue** — Failed tasks are captured with full context for debugging, with one-click replay support.
    ```

    Note: Features use `- **Name** — Description` bullet format. NOT blockquotes (`>`). NOT API endpoints.

    ### EXAMPLE OF GOOD OVERVIEW (for a backend API project):

    ```
    ## Overview

    TaskFlow started as an internal tool to replace our team's brittle cron-based job runner. It's a Redis-backed distributed task queue designed for Python services that need reliable async job processing without the operational overhead of Celery.

    The core idea: define tasks as decorated functions, push them to named queues, and let workers handle the rest — retries, dead-lettering, and priority routing included. It's built for teams running 10-100 microservices that need a lightweight alternative to heavier queue systems.

    Under the hood, it uses Redis Streams for ordered delivery, Lua scripts for atomic operations, and a FastAPI dashboard for real-time monitoring.
    ```

    Note: The overview does NOT repeat the tagline. It tells the story — why it exists, who it's for, and what's interesting about the architecture.

    ### EXAMPLE OF API OVERVIEW TABLE (for backend/API projects):

    ```
    ## API Overview

    | Method | Endpoint | Description |
    |--------|----------|-------------|
    | POST | `/api/auth/login` | Authenticate user with credentials |
    | POST | `/api/auth/verify-otp` | Verify one-time password |
    | GET | `/api/users/profile` | Get current user profile |
    | PUT | `/api/users/:id` | Update user details |
    | GET | `/api/tasks` | List all tasks with pagination |
    ```
    ```

    Note: Only include this section for API/backend projects. Group by resource. Keep descriptions short.

    ### EXAMPLE OF GOOD CONTRIBUTING SECTION:

    ```
    ## Contributing

    Contributions are welcome and appreciated! Here's how to get started:

    1. Fork the repository
    2. Create a feature branch (`git checkout -b feature/amazing-feature`)
    3. Commit your changes (`git commit -m 'Add amazing feature'`)
    4. Push to the branch (`git push origin feature/amazing-feature`)
    5. Open a Pull Request

    Please make sure your code follows the existing style and includes appropriate tests.
    ```

    ### BADGE FORMAT REFERENCE:
    Use this exact format for shields.io badges:
    `![Label](https://img.shields.io/badge/Label-Value-HexColor?style=for-the-badge&logo=logoname&logoColor=white)`

    Common logos: python, javascript, typescript, react, nextdotjs, nodedotjs, fastapi, spring, docker, postgresql, mongodb, redis, tailwindcss, java, go, rust
    For the license badge, use: `![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)` (replace MIT with actual license)
    """

        # ── 4. Output Structure ────────────────────────────────────────────
        banner_block = ""
        if header_banner_url:
            banner_block += f"Start with: ![Banner]({header_banner_url})\n"
        if conclusion_banner_url:
            banner_block += f"End with: ![Footer]({conclusion_banner_url})\n"

        if not banner_block:
            banner_block = (
                "Start with `# Project Name` and a one-line tagline.\n"
                "Then place 3-5 shields.io badges (for-the-badge style) directly below the tagline — "
                "NOT in a separate section. No '## Badges' heading.\n"
            )

        # ── Detect if this is an API/backend project ──────────────────────
        is_api_project = metadata.project_type in ("api_server", "full_stack_app")

        api_section_instruction = ""
        if is_api_project:
            api_section_instruction = (
                "    Include an **API Overview** section with a markdown table of the main endpoints "
                "(Method | Endpoint | Description). Group by resource. Only include the most important "
                "routes — not every single endpoint. Place this AFTER Features and BEFORE Getting Started.\n"
            )

        structure = f"""
    ### OUTPUT STRUCTURE:
    {banner_block}
    1. **Title, Tagline & Badges** — Project name as H1, one-sentence tagline below it, then 3-5 shields.io badges on the next line. Badges are part of the header, NOT a separate section.
    2. **Overview** — 2-3 paragraphs. Do NOT repeat the tagline. Explain: why this project exists, who it's for, and what's architecturally interesting. Write like you're explaining to a smart dev over coffee.
    3. **Features** — 4-8 high-level capabilities as bullet points using `- **Feature Name** — description` format. Each bullet is a user-facing capability, NOT an API endpoint. Do NOT use blockquotes (`>`).
    {api_section_instruction}4. **Getting Started** — Numbered steps: clone → install → configure → run. Code blocks with language tags. Target: running in under 2 minutes.
    5. **Usage** — 1-2 practical examples of the most common workflow.
    6. **Tech Stack** — Clean table or short list of major technologies and their role.
    7. **Project Structure** — Top-level directory tree in a code block. Only folders that matter.
    8. **Contributing** — Include fork → branch → commit → push → PR steps. Make it welcoming and actionable.
    9. **License** — One line with the license name. If a LICENSE file exists, link to it.
    """

        # ── 5. Constraints ─────────────────────────────────────────────────
        constraints = """
    ### HARD RULES:
    - NEVER create a separate "## Badges" section. Badges go directly under the title/tagline.
    - NEVER list API endpoints as features. Features are user-facing capabilities.
    - NEVER use blockquotes (`>`) for feature items. Use bullet points: `- **Name** — description`.
    - NEVER start the Overview by repeating the tagline. The overview must add NEW information.
    - NEVER invent features, dependencies, or setup steps not in the source code.
    - NEVER wrap output in ```markdown``` fences.
    - NEVER include <scratchpad>, reasoning blocks, or meta-commentary.
    - ALL badges must use `style=for-the-badge` with proper `logo` and `logoColor=white` parameters.
    - The Contributing section MUST include fork/branch/commit/push/PR steps — not just "contributions welcome".
    - Keep total README between 300-600 lines.
    - All code blocks must specify the language.
    - If the project has frontend AND backend, explain both in Getting Started.
    """

        # ── 6. Self-Verification ───────────────────────────────────────────
        verification = """
    ### BEFORE YOU OUTPUT — VERIFY:
    1. Badges use valid shields.io URLs with `style=for-the-badge` and are NOT in a separate section.
    2. Every feature listed is backed by actual code in the source files.
    3. Features use `- **Name** — description` bullet format, NOT blockquotes (`>`).
    4. The Overview does NOT repeat the tagline — it adds context about why, who, and how.
    5. Every dependency in Getting Started appears in the actual dependency files.
    6. No API endpoints are listed as features (they belong in the API Overview table if applicable).
    7. The Contributing section has actionable steps (fork → branch → commit → push → PR).
    8. A developer could actually follow Getting Started and have it running.
    """

        # ── 7. Input Data ──────────────────────────────────────────────────
        endpoints_list = self._extract_api_endpoints(file_contents)

        input_data = f"""
    ### PROJECT CONTEXT:
    - **Name**: {project_name}
    - **Repository**: {github_url}
    - **Primary Language**: {metadata.primary_language}
    - **Tech Stack**: {', '.join(metadata.tech_stack) if metadata.tech_stack else 'See source code'}
    - **Project Type**: {metadata.project_type}

    {endpoints_list}

    **Existing README** (reference only — rewrite from scratch):
    <existing_readme>
    {existing_readme[:1_500] if existing_readme else "None"}
    </existing_readme>

    **Source Code**:
    <source_code>
    {file_contents}
    </source_code>

    {user_preferences}

    Now write the README.
    """

        return f"{system_context}\n\n{task}\n{example}\n{structure}\n{constraints}\n{verification}\n{input_data}"



    # ------------------------------------------------------------------
    # Private — metadata analysis (heuristic, no AI call)
    # ------------------------------------------------------------------

    def _analyze_project_metadata(
        self, source_files: Dict, repo_structure: List
    ) -> ProjectMetadata:
        """Detect language, framework, and project type from file contents."""

        # --- Language detection ---
        lang_counts: Dict[str, int] = {}
        ext_map = {
            ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript",
            ".ts": "TypeScript", ".tsx": "TypeScript", ".java": "Java",
            ".go": "Go", ".rs": "Rust", ".cpp": "C++", ".cc": "C++",
            ".cxx": "C++", ".kt": "Kotlin", ".swift": "Swift",
            ".dart": "Dart", ".rb": "Ruby", ".cs": "C#",
        }
        for file_path in source_files:
            ext = os.path.splitext(file_path)[1].lower()
            if lang := ext_map.get(ext):
                lang_counts[lang] = lang_counts.get(lang, 0) + 1

        primary_language = max(lang_counts, key=lang_counts.get) if lang_counts else "Unknown"

        # --- Framework / tech-stack detection ---
        tech_stack: List[str] = []
        frameworks: List[str] = []

        python_markers = {
            "fastapi": "FastAPI", "django": "Django",
            "flask": "Flask", "streamlit": "Streamlit",
        }
        js_markers = {
            "react": "React", "vue": "Vue.js", "angular": "Angular",
            "express": "Express.js", "next": "Next.js", "svelte": "Svelte",
            "nuxt": "Nuxt.js", "nest": "NestJS",
        }
        java_markers = {
            "spring-boot": "Spring Boot", "spring boot": "Spring Boot",
            "spring-web": "Spring Boot", "spring-data": "Spring Data",
            "spring-security": "Spring Security", "quarkus": "Quarkus",
            "micronaut": "Micronaut", "jakarta.servlet": "Jakarta EE",
        }
        go_markers = {
            "gin-gonic": "Gin", "gorilla/mux": "Gorilla Mux",
            "fiber": "Fiber", "echo": "Echo",
        }
        rust_markers = {
            "actix-web": "Actix Web", "rocket": "Rocket",
            "axum": "Axum", "warp": "Warp",
        }
        csharp_markers = {
            "microsoft.aspnetcore": "ASP.NET Core", "aspnetcore": "ASP.NET Core",
            "entityframeworkcore": "Entity Framework",
        }
        db_markers = {
            "mysql": "MySQL", "postgresql": "PostgreSQL", "postgres": "PostgreSQL",
            "mongodb": "MongoDB", "redis": "Redis", "sqlite": "SQLite",
            "dynamodb": "DynamoDB",
        }

        all_content_lower = ""

        for file_path, content in source_files.items():
            file_name = os.path.basename(file_path).lower()
            content_lower = content.lower()
            all_content_lower += content_lower + "\n"

            # Python deps
            if file_name in ("requirements.txt", "pyproject.toml", "setup.py", "pipfile"):
                for keyword, label in python_markers.items():
                    if keyword in content_lower and label not in frameworks:
                        tech_stack.append(label)
                        frameworks.append(label)

            # JS/TS deps
            elif file_name == "package.json":
                for keyword, label in js_markers.items():
                    if keyword in content_lower and label not in frameworks:
                        tech_stack.append(label)
                        frameworks.append(label)

            # Java deps (pom.xml, build.gradle)
            elif file_name in ("pom.xml", "build.gradle", "build.gradle.kts"):
                for keyword, label in java_markers.items():
                    if keyword in content_lower and label not in frameworks:
                        tech_stack.append(label)
                        frameworks.append(label)

            # Java source files — detect frameworks from annotations
            elif file_path.endswith(".java"):
                java_annotation_markers = {
                    "@springbootapplication": "Spring Boot",
                    "import org.springframework": "Spring Boot",
                    "@restcontroller": "Spring Boot",
                    "@enablewebsocket": "Spring WebSocket",
                    "spring-security": "Spring Security",
                    "springsecurity": "Spring Security",
                    "@enablecaching": "Spring Cache",
                }
                for keyword, label in java_annotation_markers.items():
                    if keyword in content_lower and label not in frameworks:
                        tech_stack.append(label)
                        frameworks.append(label)

            # Go deps
            elif file_name in ("go.mod", "go.sum"):
                for keyword, label in go_markers.items():
                    if keyword in content_lower and label not in frameworks:
                        tech_stack.append(label)
                        frameworks.append(label)

            # Rust deps
            elif file_name == "cargo.toml":
                for keyword, label in rust_markers.items():
                    if keyword in content_lower and label not in frameworks:
                        tech_stack.append(label)
                        frameworks.append(label)

            # C# deps
            elif file_name.endswith(".csproj") or file_name.endswith(".sln"):
                for keyword, label in csharp_markers.items():
                    if keyword in content_lower and label not in frameworks:
                        tech_stack.append(label)
                        frameworks.append(label)

            # DB detection from config/env files
            if file_name in ("application.yaml", "application.yml", "application.properties",
                             ".env", ".env.example", "docker-compose.yml", "docker-compose.yaml",
                             "requirements.txt", "pom.xml", "build.gradle", "package.json"):
                for keyword, label in db_markers.items():
                    if keyword in content_lower and label not in tech_stack:
                        tech_stack.append(label)

        # Docker detection
        if any(os.path.basename(f).lower() in ("dockerfile", "docker-compose.yml", "docker-compose.yaml")
               for f in source_files):
            if "Docker" not in tech_stack:
                tech_stack.append("Docker")

        if primary_language not in tech_stack:
            tech_stack.insert(0, primary_language)

        # --- Project type detection (comprehensive) ---
        project_type = "library"

        # Python entry points
        py_entry_points = {"main.py", "app.py", "server.py", "manage.py", "wsgi.py", "asgi.py"}
        has_py_entry = any(os.path.basename(f) in py_entry_points for f in source_files)

        # Java/Spring Boot detection — check all content for annotations
        has_java_app = (
            "springbootapplication" in all_content_lower
            or "@springbootapplication" in all_content_lower
            or "import org.springframework.boot" in all_content_lower
        )
        has_java_main = any(
            "public static void main" in source_files.get(f, "")
            for f in source_files if f.endswith(".java")
        )

        # Go entry points
        has_go_main = any(
            os.path.basename(f) == "main.go" for f in source_files
        )

        # Rust entry points
        has_rust_main = any(
            f.endswith("main.rs") for f in source_files
        )

        # Web framework indicators
        web_frameworks = {"FastAPI", "Flask", "Django", "Spring Boot", "Express.js",
                          "NestJS", "Gin", "Fiber", "Echo", "Actix Web", "Rocket",
                          "Axum", "ASP.NET Core", "Quarkus", "Micronaut"}
        has_web_framework = bool(web_frameworks & set(frameworks))

        # Frontend frameworks
        frontend_frameworks = {"React", "Vue.js", "Angular", "Next.js", "Svelte", "Nuxt.js"}
        has_frontend = bool(frontend_frameworks & set(frameworks))

        # REST controller annotations (Java)
        has_rest_controllers = (
            "@restcontroller" in all_content_lower
            or "@requestmapping" in all_content_lower
            or "@getmapping" in all_content_lower
            or "@postmapping" in all_content_lower
        )

        # Determine project type
        if has_web_framework or has_rest_controllers:
            if has_frontend:
                project_type = "full_stack_app"
            else:
                project_type = "api_server"
        elif has_frontend:
            project_type = "web_app"
        elif has_java_app or has_java_main:
            # If we detected Spring Boot annotations but it wasn't in frameworks yet
            if has_java_app and "Spring Boot" not in frameworks:
                frameworks.append("Spring Boot")
                tech_stack.append("Spring Boot")
            project_type = "api_server" if (has_rest_controllers or has_java_app) else "application"
        elif has_py_entry:
            project_type = "cli_tool"
        elif has_go_main or has_rust_main:
            project_type = "application"
        elif any(os.path.basename(f) in ("index.html", "app.js") for f in source_files):
            project_type = "web_app"

        return ProjectMetadata(
            primary_language=primary_language,
            project_type=project_type,
            tech_stack=tech_stack[:8],
            frameworks=frameworks[:5],
        )

    # ------------------------------------------------------------------
    # Private — content utilities
    # ------------------------------------------------------------------

    def _clean_readme_content(self, readme_content: str) -> str:
        """Strip any AI artifacts: scratchpad blocks, markdown fences, metadata."""
        content = readme_content.strip()

        # Remove scratchpad if AI still generates one despite instructions
        if "<scratchpad>" in content:
            start = content.find("<scratchpad>")
            if "</scratchpad>" in content:
                end = content.find("</scratchpad>") + len("</scratchpad>")
            else:
                end = min(start + 500, len(content))
            content = content[:start] + content[end:]
            content = content.strip()

        # Remove "### README.md" / "## README.md" header if hallucinated
        for prefix in ("### README.md", "## README.md", "# README.md"):
            if content.startswith(prefix):
                content = content[len(prefix):].strip()
                break

        # Strip global ```markdown ... ``` wrapper
        if content.startswith("```markdown") and content.endswith("```"):
            content = content[len("```markdown"):].strip()
            content = content[:-3].strip()
        elif content.startswith("```") and content.endswith("```"):
            first_nl = content.find("\n")
            if first_nl != -1:
                content = content[first_nl + 1:].strip()
            content = content[:-3].strip()

        # Legacy metadata block
        if "---METADATA---" in content:
            content = content[:content.find("---METADATA---")].strip()

        return content


    def _create_fallback_readme(
        self,
        repo_name: str,
        repo_url: str,
        header_banner_url: Optional[str] = None,
        conclusion_banner_url: Optional[str] = None,
    ) -> str:
        """Minimal README used when AI generation is unavailable."""
        header = f"![Header]({header_banner_url})\n\n" if header_banner_url else ""
        conclusion = f"\n\n![Conclusion]({conclusion_banner_url})" if conclusion_banner_url else ""

        return f"""{header}# {repo_name}

A project hosted at {repo_url}

## About

This project is currently being analysed. Please check back later for a comprehensive README.

## Quick Start

```bash
git clone {repo_url}
cd {repo_name}
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

Please check the repository for licence information.{conclusion}
"""
