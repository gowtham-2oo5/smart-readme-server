import asyncio
import base64
import logging
import os
from typing import Dict, List, Optional

import httpx

from config import settings

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GITHUB_API = "https://api.github.com"

# Critical config/manifest files — fetched without truncation
CRITICAL_FILES: set[str] = {
    "build.gradle",
    "app/build.gradle",
    "package.json",
    "pubspec.yaml",
    "AndroidManifest.xml",
    "Info.plist",
    "Podfile",
    "requirements.txt",
    "pom.xml",
    "Cargo.toml",
    "go.mod",
}

# These are fetched first (before generic code files)
PRIORITY_FILES: set[str] = {
    "package.json", "requirements.txt", "Cargo.toml", "go.mod", "pom.xml",
    "composer.json", "Gemfile", "setup.py", "pyproject.toml", "Dockerfile",
    "docker-compose.yml", "README.md", "README.txt", "README",
    "AndroidManifest.xml", "build.gradle", "app/build.gradle",
    "gradle.properties", "settings.gradle", "proguard-rules.pro",
    "Info.plist", "Podfile", "Podfile.lock", "project.pbxproj",
    "AppDelegate.swift", "AppDelegate.m", "SceneDelegate.swift",
    "pubspec.yaml", "pubspec.lock", "analysis_options.yaml",
    "lib/main.dart", "android/app/build.gradle", "ios/Runner/Info.plist",
}

CODE_EXTENSIONS: set[str] = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs",
    ".php", ".rb", ".cpp", ".c", ".h", ".cs", ".swift", ".kt",
    ".dart", ".m", ".mm", ".scala", ".clj", ".ex", ".exs",
    ".html", ".css",
}

# Directories to skip entirely to save tokens
SKIP_DIRS: set[str] = {
    ".git", "node_modules", "vendor", "__pycache__",
    ".next", "dist", "build", ".venv", "venv", "pods",
    ".flutter-plugins", ".dart_tool", "test", "tests",
    "spec", "docs", "assets", "public", ".idea", ".vscode",
    "migrations", "alembic"
}

# Keywords indicating a file likely contains core business logic or routing
HIGH_VALUE_MARKERS: List[str] = [
    "controller", "service", "route", "api", "app", 
    "main", "index", "config", "handler", "manager",
    "server", "core"
]

MAX_FILES = 45
TRUNCATE_LIMIT = 3_000


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class GitHubService:
    """Async GitHub REST API client using httpx."""

    def __init__(self):
        self._headers: Dict[str, str] = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if settings.github_token:
            self._headers["Authorization"] = f"token {settings.github_token}"

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def get_repo_info(self, owner: str, repo: str) -> Dict[str, str]:
        """Returns basic repo metadata (no network call needed)."""
        return {
            "owner": owner,
            "repo": repo,
            "url": f"https://github.com/{owner}/{repo}",
        }

    async def get_default_branch(self, owner: str, repo: str) -> str:
        try:
            async with httpx.AsyncClient(headers=self._headers, timeout=30) as client:
                resp = await client.get(f"{GITHUB_API}/repos/{owner}/{repo}")
                self._raise_for_rate_limit(resp)
                resp.raise_for_status()
                return resp.json().get("default_branch", "main")
        except httpx.HTTPStatusError as exc:
            log.error("HTTP error fetching default branch: %s", exc)
        except Exception as exc:
            log.error("Unexpected error fetching default branch: %s", exc)
        return "main"

    async def get_repo_structure(self, owner: str, repo: str, branch: str) -> List[Dict]:
        try:
            async with httpx.AsyncClient(headers=self._headers, timeout=30) as client:
                resp = await client.get(
                    f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
                )
                self._raise_for_rate_limit(resp)
                resp.raise_for_status()
                return resp.json().get("tree", [])
        except httpx.HTTPStatusError as exc:
            log.error("HTTP error fetching repo structure: %s", exc)
        except Exception as exc:
            log.error("Unexpected error fetching repo structure: %s", exc)
        return []

    async def fetch_source_files(
        self,
        owner: str,
        repo: str,
        repo_structure: List[Dict],
        branch: str,
    ) -> Dict[str, str]:
        """Fetch up to MAX_FILES source files concurrently."""
        log.info("🔍 Selecting files to fetch…")
        priority: List[str] = []
        high_value: List[str] = []
        secondary: List[str] = []

        # Convert PRIORITY_FILES to lower for case-insensitive matching
        priority_files_lower = {f.lower() for f in PRIORITY_FILES}

        for item in repo_structure:
            path = item.get("path", "")
            if item.get("type") == "tree":
                continue  # skip directory entries
                
            path_lower = path.lower()
            name_lower = os.path.basename(path_lower)

            # Check if any path segment matches a skipped directory exactly
            path_segments = set(path_lower.split('/'))
            if any(skip in path_segments for skip in SKIP_DIRS):
                continue

            if name_lower in priority_files_lower or path in PRIORITY_FILES:
                priority.append(path)
            elif any(path_lower.endswith(ext) for ext in CODE_EXTENSIONS):
                # Determine if it's a high-value core file
                if any(marker in name_lower for marker in HIGH_VALUE_MARKERS):
                    high_value.append(path)
                else:
                    secondary.append(path)

        # Assemble files to fetch, with priority -> high_value -> secondary
        files_to_fetch = (priority + high_value + secondary)[:MAX_FILES]
        log.info(
            "Fetching %d files (Priority: %d, High-Value: %d, Secondary: %d)",
            len(files_to_fetch), len(priority), len(high_value), len(secondary)
        )

        async with httpx.AsyncClient(headers=self._headers, timeout=30) as client:
            tasks = [
                self._fetch_single_file(client, owner, repo, fp, branch)
                for fp in files_to_fetch
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        source_files: Dict[str, str] = {}
        for file_path, result in zip(files_to_fetch, results):
            if isinstance(result, Exception) or result is None:
                continue
            content: str = result
            is_critical = any(c in file_path for c in CRITICAL_FILES)
            if is_critical:
                source_files[file_path] = content
                log.info("✅ Fetched (full):     %s  (%d chars)", file_path, len(content))
            else:
                source_files[file_path] = content[:TRUNCATE_LIMIT]
                log.info("✅ Fetched (truncated): %s  (%d chars)", file_path, min(len(content), TRUNCATE_LIMIT))

        log.info("Total files fetched: %d", len(source_files))
        return source_files

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _fetch_single_file(
        self,
        client: httpx.AsyncClient,
        owner: str,
        repo: str,
        file_path: str,
        branch: str,
    ) -> Optional[str]:
        try:
            resp = await client.get(
                f"{GITHUB_API}/repos/{owner}/{repo}/contents/{file_path}?ref={branch}"
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("content") and data.get("size", 0) < 100_000:
                    return base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
        except Exception as exc:
            log.warning("Could not fetch %s: %s", file_path, exc)
        return None

    @staticmethod
    def _raise_for_rate_limit(response: httpx.Response) -> None:
        if response.status_code in (403, 429):
            reset = response.headers.get("X-RateLimit-Reset", "unknown")
            raise httpx.HTTPStatusError(
                f"GitHub rate limit hit (resets at {reset}). "
                "Set GITHUB_TOKEN in .env to increase your limit.",
                request=response.request,
                response=response,
            )
