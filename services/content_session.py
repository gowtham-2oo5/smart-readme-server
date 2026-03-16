"""
ContentSession
==============
Generic MCQ-driven session for README, LinkedIn, and Resume generation.
Dynamically builds questions based on content type and detected repo features.
"""

from __future__ import annotations

import copy
import logging
from dataclasses import dataclass, field

from models import ArticleSessionState, ContentType

log = logging.getLogger(__name__)

# ── Question banks per content type ───────────────────────────────────────────

_README_QUESTIONS: list[dict] = [
    {
        "key": "audience",
        "question": "Who will read this README?",
        "multi_select": True,
        "options": [
            {"id": "developers_using", "label": "Developers using it", "description": "They want to install, configure, and use your project"},
            {"id": "developers_contributing", "label": "Contributors", "description": "They want to understand the codebase and contribute"},
            {"id": "hiring_managers", "label": "Recruiters / Hiring managers", "description": "They want to see what you built and how well you document"},
            {"id": "students", "label": "Students / Learners", "description": "They want to learn from your code and approach"},
        ],
        "allow_custom": True,
        "custom_placeholder": "Describe your target audience…",
    },
    {
        "key": "differentiator",
        "question": "What makes this project stand out?",
        "multi_select": True,
        "options": [
            {"id": "tech_stack", "label": "Interesting tech stack", "description": "Unique combination of technologies or architecture"},
            {"id": "problem_solved", "label": "Problem it solves", "description": "Addresses a real pain point in a clever way"},
            {"id": "scale_perf", "label": "Scale / Performance", "description": "Handles large data, high traffic, or complex workflows"},
            {"id": "learning", "label": "Learning project", "description": "Built to learn and demonstrate skills"},
            {"id": "dx", "label": "Developer experience", "description": "Easy to set up, great docs, smooth workflow"},
        ],
        "allow_custom": True,
        "custom_placeholder": "What's special about this project?",
    },
    {
        "key": "sections",
        "question": "Which sections matter most?",
        "multi_select": True,
        "options": [
            {"id": "api_docs", "label": "API documentation", "description": "Endpoint tables, request/response examples"},
            {"id": "architecture", "label": "Architecture overview", "description": "System design, data flow, diagrams"},
            {"id": "setup_guide", "label": "Detailed setup guide", "description": "Step-by-step with env vars, configs, troubleshooting"},
            {"id": "examples", "label": "Usage examples", "description": "Real-world code snippets and workflows"},
            {"id": "contributing", "label": "Contributing guide", "description": "How to contribute, code style, PR process"},
        ],
        "allow_custom": True,
        "custom_placeholder": "Any other sections you want?",
    },
    {
        "key": "tone",
        "question": "What tone should the README have?",
        "options": [
            {"id": "professional", "label": "Professional", "description": "Clean, formal, enterprise-ready"},
            {"id": "developer", "label": "Developer-friendly", "description": "Casual but informative, like good open-source docs"},
            {"id": "minimal", "label": "Minimal", "description": "Just the essentials, no fluff"},
            {"id": "detailed", "label": "Comprehensive", "description": "Thorough documentation covering everything"},
        ],
        "allow_custom": True,
        "custom_placeholder": "Describe the tone you want…",
    },
    {
        "key": "banner",
        "question": "Want a banner at the top?",
        "options": [
            {"id": "professional", "label": "Professional Banner", "description": "Clean capsule-style header with tech stack"},
            {"id": "animated", "label": "Animated Banner", "description": "Eye-catching waving animation"},
            {"id": "none", "label": "No Banner", "description": "Start clean with just the title and badges"},
        ],
        "allow_custom": False,
    },
]

_LINKEDIN_QUESTIONS: list[dict] = [
    {
        "key": "story_angle",
        "question": "What's the story behind this project?",
        "options": [
            {"id": "problem_solved", "label": "I solved a real problem", "description": "Built this because something was broken/missing"},
            {"id": "learning_journey", "label": "Learning journey", "description": "Built this to learn a new tech/concept"},
            {"id": "team_achievement", "label": "Team achievement", "description": "Shipped this with a team — highlight collaboration"},
            {"id": "side_project", "label": "Weekend/side project", "description": "Built this for fun or curiosity"},
            {"id": "hackathon", "label": "Hackathon / Competition", "description": "Built under time pressure, won something"},
        ],
        "allow_custom": True,
        "custom_placeholder": "What's the story?",
    },
    {
        "key": "highlights",
        "question": "What should the post highlight?",
        "multi_select": True,
        "options": [
            {"id": "tech_decisions", "label": "Technical decisions", "description": "Why you chose this stack/architecture"},
            {"id": "challenges", "label": "Challenges overcome", "description": "Hard problems you solved along the way"},
            {"id": "impact", "label": "Impact & numbers", "description": "Users, performance gains, scale metrics"},
            {"id": "lessons", "label": "Lessons learned", "description": "What you'd do differently next time"},
            {"id": "demo", "label": "Demo / Screenshots", "description": "Visual proof of what it does"},
        ],
        "allow_custom": True,
        "custom_placeholder": "Anything else to highlight?",
    },
    {
        "key": "goal",
        "question": "What do you want from this post?",
        "options": [
            {"id": "visibility", "label": "Get visibility", "description": "Showcase your work to a wider audience"},
            {"id": "hiring", "label": "Attract opportunities", "description": "Show skills to recruiters and hiring managers"},
            {"id": "community", "label": "Build community", "description": "Get contributors, feedback, or collaborators"},
            {"id": "thought_leadership", "label": "Thought leadership", "description": "Position yourself as an expert in this space"},
        ],
        "allow_custom": True,
        "custom_placeholder": "What's your goal?",
    },
    {
        "key": "tone",
        "question": "What vibe should the post have?",
        "options": [
            {"id": "thought_leader", "label": "Insightful & confident", "description": "Share expertise and lessons learned"},
            {"id": "casual", "label": "Casual & authentic", "description": "Conversational, like talking to a friend"},
            {"id": "technical", "label": "Technical deep-dive", "description": "Code-focused, architecture decisions"},
            {"id": "storytelling", "label": "Storytelling", "description": "Narrative-driven, build-in-public style"},
        ],
        "allow_custom": True,
        "custom_placeholder": "Describe the vibe you want…",
    },
]

