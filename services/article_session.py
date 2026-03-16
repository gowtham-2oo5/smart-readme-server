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

from models import ArticleSessionState

log = logging.getLogger(__name__)

# ── Adaptive question bank ────────────────────────────────────────────────────

_MCQ_BANK: list[dict] = [
    {
        "question": "Who is the target audience for this article?",
        "options": [
            {"id": "a", "label": "Beginners", "description": "New developers, step-by-step explanations"},
            {"id": "b", "label": "Intermediate devs", "description": "Familiar with the stack, want depth"},
            {"id": "c", "label": "Senior engineers", "description": "Architecture decisions, tradeoffs"},
        ],
        "allow_custom": True,
        "custom_placeholder": "Describe your target audience...",
    },
    {
        "question": "What tone and style should the article have?",
        "options": [
            {"id": "a", "label": "Technical deep-dive", "description": "Code-heavy, detailed analysis"},
            {"id": "b", "label": "Story-driven", "description": "Conversational, narrative flow"},
            {"id": "c", "label": "Tutorial walkthrough", "description": "Step-by-step, hands-on guide"},
        ],
        "allow_custom": True,
        "custom_placeholder": "Describe the style you want...",
    },
]

_FEATURE_MCQ: dict = {
    "question": "Which features should be the main focus?",
    "options": [],  # filled dynamically from detected features
    "allow_custom": True,
    "custom_placeholder": "Tell us what to focus on...",
}

_LENGTH_MCQ: dict = {
    "question": "How long should the article be?",
    "options": [
        {"id": "a", "label": "Short", "description": "~800 words, quick overview"},
        {"id": "b", "label": "Medium", "description": "~1500 words, solid coverage"},
        {"id": "c", "label": "Long", "description": "~2500 words, comprehensive deep-dive"},
    ],
    "allow_custom": False,
    "custom_placeholder": "",
}


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

    _question_queue: list[dict] = field(default_factory=list)
    _asked: list[str] = field(default_factory=list)

    # ── Feature / question setup ──────────────────────────────────────────────

    def set_features(self, features: list[str]) -> None:
        """Called by IngestionService after feature identification."""
        self.features = features
        self._build_question_queue()
        self.state = ArticleSessionState.QUESTIONING
        log.info("Session %s: features set, %d MCQ rounds queued",
                 self.session_id, len(self._question_queue))

    def _build_question_queue(self) -> None:
        """Construct MCQ rounds based on detected features."""
        import copy
        questions: list[dict] = [copy.deepcopy(q) for q in _MCQ_BANK]

        # Add feature focus question if enough features detected
        if len(self.features) >= 3:
            fq = copy.deepcopy(_FEATURE_MCQ)
            fq["options"] = [
                {"id": chr(97 + i), "label": f, "description": ""}
                for i, f in enumerate(self.features[:8])
            ]
            questions.append(fq)

        questions.append(copy.deepcopy(_LENGTH_MCQ))
        self._question_queue = questions

    # ── Q&A state management ───────────────────────────────────────────────────

    def next_question(self) -> dict | None:
        """Return the next MCQ dict, or None if all answered."""
        idx = len(self._asked)
        if idx >= len(self._question_queue):
            return None
        mcq = self._question_queue[idx]
        self._asked.append(mcq["question"])
        return {
            "round": idx + 1,
            "total_rounds": len(self._question_queue),
            **mcq,
        }

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
