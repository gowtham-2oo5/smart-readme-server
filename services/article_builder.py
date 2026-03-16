"""
ArticleBuilder
==============
Constructs the final prompt sent to Gemini for article generation.

Combines:
  - RAG-retrieved relevant code chunks
  - User answers from the Q&A phase
  - Identified features
  - Medium-specific article formatting instructions
"""

from __future__ import annotations

import logging

from services.article_session import ArticleSession
from services.rag_service import RAGService

log = logging.getLogger(__name__)


class ArticleBuilder:
    """Builds the Gemini article generation prompt from session context + RAG."""

    def __init__(self, rag_service: RAGService):
        self._rag = rag_service

    async def build_prompt(self, session: ArticleSession) -> str:
        """
        Assemble the full prompt for Gemini.

        Retrieves relevant chunks for three facets of the article to give
        Gemini well-rounded context without hitting token limits.
        """
        target_words = session.target_length_words()

        # Pull rich context for different article angles
        # With reranking, we can safely fetch more candidates — the cross-encoder
        # will surface the most relevant ones.
        overview_chunks = await self._rag.retrieve(
            session.session_id,
            query="project overview, main purpose, what does it do, problem solved",
            k=8,
        )
        impl_chunks = await self._rag.retrieve(
            session.session_id,
            query="implementation details, architecture, core logic, algorithms, data flow",
            k=8,
            chunk_types=["function", "class"],
        )
        config_chunks = await self._rag.retrieve(
            session.session_id,
            query="setup, configuration, dependencies, tech stack, environment",
            k=5,
            chunk_types=["config"],
        )

        rag_context = _format_chunks("Project Overview", overview_chunks) + \
                      _format_chunks("Implementation", impl_chunks) + \
                      _format_chunks("Configuration / Setup", config_chunks)

        features_str = "\n".join(f"- {f}" for f in session.features)
        qa_str = "\n".join(
            f"Q: {q}\nA: {a}" for q, a in session.answers.items()
        )

        tone_note = _parse_tone(session.answers)
        focus_note = _parse_focus(session.answers, session.features)

        return f"""You are a world-class technical writer creating a Medium article.

REPOSITORY: {session.owner}/{session.repo}
TARGET LENGTH: approximately {target_words} words
TONE: {tone_note}
FOCUS: {focus_note}

CORE FEATURES IDENTIFIED:
{features_str}

USER PREFERENCES (Q&A):
{qa_str}

RELEVANT CODEBASE CONTEXT (retrieved via semantic search):
{rag_context}

──────────────────────────────────────────────────────────────────────────────
ARTICLE REQUIREMENTS:

1. **Structure** — Write a proper Medium article with:
   - A compelling hook in the opening paragraph (no "Introduction" heading)
   - 3-5 sections with descriptive H2 headings (##)
   - A concise closing that gives readers a clear next step

2. **Code snippets** — Include 2-4 real code examples extracted from the
   codebase context above. Format them as fenced code blocks with language tags.
   Only show code that genuinely illuminates a point.

3. **No fluff** — Every sentence earns its place. Cut marketing speak.
   Write as a developer talking honestly to another developer.

4. **Medium style** — First person is fine. Contractions are fine.
   Concrete > abstract. Show, don't just tell.

5. **Accuracy** — Only describe features and code patterns that appear in the
   codebase context. Do not invent capabilities.

6. **Self-verification** — Before outputting, verify:
   - Every code snippet comes from the codebase context above
   - No features are mentioned that aren't evidenced in the code
   - The article teaches something genuinely useful
   - Each section earns its place — no filler paragraphs

Write the complete article now. Do NOT include any preamble or meta-commentary.
Start directly with the article title (use # for title).
"""


# ── Private helpers ───────────────────────────────────────────────────────────

def _format_chunks(label: str, chunks: list[str]) -> str:
    if not chunks:
        return ""
    joined = "\n---\n".join(c[:800] for c in chunks)
    return f"\n### {label}\n{joined}\n"


def _parse_tone(answers: dict[str, str]) -> str:
    combined = " ".join(answers.values()).upper()
    if "B" in combined or "STORY" in combined or "CONVERSATIONAL" in combined:
        return "Story-driven and conversational — use first person, share motivations"
    if "C" in combined or "TUTORIAL" in combined:
        return "Tutorial walkthrough — step by step, beginner-friendly"
    return "Technical deep-dive — precise, informative, assumes developer audience"


def _parse_focus(answers: dict[str, str], features: list[str]) -> str:
    combined = " ".join(answers.values())
    # If user explicitly named features, use that
    for feat in features:
        if feat.lower()[:10] in combined.lower():
            return combined
    # Fallback to top 3 features
    return ", ".join(features[:3]) if features else "core functionality"
