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

    # ------------------------------------------------------------------
    # Shared retrieval pipeline
    # ------------------------------------------------------------------

    async def _retrieve_repo_context(self, owner: str, repo: str) -> Dict[str, Any]:
        """Shared retrieval pipeline — gitingest + metadata analysis.

        Returns a dict with keys:
            repo_info, default_branch, summary_str, tree_str,
            gitingest_content, source_files, metadata
        """
        repo_info = self.github_service.get_repo_info(owner, repo)
        default_branch = await self.github_service.get_default_branch(owner, repo)
        log.info("📋 Using branch: %s", default_branch)

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

        return {
            "repo_info": repo_info,
            "default_branch": default_branch,
            "summary_str": summary_str,
            "tree_str": tree_str,
            "gitingest_content": gitingest_content,
            "source_files": source_files,
            "metadata": metadata,
        }

    @staticmethod
    def _parse_gitingest_content(gitingest_content: str) -> Dict[str, str]:
        """Parse the flat gitingest blob into a {filepath: content} dict."""
        source_files: Dict[str, str] = {}
        for block in re.split(r"={48}\n[Ff][Ii][Ll][Ee]: ", gitingest_content):
            if not block.strip():
                continue
            parts = block.split("\n" + "=" * 48 + "\n", 1)
            if len(parts) == 2:
                file_path = parts[0].strip()
                file_body = parts[1].strip()
                source_files[file_path] = file_body[:2000]
        return source_files

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate_readme(
        self, owner: str, repo: str, banner_config: Optional[BannerConfig] = None, tone: str = "professional"
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
        summary_str: str, tree_str: str, gitingest_content: str, max_chars: int = 100_000
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
    ) -> str:
        """Construct the optimised AI prompt using advanced prompt engineering patterns."""

        # 1. System/Role Context
        system_context = (
            "You are an elite developer experience (DX) engineer, technical writer, and open-source maintainer. "
            f"Your documentation is globally recognized for being clean, visually stunning, scannable, perfectly accurate, and written in a **{tone}** tone. "
            "You expertly balance the needs of absolute beginners with those of senior engineers looking for deep architectural facts."
        )

        # 2. Design Constraints
        banners_section = """
### DESIGN CONSTRAINTS:
Do NOT include any external images, banners, or decorative SVGs. We want a clean, minimalist, highly professional look focused purely on the technical content.
"""

        # 3. Instruction & Constraints
        instructions = """
### CORE INSTRUCTIONS:
Read the provided source code files and extract the essential architectural patterns, features, and usage rules. 
Write a masterclass README.md tailored exactly to the project's complexity and tech stack.

### CRITICAL REQUIREMENTS:
1. **Audience-First**: Identify the CORE project purpose. Why does this exist? State it clearly in the first paragraph.
2. **Scannability**: Use clean markdown structure: H1 -> H2 -> H3. Use bolding for emphasis, but sparingly.
3. **No Fluff**: Do NOT pad the document with generic filler text or overly enthusiastic marketing speak. Be a confident, concise engineer.
4. **Accuracy First**: Only document features, dependencies, or installation steps that are explicitly verifiable in the provided code. If you guess, it breaks user trust. 
5. **Practical Examples**: Focus on the 80% use case. Do NOT write verbose troubleshoot sections for extreme edge cases.
6. **Code Blocks**: Always specify the language for code blocks (e.g. ````python`, ````bash`).
7. **No Output Wrapping**: Do NOT wrap your final README output in ```markdown ... ``` code blocks. Output raw markdown. Do NOT prepend "### README.md".
8. **Professional Header**: Since we are not using generic image banners, you MUST start the document with a beautifully formatted Markdown Title (`# Project Name`), a 1-sentence tagline, and a row of 4-6 shield.io styling badges representing the core tech stack exactly accurately.

### REASONING PROCESS (Chain of Thought):
Before generating the final README, please write a brief reasoning block where you identify:
1. The project's core value proposition.
2. The primary target audience.
3. The top 3 features to highlight.
4. Any complex installation/setup steps that need simplifying.
You MUST wrap this exact block in `<scratchpad>` and `</scratchpad>` XML tags. Do NOT use markdown headers like `### <scratchpad>`.

### REQUIRED STRUCTURE (After the scratchpad):
1. **Title & Tagline**: A single clear sentence explaining what the project is.
2. **Badges**: 4-6 badges showing the core tech stack exactly accurately.
3. **Overview**: Brief but compelling project overview.
4. **Key Features**: The top 3-5 features (as bullet points with brief explanations).
5. **Quick Start Guide**: Get developers running in under 3 minutes.
6. **Architecture**: A deep, highly technical breakdown of the system design. Do NOT write generic filler like "Built with Spring Boot and JPA". Instead, explain the actual core domain models, how data flows through the application, the structure of the API/Database layers, and any advanced architectural choices (e.g., WebSocket pipelines, JWT auth flows, design patterns used). Use bullet points for readability.
7. **License & Contributing**: Brief standard clauses.
"""
        
        # 4. Input Context
        input_data = f"""
### INPUT DATA:
**Project Name**: {project_name}
**Repository**: {github_url}
**Detected Primary Language**: {metadata.primary_language}

**EXISTING README.md** (Draw inspiration from this if useful, but adapt it to the new standards):
<existing_readme>
{existing_readme[:2_000] if existing_readme else "No existing README found"}
</existing_readme>

**PROJECT FILES**:
<source_code>
{file_contents}
</source_code>

Now, take a deep breath, write your `<scratchpad>`, and then generate the ultimate README.md.
"""

        # Assemble the full optimized prompt template
        return f"{system_context}\n\n{banners_section}\n\n{instructions}\n\n{input_data}"

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
            "express": "Express.js", "next": "Next.js",
        }

        for file_path, content in source_files.items():
            file_name = os.path.basename(file_path).lower()
            content_lower = content.lower()

            if file_name in ("requirements.txt", "pyproject.toml", "setup.py"):
                for keyword, label in python_markers.items():
                    if keyword in content_lower and label not in frameworks:
                        tech_stack.append(label)
                        frameworks.append(label)

            elif file_name == "package.json":
                for keyword, label in js_markers.items():
                    if keyword in content_lower and label not in frameworks:
                        tech_stack.append(label)
                        frameworks.append(label)

        if primary_language not in tech_stack:
            tech_stack.insert(0, primary_language)

        # --- Project type ---
        project_type = "library"
        entry_points = {"main.py", "app.py", "server.py"}
        if any(os.path.basename(f) in entry_points for f in source_files):
            project_type = (
                "api"
                if any(fw in frameworks for fw in ("FastAPI", "Flask", "Django"))
                else "cli_tool"
            )
        elif any(
            os.path.basename(f) in ("index.html", "app.js") for f in source_files
        ):
            project_type = "web_app"
        elif any(fw in frameworks for fw in ("React", "Vue.js", "Angular", "Next.js")):
            project_type = "web_app"

        return ProjectMetadata(
            primary_language=primary_language,
            project_type=project_type,
            tech_stack=tech_stack[:5],
            frameworks=frameworks[:3],
        )

    # ------------------------------------------------------------------
    # Private — content utilities
    # ------------------------------------------------------------------

    def _clean_readme_content(self, readme_content: str) -> str:
        """Strip the AI-appended <scratchpad> block, markdown fences, and legacy formatting."""
        content = readme_content.strip()

        # 1. Safely remove scratchpad block entirely
        if "<scratchpad>" in content:
            start = content.find("<scratchpad>")
            
            # Find the end of the scratchpad
            if "</scratchpad>" in content:
                end = content.find("</scratchpad>") + len("</scratchpad>")
            else:
                # Fallback: if AI forgot the closing tag, try to find the start of the README
                fallback_end = content.find("### README.md", start)
                if fallback_end == -1:
                    fallback_end = content.find("## README.md", start)
                if fallback_end == -1:
                    fallback_end = content.find("![Header]", start)
                if fallback_end == -1:  # Absolute worst case, just cut 500 chars (unlikely to hit)
                    fallback_end = min(start + 500, len(content))
                end = fallback_end

            # we also want to remove `### ` if it precedes the scratchpad
            pre_start = content.rfind("### ", 0, start)
            if pre_start != -1 and pre_start >= start - 15:
                start = pre_start
                
            content = content[:start] + content[end:]
            content = content.strip()

        # 2. Remove "### README.md" if AI hallucinated it out of habit
        if content.startswith("### README.md"):
            content = content[len("### README.md"):].strip()
        elif content.startswith("## README.md"):
            content = content[len("## README.md"):].strip()
        elif content.startswith("# README.md"):
            content = content[len("# README.md"):].strip()

        # 3. Strip global ```markdown ... ``` wrapper
        if content.startswith("```markdown") and content.endswith("```"):
            content = content[len("```markdown"):].strip()
            content = content[:-3].strip()

        # Legacy fallback if it still generates metadata
        if "---METADATA---" in content:
            content = content[: content.find("---METADATA---")].strip()
            
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
