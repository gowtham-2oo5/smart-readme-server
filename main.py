import asyncio
import logging
import logging.config
import sys
from functools import lru_cache
from pathlib import Path

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from models import BannerConfig, ProjectMetadata, ReadmeRequest, ReadmeResponse
from services.file_service import FileService
from services.readme_service import ReadmeService

# ---------------------------------------------------------------------------
# Logging — configure once at startup
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App & Dependencies
# ---------------------------------------------------------------------------

app = FastAPI(
    title="README Generator API",
    description="Generate comprehensive README files for GitHub repositories using Qwen 2.5 Coder 32B",
    version="2.0.0",
)

# CORS — allow frontend clients to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@lru_cache()
def get_readme_service() -> ReadmeService:
    """Dependency: singleton ReadmeService."""
    return ReadmeService()

@lru_cache()
def get_file_service() -> FileService:
    """Dependency: singleton FileService."""
    return FileService()

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    return {
        "message": "README Generator API — Powered by Qwen 2.5 Coder 32B via NVIDIA API",
        "version": "2.0.0",
        "ai_model": settings.ai_model,
        "features": {
            "professional_banners": "🎨 Animated typing banners with JetBrains Mono",
            "dark_themes": "🌙 Professional dark themes optimised for GitHub",
            "custom_fonts": "🔤 Multiple professional fonts available",
            "ai_generation": "🤖 AI-powered comprehensive README generation",
        },
        "endpoints": {
            "generate": "/generate-readme",
            "models": "/models",
            "health": "/health",
            "files": "/files",
            "banner_preview": "/banner-preview/{owner}/{repo}",
            "banner_options": "/banner-options",
        },
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "version": "2.0.0", "ai_model": settings.ai_model}

@app.get("/models")
async def get_models(readme_svc: ReadmeService = Depends(get_readme_service)):
    """List supported AI models."""
    return {
        "supported_models": readme_svc.get_supported_models(),
        "default_model": settings.ai_model,
    }

@app.post("/generate-readme", response_model=ReadmeResponse)
async def generate_readme(request: ReadmeRequest, readme_svc: ReadmeService = Depends(get_readme_service)):
    """Generate a README for a GitHub repository using Qwen 2.5 Coder 32B."""
    try:
        log.info("📥 Received request: %s/%s", request.owner_name, request.repo_name)

        if request.banner_config and request.banner_config.include_banner:
            log.info(
                "🎨 Banner config: style=%s  font=%s  theme=%s",
                request.banner_config.style,
                request.banner_config.font,
                request.banner_config.theme,
            )

        result = await readme_svc.generate_readme(
            owner=request.owner_name,
            repo=request.repo_name,
            banner_config=request.banner_config,
        )

        return ReadmeResponse(success=True, data=result)

    except Exception as exc:
        log.error("❌ Error generating README: %s", exc)
        # Returning 500 simplifies the client processing logic, instead of 200 with success=False implicitly
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating README: {str(exc)}"
        ) from exc


@app.get("/files")
async def list_generated_files(file_svc: FileService = Depends(get_file_service)):
    """List all generated README files."""
    try:
        files = file_svc.list_generated_readmes()
        return {"success": True, "files": files, "total_files": len(files)}
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@app.get("/files/{file_name}")
async def get_file_content(file_name: str, file_svc: FileService = Depends(get_file_service)):
    """Retrieve the content of a specific saved README file."""
    try:
        safe_name = Path(file_name).name  # prevent path traversal
        file_path = f"./generated_readmes/{safe_name}"
        content = file_svc.read_readme(file_path)
        file_info = file_svc.get_file_info(file_path)
        return {"success": True, "content": content, "file_info": file_info}
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"File '{file_name}' not found.")
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@app.delete("/files/{file_name}")
async def delete_file(file_name: str, file_svc: FileService = Depends(get_file_service)):
    """Delete a generated README file."""
    try:
        safe_name = Path(file_name).name  # prevent path traversal
        file_path = f"./generated_readmes/{safe_name}"
        if file_svc.delete_readme(file_path):
            return {"success": True, "message": f"File '{file_name}' deleted successfully."}
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"File '{file_name}' not found.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@app.get("/banner-preview/{owner}/{repo}")
async def preview_banner(
    owner: str,
    repo: str,
    font: str = "jetbrains",
    theme: str = "github_dark",
    style: str = "professional",
    readme_svc: ReadmeService = Depends(get_readme_service)
):
    """🎨 Preview dual professional banners for a repository."""
    try:
        log.info("🎨 Generating dual banner preview for %s/%s", owner, repo)

        # Gather repo data
        repo_info = readme_svc.github_service.get_repo_info(owner, repo)
        default_branch = await readme_svc.github_service.get_default_branch(owner, repo)
        repo_structure = await readme_svc.github_service.get_repo_structure(owner, repo, default_branch)
        source_files = await readme_svc.github_service.fetch_source_files(
            owner, repo, repo_structure, default_branch
        )

        # Analyse metadata with graceful fallback
        try:
            if source_files:
                metadata = readme_svc._analyze_project_metadata(source_files, repo_structure)
            else:
                raise ValueError("No source files found")
        except Exception as exc:
            log.warning("⚠️ Using fallback metadata: %s", exc)
            metadata = ProjectMetadata(
                primary_language="Python",
                project_type="api",
                tech_stack=["Python"],
                frameworks=[],
            )

        # Generate banner URLs
        try:
            header_banner_url, conclusion_banner_url = readme_svc.banner_service.generate_dual_banners(
                repo_info=repo_info,
                metadata=metadata,
                font=font,
                theme=theme,
                style=style,
            )
        except Exception as exc:
            log.error("❌ Banner generation failed: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Banner generation failed: {exc}")

        # Build preview HTML
        try:
            header_preview = readme_svc.banner_service.get_banner_preview_html(
                header_banner_url, f"Header — {style.title()} Capsule Banner"
            )
            conclusion_preview = readme_svc.banner_service.get_banner_preview_html(
                conclusion_banner_url, "Conclusion — Typing SVG Banner"
            )
        except Exception as exc:
            log.warning("⚠️ Preview HTML generation failed: %s", exc)
            header_preview = f'<img src="{header_banner_url}" alt="Header Banner">'
            conclusion_preview = f'<img src="{conclusion_banner_url}" alt="Conclusion Banner">'

        return {
            "success": True,
            "dual_banners": {
                "header": {
                    "url": header_banner_url,
                    "type": "Capsule Render",
                    "preview_html": header_preview,
                },
                "conclusion": {
                    "url": conclusion_banner_url,
                    "type": "Typing SVG",
                    "preview_html": conclusion_preview,
                },
            },
            "metadata": {
                "primary_language": metadata.primary_language,
                "tech_stack": metadata.tech_stack,
                "project_type": metadata.project_type,
            },
            "config": {"font": font, "theme": theme, "style": style},
        }

    except HTTPException:
        raise
    except Exception as exc:
        log.error("❌ Banner preview error: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@app.get("/banner-options")
async def get_banner_options(readme_svc: ReadmeService = Depends(get_readme_service)):
    """🎨 List all available banner configuration options."""
    try:
        return {
            "success": True,
            "options": {
                "fonts": readme_svc.banner_service.get_supported_fonts(),
                "themes": readme_svc.banner_service.get_supported_themes(),
                "styles": {
                    "professional": "Multi-line professional banner with tech stack",
                    "animated": "Single-line animated banner with neon effects",
                    "minimal": "Clean minimal banner with essential info",
                },
            },
            "defaults": {"font": "jetbrains", "theme": "github_dark", "style": "professional"},
        }
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
