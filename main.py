import asyncio
import logging
import logging.config
import sys
import uuid
from functools import lru_cache
from pathlib import Path

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from models import (
    ArticleRequest,
    ArticleSessionState,
    ArticleStartRequest,
    ArticleStartResponse,
    BannerConfig,
    ContentResponse,
    ContentType,
    LinkedInRequest,
    ProjectMetadata,
    ReadmeRequest,
    ReadmeResponse,
    ResumeRequest,
    SessionStartRequest,
    WSMessageIn,
)
from services.ai_service import AIService
from services.article_builder import ArticleBuilder
from services.article_session import ArticleSession
from services.content_session import ContentSession
from services.file_service import FileService
from services.gemini_service import GeminiService
from services.ingestion_service import IngestionService
from services.rag_service import RAGService
from services.readme_service import ReadmeService
from services.websocket_manager import manager as ws_manager

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
    description=f"Generate comprehensive README files for GitHub repositories using AI ({settings.ai_model})",
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
        "message": f"README Generator API — Powered by {settings.ai_model} via NVIDIA API",
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
            "linkedin": "/generate-linkedin",
            "article": "/generate-article",
            "article_chat_start": "POST /article/start",
            "article_chat_ws": "WS /ws/article/{session_id}",
            "resume": "/generate-resume-points",
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
    """Generate a README for a GitHub repository using the configured AI model."""
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
            tone=request.tone,
        )

        return ReadmeResponse(success=True, data=result)

    except Exception as exc:
        log.error("❌ Error generating README: %s", exc)
        # Returning 500 simplifies the client processing logic, instead of 200 with success=False implicitly
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating README: {str(exc)}"
        ) from exc


@app.post("/generate-linkedin", response_model=ContentResponse)
async def generate_linkedin(
    request: LinkedInRequest,
    readme_svc: ReadmeService = Depends(get_readme_service),
):
    """Generate a LinkedIn announcement post for a GitHub repository."""
    try:
        log.info("📥 LinkedIn request: %s/%s", request.owner_name, request.repo_name)

        result = await readme_svc.generate_content(
            owner=request.owner_name,
            repo=request.repo_name,
            content_type=ContentType.LINKEDIN,
            tone=request.tone.value,
            focus=request.focus.value,
        )

        return ContentResponse(
            success=True,
            content_type=ContentType.LINKEDIN,
            content=result["content"],
            data=result,
        )

    except Exception as exc:
        log.error("❌ Error generating LinkedIn post: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating LinkedIn post: {str(exc)}",
        ) from exc


@app.post("/generate-article", response_model=ContentResponse)
async def generate_article(
    request: ArticleRequest,
    readme_svc: ReadmeService = Depends(get_readme_service),
):
    """Generate a technical article about a GitHub repository."""
    try:
        log.info("📥 Article request: %s/%s", request.owner_name, request.repo_name)

        result = await readme_svc.generate_content(
            owner=request.owner_name,
            repo=request.repo_name,
            content_type=ContentType.ARTICLE,
            tone=request.tone,
            article_style=request.article_style.value,
            target_length=request.target_length.value,
        )

        return ContentResponse(
            success=True,
            content_type=ContentType.ARTICLE,
            content=result["content"],
            data=result,
        )

    except Exception as exc:
        log.error("❌ Error generating article: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating article: {str(exc)}",
        ) from exc


