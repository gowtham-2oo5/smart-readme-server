"""
ArticleSession
==============
State machine that tracks a single user's chat-based article generation session.

States:
  INGESTING   → repo is being processed
  QUESTIONING → system is asking the user clarifying questions
  GENERATING  → Gemini is streaming the article
  TUNING      → user can request tweaks to the draft
  DONE        → session complete
  ERROR       → unrecoverable error
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List

from models import ArticleSessionState

log = logging.getLogger(__name__)

# ── Adaptive question bank ────────────────────────────────────────────────────

_BASE_QUESTIONS = [
    "Who is the target audience for this article? (e.g. 'beginner Python devs', 'senior backend engineers')",
    "What tone do you prefer? Options: A) Technical deep-dive  B) Story-driven / conversational  C) Tutorial walkthrough",
]

_FEATURE_QUESTIONS = [
    "Which 2-3 features should be the main focus of the article?",
]

_API_QUESTIONS = [
    "Should we include real API request/response examples with curl or code snippets?",
]

_ML_QUESTIONS = [
    "Should we include benchmark results or performance comparisons?",
]

_LENGTH_QUESTION = (
    "How long should the article be? Options: A) Short (~800 words)  "
    "B) Medium (~1500 words, recommended)  C) Long (~2500 words)"
)


@dataclass
class ArticleSession:
    """Holds all state for one chat-based article generation session."""

    session_id: str
    owner: str
    repo: str

    state: ArticleSessionState = ArticleSessionState.INGESTING
    features: list[str] = field(default_factory=list)
    answers: dict[str, str] = field(default_factory=dict)
    draft: str = ""

    _question_queue: list[str] = field(default_factory=list)
    _asked: list[str] = field(default_factory=list)

    # ── Feature / question setup ──────────────────────────────────────────────

    def set_features(self, features: list[str]) -> None:
        """Called by IngestionService after feature identification."""
        self.features = features
        self._build_question_queue()
        self.state = ArticleSessionState.QUESTIONING
        log.info("Session %s: features set, %d questions queued",
                 self.session_id, len(self._question_queue))

    def _build_question_queue(self) -> None:
        """Construct a context-aware question list based on detected features."""
        questions = list(_BASE_QUESTIONS)

        feature_text = " ".join(self.features).lower()

        if len(self.features) >= 4:
            questions += _FEATURE_QUESTIONS

        if any(kw in feature_text for kw in ("api", "endpoint", "rest", "graphql", "http")):
            questions += _API_QUESTIONS

        if any(kw in feature_text for kw in ("model", "ml", "ai", "train", "predict", "benchmark")):
            questions += _ML_QUESTIONS

        questions.append(_LENGTH_QUESTION)
        self._question_queue = questions

    # ── Q&A state management ───────────────────────────────────────────────────

    def next_question(self) -> str | None:
        """Return the next unanswered question, or None if all answered."""
        remaining = [q for q in self._question_queue if q not in self._asked]
        if not remaining:
            return None
        q = remaining[0]
        self._asked.append(q)
        return q

    def record_answer(self, answer: str) -> None:
        """Store the user's answer to the last-asked question."""
        if self._asked:
            last_q = self._asked[-1]
            self.answers[last_q] = answer
            log.debug("Session %s: answered Q[%d] = %r", self.session_id,
                      len(self.answers), answer[:60])

    @property
    def has_enough_context(self) -> bool:
        """True once all questions have been presented and answered."""
        return (
            len(self.answers) >= len(self._question_queue)
            and len(self._question_queue) > 0
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def mark_generating(self) -> None:
        self.state = ArticleSessionState.GENERATING

    def mark_done(self, draft: str) -> None:
        self.draft = draft
        self.state = ArticleSessionState.TUNING   # allow follow-up tuning

    def mark_error(self) -> None:
        self.state = ArticleSessionState.ERROR

    def target_length_words(self) -> int:
        """Parse the user's length choice into a target word count."""
        answer = " ".join(self.answers.values()).upper()
        if "SHORT" in answer or " A)" in answer or answer.strip() == "A":
            return 800
        if "LONG" in answer or " C)" in answer or answer.strip() == "C":
            return 2500
        return 1500   # default MEDIUM
