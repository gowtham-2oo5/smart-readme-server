"""
GeminiService
=============
Thin async wrapper around the Google Generative AI SDK for Gemini 2.5 Flash.

Provides:
  - ``generate(prompt)``           → full text (non-streaming)
  - ``stream_generate(prompt)``    → async generator yielding token chunks

The AIService (Qwen / NVIDIA) is kept separate; this service handles only
Gemini usage so concerns stay clean.
"""

from __future__ import annotations

import logging
from typing import AsyncIterator

import google.generativeai as genai

from config import settings

log = logging.getLogger(__name__)


class GeminiService:
    """Google Gemini 2.5 Flash — used for final article generation."""

    def __init__(self):
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not set in environment / .env")
        genai.configure(api_key=settings.gemini_api_key)
        self._model = genai.GenerativeModel(settings.gemini_model)
        log.info("GeminiService initialised with model %s", settings.gemini_model)

    # ── Non-streaming ─────────────────────────────────────────────────────────

    async def generate(self, prompt: str) -> str:
        """Generate a full response synchronously (wrapped in asyncio executor)."""
        import asyncio
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self._model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                    top_p=0.95,
                    max_output_tokens=4096,
                ),
            ),
        )
        return response.text

    # ── Streaming ─────────────────────────────────────────────────────────────

    async def stream_generate(self, prompt: str) -> AsyncIterator[str]:
        """
        Async generator that yields text chunks as Gemini streams them.

        Usage:
            async for chunk in gemini.stream_generate(prompt):
                await ws.send_json({"type": "article_chunk", "data": chunk})
        """
        import asyncio
        from queue import Queue, Empty

        chunk_queue: Queue[str | None] = Queue()

        def _stream_sync():
            """Run the blocking stream in a thread; push chunks to the queue."""
            try:
                response = self._model.generate_content(
                    prompt,
                    stream=True,
                    generation_config=genai.GenerationConfig(
                        temperature=0.7,
                        top_p=0.95,
                        max_output_tokens=4096,
                    ),
                )
                for chunk in response:
                    if chunk.text:
                        chunk_queue.put(chunk.text)
            except Exception as exc:
                log.error("Gemini stream error: %s", exc)
            finally:
                chunk_queue.put(None)   # sentinel

        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, _stream_sync)

        # Drain the queue asynchronously
        while True:
            try:
                item = chunk_queue.get_nowait()
            except Empty:
                await asyncio.sleep(0.05)   # yield control briefly
                continue

            if item is None:
                break
            yield item