@app.post("/generate-resume-points", response_model=ContentResponse)
async def generate_resume_points(
    request: ResumeRequest,
    readme_svc: ReadmeService = Depends(get_readme_service),
):
    """Generate resume bullet points and project description for a GitHub repository."""
    try:
        log.info("📥 Resume request: %s/%s (target: %s)", request.owner_name, request.repo_name, request.role_target)

        result = await readme_svc.generate_content(
            owner=request.owner_name,
            repo=request.repo_name,
            content_type=ContentType.RESUME,
            role_target=request.role_target,
            seniority=request.seniority,
            num_bullets=request.num_bullets,
            include_metrics=request.include_metrics,
        )

        return ContentResponse(
            success=True,
            content_type=ContentType.RESUME,
            content=result["content"],
            data=result,
        )

    except Exception as exc:
        log.error("❌ Error generating resume points: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating resume points: {str(exc)}",
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


# ---------------------------------------------------------------------------
# Chat-Based Article Generator — Session Store + Endpoints
# ---------------------------------------------------------------------------

# In-memory session store — maps session_id → ArticleSession
_sessions: dict[str, ArticleSession] = {}


@lru_cache()
def _get_ai_service() -> AIService:
    return AIService()


@lru_cache()
def _get_rag_service() -> RAGService:
    return RAGService()


@lru_cache()
def _get_gemini_service() -> GeminiService:
    return GeminiService()


@lru_cache()
def _get_ingestion_service() -> IngestionService:
    return IngestionService(
        ai_service=_get_ai_service(),
        rag_service=_get_rag_service(),
    )


@lru_cache()
def _get_article_builder() -> ArticleBuilder:
    return ArticleBuilder(rag_service=_get_rag_service())


@app.post("/article/start", response_model=ArticleStartResponse)
async def article_start(request: ArticleStartRequest, background_tasks: BackgroundTasks):
    """
    Kick off a chat-based article generation session.

    Returns a ``session_id`` immediately.  Connect to
    ``WS /ws/article/{session_id}`` to receive progress and continue the
    conversation.
    """
    session_id = str(uuid.uuid4())
    session = ArticleSession(
        session_id=session_id,
        owner=request.owner_name,
        repo=request.repo_name,
    )
    _sessions[session_id] = session
    log.info("🆕 Article session %s created for %s/%s", session_id, request.owner_name, request.repo_name)

    # Kick off ingestion in the background so we can return the session_id
    background_tasks.add_task(
        _run_ingestion,
        session_id=session_id,
        owner=request.owner_name,
        repo=request.repo_name,
    )

    return ArticleStartResponse(
        session_id=session_id,
        status=ArticleSessionState.INGESTING,
        message=f"Session started. Connect to WS /ws/article/{session_id} to begin.",
    )


async def _run_ingestion(session_id: str, owner: str, repo: str) -> None:
    """Background task: ingest repo, embed chunks, identify features."""
    session = _sessions.get(session_id)
    if session is None:
        return

    ingestion_svc = _get_ingestion_service()

    try:
        async for progress_msg in ingestion_svc.ingest_repo(owner, repo, session_id):
            # Stop wasting work if the client disconnected
            if ws_manager.has_disconnected(session_id):
                log.info("Client disconnected during ingestion — aborting session %s", session_id)
                return

            if progress_msg.startswith("__features_identified__:"):
                # Sentinel indicating feature identification is done
                raw = progress_msg.split(":", 1)[1]
                features = [f.strip() for f in raw.split(",") if f.strip()]
                session.set_features(features)
                # Push to WebSocket if client is already connected
                await ws_manager.send_features(session_id, features)
                # Send first question
                first_q = session.next_question()
                if first_q:
                    await ws_manager.send_question(session_id, first_q)
            else:
                await ws_manager.send_progress(session_id, progress_msg)

    except Exception as exc:
        log.error("❌ Ingestion failed for session %s: %s", session_id, exc)
        session.mark_error()
        await ws_manager.send_error(session_id, f"Ingestion failed: {exc}")


@app.websocket("/ws/article/{session_id}")
async def article_websocket(websocket: WebSocket, session_id: str):
    """
    Bidirectional WebSocket for the chat-based article pipeline.

    Client → Server events:
      { "type": "answer",      "data": "<user answer>" }
      { "type": "tune",        "data": "<tuning instruction>" }
      { "type": "regenerate",  "data": "" }

    Server → Client events:
      { "type": "progress",            "data": "<message>" }
      { "type": "features_identified", "data": ["feature1", ...] }
      { "type": "question",            "data": "<question text>" }
      { "type": "article_chunk",       "data": "<token chunk>" }
      { "type": "article_done",        "data": { "word_count": N } }
      { "type": "error",               "data": "<message>" }
    """
    session = _sessions.get(session_id)
    if session is None:
        await websocket.accept()
        await websocket.send_json({"type": "error", "data": f"Session '{session_id}' not found."})
        await websocket.close()
        return

    await ws_manager.connect(session_id, websocket)

    # If ingestion already finished before WS connected, send current state
    if session.state == ArticleSessionState.ERROR:
        await ws_manager.send_error(session_id, "Ingestion failed before connection was established.")
        return

    if session.state == ArticleSessionState.QUESTIONING and session.features:
        await ws_manager.send_features(session_id, session.features)
        q = session.next_question()
        if q:
            await ws_manager.send_question(session_id, q)

    gemini_svc = _get_gemini_service()
    builder = _get_article_builder()

    try:
        while True:
            raw = await websocket.receive_json()
            msg = WSMessageIn(**raw)

            if msg.type == "answer" or msg.type == "mcq_answer":
                # Accept both plain answer and structured mcq_answer
                answer_text = msg.data
                if isinstance(msg.data, dict):
                    answer_text = msg.data.get("custom_text") or msg.data.get("option_id", "")
                session.record_answer(str(answer_text))

                if session.has_enough_context:
                    # All Q&A done — generate the article
                    await _stream_article(session, gemini_svc, builder)
                else:
                    next_q = session.next_question()
                    if next_q:
                        await ws_manager.send_question(session_id, next_q)

            elif msg.type == "tune":
                if not session.draft:
                    await ws_manager.send_error(session_id, "No draft to tune yet.")
                    continue
                # Append tuning instruction to the existing draft prompt and regenerate
                tune_prompt = (
                    f"Here is a Medium article draft:\n\n{session.draft}\n\n"
                    f"Apply the following change and return the FULL revised article:\n{msg.data}"
                )
                await _stream_article_from_prompt(session, gemini_svc, tune_prompt)

            elif msg.type == "regenerate":
                await _stream_article(session, gemini_svc, builder)

    except WebSocketDisconnect:
        log.info("WS client disconnected from session %s", session_id)
    except Exception as exc:
        log.error("WS error on session %s: %s", session_id, exc)
        await ws_manager.send_error(session_id, str(exc))
    finally:
        ws_manager.disconnect(session_id)


async def _stream_article(
    session: ArticleSession,
    gemini_svc: GeminiService,
    builder: ArticleBuilder,
) -> None:
    """Build the prompt and stream Gemini's response to the client."""
    session.mark_generating()
    prompt = await builder.build_prompt(session)
    await _stream_article_from_prompt(session, gemini_svc, prompt)


async def _stream_article_from_prompt(
    session: ArticleSession,
    gemini_svc: GeminiService,
    prompt: str,
) -> None:
    """Stream article tokens to the client and track the full draft."""
    full_text = ""
    try:
        async for chunk in gemini_svc.stream_generate(prompt):
            full_text += chunk
            await ws_manager.send_article_chunk(session.session_id, chunk)
        word_count = len(full_text.split())
        session.mark_done(full_text)
        await ws_manager.send_article_done(session.session_id, word_count)
        log.info("Article generation done for session %s: %d words", session.session_id, word_count)
    except Exception as exc:
        log.error("Streaming failed for session %s: %s", session.session_id, exc)
        session.mark_error()
        await ws_manager.send_error(session.session_id, f"Generation failed: {exc}")


# ---------------------------------------------------------------------------
# Generic MCQ Content Sessions (README, LinkedIn, Resume)
# ---------------------------------------------------------------------------

_content_sessions: dict[str, ContentSession] = {}


@app.post("/session/start", response_model=ArticleStartResponse)
async def session_start(request: SessionStartRequest, background_tasks: BackgroundTasks):
    """Start a generic MCQ-driven content generation session."""
    if request.content_type not in ("readme", "linkedin", "resume"):
        raise HTTPException(status_code=400, detail=f"Invalid content_type: {request.content_type}")

    session_id = str(uuid.uuid4())
    session = ContentSession(
        session_id=session_id,
        owner=request.owner_name,
        repo=request.repo_name,
        content_type=request.content_type,
    )
    _content_sessions[session_id] = session
    log.info("🆕 Content session %s [%s] for %s/%s",
             session_id, request.content_type, request.owner_name, request.repo_name)

    background_tasks.add_task(
        _run_content_ingestion,
        session_id=session_id,
        owner=request.owner_name,
        repo=request.repo_name,
    )

    return ArticleStartResponse(
        session_id=session_id,
        status=ArticleSessionState.INGESTING,
        message=f"Session started. Connect to WS /ws/session/{session_id}",
    )


async def _run_content_ingestion(session_id: str, owner: str, repo: str) -> None:
    """Background: ingest repo and identify features for a content session."""
    session = _content_sessions.get(session_id)
    if session is None:
        return

    ingestion_svc = _get_ingestion_service()

    try:
        async for progress_msg in ingestion_svc.ingest_repo(owner, repo, session_id, skip_embedding=True):
            # Stop wasting work if the client disconnected
            if ws_manager.has_disconnected(session_id):
                log.info("Client disconnected during content ingestion — aborting session %s", session_id)
                return

            if progress_msg.startswith("__features_identified__:"):
                raw = progress_msg.split(":", 1)[1]
                features = [f.strip() for f in raw.split(",") if f.strip()]
                session.set_features(features)
                await ws_manager.send_features(session_id, features)
                first_q = session.next_question()
                if first_q:
                    await ws_manager.send_question(session_id, first_q)
            else:
                await ws_manager.send_progress(session_id, progress_msg)
    except Exception as exc:
        log.error("❌ Content ingestion failed for session %s: %s", session_id, exc)
        session.mark_error()
        await ws_manager.send_error(session_id, f"Ingestion failed: {exc}")


@app.websocket("/ws/session/{session_id}")
async def content_websocket(websocket: WebSocket, session_id: str):
    """WebSocket for generic MCQ content sessions."""
    session = _content_sessions.get(session_id)
    if session is None:
        await websocket.accept()
        await websocket.send_json({"type": "error", "data": f"Session '{session_id}' not found."})
        await websocket.close()
        return

    await ws_manager.connect(session_id, websocket)

    if session.state == ArticleSessionState.ERROR:
        await ws_manager.send_error(session_id, "Ingestion failed before connection.")
        return

    if session.state == ArticleSessionState.QUESTIONING and session.features:
        await ws_manager.send_features(session_id, session.features)
        q = session.next_question()
        if q:
            await ws_manager.send_question(session_id, q)

    readme_svc = get_readme_service()

    try:
        while True:
            raw = await websocket.receive_json()
            msg = WSMessageIn(**raw)

            if msg.type in ("answer", "mcq_answer"):
                answer_text = msg.data
                if isinstance(msg.data, dict):
                    answer_text = msg.data.get("custom_text") or msg.data.get("option_id", "")
                session.record_answer(str(answer_text))

                if session.has_enough_context:
                    await _generate_content(session, readme_svc)
                else:
                    next_q = session.next_question()
                    if next_q:
                        await ws_manager.send_question(session_id, next_q)

    except WebSocketDisconnect:
        log.info("WS disconnected from content session %s", session_id)
    except Exception as exc:
        log.error("WS error on content session %s: %s", session_id, exc)
        await ws_manager.send_error(session_id, str(exc))
    finally:
        ws_manager.disconnect(session_id)


async def _generate_content(session: ContentSession, readme_svc: ReadmeService) -> None:
    """Generate content using the existing service, stream result to client."""
    session.mark_generating()
    params = session.get_generation_params()

    try:
        if session.content_type == "readme":
            result = await readme_svc.generate_readme(
                owner=session.owner,
                repo=session.repo,
                banner_config=BannerConfig(**params.pop("banner_config")),
                **params,
            )
            content = result.get("readme_content", "")
        else:
            ct = ContentType.LINKEDIN if session.content_type == "linkedin" else ContentType.RESUME
            result = await readme_svc.generate_content(
                owner=session.owner,
                repo=session.repo,
                content_type=ct,
                **params,
            )
            content = result.get("content", "")

        # Stream in chunks to match the article UX
        chunk_size = 80
        for i in range(0, len(content), chunk_size):
            await ws_manager.send_article_chunk(session.session_id, content[i:i + chunk_size])

        session.mark_done(content)
        await ws_manager.send_article_done(session.session_id, len(content.split()))

    except Exception as exc:
        log.error("Content generation failed for session %s: %s", session.session_id, exc)
        session.mark_error()
        await ws_manager.send_error(session.session_id, f"Generation failed: {exc}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