_RESUME_QUESTIONS: list[dict] = [
    {
        "key": "role_target",
        "question": "What role are you targeting?",
        "options": [
            {"id": "Software Engineer", "label": "Software Engineer", "description": "General SWE role"},
            {"id": "Frontend Engineer", "label": "Frontend Engineer", "description": "UI/UX focused"},
            {"id": "Backend Engineer", "label": "Backend Engineer", "description": "APIs, systems, infra"},
            {"id": "Full Stack Engineer", "label": "Full Stack Engineer", "description": "End-to-end development"},
            {"id": "DevOps Engineer", "label": "DevOps/SRE", "description": "Infrastructure, CI/CD, reliability"},
            {"id": "ML Engineer", "label": "ML Engineer", "description": "Machine learning, data pipelines"},
        ],
        "allow_custom": True,
        "custom_placeholder": "Type your target role…",
    },
    {
        "key": "seniority",
        "question": "What seniority level?",
        "options": [
            {"id": "intern", "label": "Intern", "description": "Learning-focused, eager to grow"},
            {"id": "junior", "label": "Junior", "description": "Growth & contribution"},
            {"id": "mid", "label": "Mid-level", "description": "Ownership & delivery"},
            {"id": "senior", "label": "Senior", "description": "Impact & technical leadership"},
            {"id": "staff", "label": "Staff+", "description": "Cross-team influence, architecture"},
        ],
        "allow_custom": False,
    },
    {
        "key": "emphasis",
        "question": "What should the bullets emphasize?",
        "multi_select": True,
        "options": [
            {"id": "impact", "label": "Impact & metrics", "description": "Quantifiable results: %, speed, scale"},
            {"id": "technical", "label": "Technical depth", "description": "Architecture, algorithms, system design"},
            {"id": "leadership", "label": "Leadership", "description": "Mentoring, decisions, cross-team work"},
            {"id": "collaboration", "label": "Collaboration", "description": "Teamwork, code reviews, knowledge sharing"},
            {"id": "problem_solving", "label": "Problem solving", "description": "Debugging, root cause analysis, creative solutions"},
        ],
        "allow_custom": True,
        "custom_placeholder": "Anything specific to highlight?",
    },
    {
        "key": "style",
        "question": "What style of bullet points?",
        "options": [
            {"id": "metrics_heavy", "label": "Metrics Heavy", "description": "Quantifiable impact: %, speed, scale"},
            {"id": "narrative", "label": "Narrative", "description": "Story-driven, context + outcome"},
            {"id": "technical_depth", "label": "Technical Depth", "description": "Stack, architecture, implementation details"},
            {"id": "leadership", "label": "Leadership", "description": "Mentoring, decisions, cross-team work"},
        ],
        "allow_custom": True,
        "custom_placeholder": "Describe the style you want…",
    },
    {
        "key": "num_bullets",
        "question": "How many bullet points?",
        "options": [
            {"id": "3", "label": "3 bullets", "description": "Concise — for a tight resume"},
            {"id": "5", "label": "5 bullets", "description": "Standard — good balance of depth"},
            {"id": "8", "label": "8 bullets", "description": "Comprehensive — for a detailed project section"},
        ],
        "allow_custom": False,
    },
]

_BANKS: dict[str, list[dict]] = {
    "readme": _README_QUESTIONS,
    "linkedin": _LINKEDIN_QUESTIONS,
    "resume": _RESUME_QUESTIONS,
}

# Feature-focus question injected when repo has enough detected features
_FEATURE_MCQ: dict = {
    "key": "feature_focus",
    "question": "Which features should be highlighted?",
    "options": [],  # filled dynamically
    "allow_custom": True,
    "custom_placeholder": "Tell us what to focus on…",
}


@dataclass
class ContentSession:
    """Holds state for one MCQ-driven content generation session."""

    session_id: str
    owner: str
    repo: str
    content_type: str  # "readme" | "linkedin" | "resume"

    state: ArticleSessionState = ArticleSessionState.INGESTING
    features: list[str] = field(default_factory=list)
    answers: dict[str, str] = field(default_factory=dict)
    result: str = ""

    _question_queue: list[dict] = field(default_factory=list)
    _asked: list[str] = field(default_factory=list)

    def set_features(self, features: list[str]) -> None:
        self.features = features
        self._build_question_queue()
        self.state = ArticleSessionState.QUESTIONING
        log.info("Session %s [%s]: %d questions queued",
                 self.session_id, self.content_type, len(self._question_queue))

    def _build_question_queue(self) -> None:
        bank = _BANKS.get(self.content_type, [])
        questions = [copy.deepcopy(q) for q in bank]

        # Inject feature focus if enough features detected
        if len(self.features) >= 3:
            fq = copy.deepcopy(_FEATURE_MCQ)
            fq["options"] = [
                {"id": f, "label": f, "description": ""}
                for f in self.features[:8]
            ]
            # Insert after first question
            questions.insert(1, fq)

        self._question_queue = questions

    def next_question(self) -> dict | None:
        idx = len(self._asked)
        if idx >= len(self._question_queue):
            return None
        mcq = self._question_queue[idx]
        self._asked.append(mcq.get("key", mcq["question"]))
        return {
            "round": idx + 1,
            "total_rounds": len(self._question_queue),
            "question": mcq["question"],
            "options": mcq["options"],
            "allow_custom": mcq.get("allow_custom", False),
            "custom_placeholder": mcq.get("custom_placeholder", ""),
            "multi_select": mcq.get("multi_select", False),
        }

    def record_answer(self, answer: str) -> None:
        if self._asked:
            key = self._asked[-1]
            self.answers[key] = answer
            log.debug("Session %s: %s = %r", self.session_id, key, answer[:60])

    @property
    def has_enough_context(self) -> bool:
        return len(self.answers) >= len(self._question_queue) > 0

    def get_generation_params(self) -> dict:
        """Convert answers into params for the existing generate_content / generate_readme endpoints."""
        a = self.answers

        # Build a human-readable preferences string from ALL answers
        # so every question actually influences the output
        user_preferences = self._build_user_preferences()

        if self.content_type == "readme":
            tone = a.get("tone", "professional")
            if tone not in ("professional", "developer", "minimal", "detailed"):
                tone = "professional"

            banner_answer = a.get("banner", "professional")
            return {
                "tone": tone,
                "user_preferences": user_preferences,
                "banner_config": {
                    "include_banner": banner_answer != "none",
                    "style": banner_answer if banner_answer != "none" else "professional",
                    "font": "jetbrains",
                    "theme": "github_dark",
                },
            }
        elif self.content_type == "linkedin":
            goal = a.get("goal", "visibility")
            focus_map = {
                "visibility": "business_value",
                "hiring": "hiring",
                "community": "business_value",
                "thought_leadership": "technical",
            }
            tone = a.get("tone", "thought_leader")
            if tone == "storytelling":
                tone = "casual"
            return {
                "tone": tone,
                "focus": focus_map.get(goal, "business_value"),
                "user_preferences": user_preferences,
            }
        elif self.content_type == "resume":
            style = a.get("style", "metrics_heavy")
            num_bullets_str = a.get("num_bullets", "5")
            try:
                num_bullets = int(num_bullets_str)
            except ValueError:
                num_bullets = 5
            return {
                "role_target": a.get("role_target", "Software Engineer"),
                "seniority": a.get("seniority", "mid"),
                "num_bullets": num_bullets,
                "include_metrics": style in ("metrics_heavy", "technical_depth"),
                "user_preferences": user_preferences,
            }
        return {}

    def _build_user_preferences(self) -> str:
        """Convert all MCQ answers into a structured preferences block for the AI prompt."""
        if not self.answers:
            return ""

        # Map question keys to readable labels
        labels = {
            "audience": "Target audience",
            "differentiator": "What makes it stand out",
            "sections": "Priority sections",
            "feature_focus": "Features to highlight",
            "tone": "Tone",
            "banner": "Banner preference",
            "story_angle": "Story angle",
            "highlights": "Key highlights",
            "goal": "Post goal",
            "role_target": "Target role",
            "seniority": "Seniority level",
            "emphasis": "Bullet emphasis",
            "style": "Writing style",
            "num_bullets": "Number of bullets",
        }

        lines = []
        for key, value in self.answers.items():
            if key == "banner":
                continue  # Banner is handled structurally, not in the prompt
            label = labels.get(key, key.replace("_", " ").title())
            lines.append(f"- {label}: {value}")

        if not lines:
            return ""

        return "### USER PREFERENCES (from interview):\n" + "\n".join(lines)


    def mark_generating(self) -> None:
        self.state = ArticleSessionState.GENERATING

    def mark_done(self, result: str) -> None:
        self.result = result
        self.state = ArticleSessionState.DONE

    def mark_error(self) -> None:
        self.state = ArticleSessionState.ERROR
