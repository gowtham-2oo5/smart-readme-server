"""
Prompt templates for each content generation type.

Each builder follows the instruction hierarchy:
  System Context → Task → Examples → Input Data → Output Format → Self-Verification
"""

from __future__ import annotations

from typing import Dict, Optional

from models import ProjectMetadata


# ---------------------------------------------------------------------------
# LinkedIn Post
# ---------------------------------------------------------------------------

def build_linkedin_prompt(
    project_name: str,
    github_url: str,
    file_contents: str,
    existing_readme: str,
    metadata: ProjectMetadata,
    tone: str = "thought_leader",
    focus: str = "business_value",
    user_preferences: str = "",
) -> str:
    """Build a prompt that generates a LinkedIn announcement post."""

    tone_guide = {
        "thought_leader": (
            "Write in a confident, insightful, first-person voice. Share the journey — "
            "the problem, the 'aha' moment, the impact. Use short punchy paragraphs. "
            "Include 1-2 personal reflections that show expertise."
        ),
        "casual": (
            "Write in a friendly, approachable first-person voice. Keep it conversational, "
            "energetic, and authentic. Use short lines and occasional humour."
        ),
        "technical": (
            "Write in a technically precise but accessible voice. Highlight architectural "
            "decisions, performance numbers, and engineering trade-offs. Stay factual."
        ),
    }

    focus_guide = {
        "business_value": (
            "Emphasise the BUSINESS PROBLEM this project solves, the target users, "
            "and the measurable impact. Translate technical features into business outcomes."
        ),
        "technical": (
            "Emphasise the TECHNICAL INNOVATIONS — architecture choices, stack decisions, "
            "performance characteristics, and engineering challenges overcome."
        ),
        "hiring": (
            "Frame this as a showcase of your engineering skills. Highlight the complexity "
            "of problems solved, the scale of the system, and the technologies mastered. "
            "End with a subtle call-to-action about being open to opportunities."
        ),
    }

    system_context = (
        "You are a senior tech professional who writes viral LinkedIn posts. "
        "Your posts consistently get high engagement because they tell authentic "
        "stories about building real software, with concrete details and takeaways."
    )

    example = """
### EXAMPLE OF A GOOD LINKEDIN POST:

I spent 3 weekends building something I wish existed at my last job.

Our team wasted 2+ hours every sprint manually generating release notes from Jira tickets. So I built ReleaseBot — a CLI tool that reads your Git history, maps commits to tickets, and generates polished release notes in seconds.

Here's what it does:
→ Parses conventional commits and links them to Jira/Linear tickets
→ Groups changes by type (features, fixes, breaking changes)
→ Generates markdown release notes with one command
→ Supports custom templates for different audiences (engineering vs. product)

Built with Python, Click, and the Jira REST API. The whole thing is ~800 lines of code.

The best part? It caught 3 missing ticket references in our last release that would've slipped through.

Open source and ready to use: https://github.com/user/releasebot

What's a repetitive task on your team that's begging to be automated?

#OpenSource #DeveloperTools #Python #Automation
"""

    instructions = f"""
### TASK:
Write a LinkedIn post announcing/showcasing this project. It should feel authentic
and personal — NOT like a press release or marketing copy.

### TONE:
{tone_guide.get(tone, tone_guide["thought_leader"])}

### FOCUS:
{focus_guide.get(focus, focus_guide["business_value"])}

### FORMAT RULES:
1. **Hook**: Start with a compelling 1-liner that stops the scroll (no emojis on line 1).
2. **Story**: 2-3 short paragraphs explaining what you built and why it matters.
3. **Key Highlights**: Use → arrows for 3-5 bullet points of concrete achievements/features.
4. **Tech Stack**: Mention technologies naturally, not as a list dump.
5. **CTA**: End with a question or call-to-action to drive comments.
6. **Hashtags**: Add 3-5 relevant hashtags at the very end.
7. **LENGTH**: Keep it under 1300 characters for optimal LinkedIn engagement.
8. **NO markdown formatting** — LinkedIn uses plain text. Use line breaks and → for structure.
9. **Use emojis sparingly** — max 3-4 in the entire post, placed strategically.
10. Output ONLY the post text. No commentary, no wrapping, no scratchpad.

### SELF-VERIFICATION:
Before outputting, check:
- The hook would make YOU stop scrolling
- Every claim is backed by the actual source code
- Tech stack mentions match what's in the codebase
- It reads like a real person wrote it, not a template
"""

    input_data = f"""
### INPUT DATA:
**Project Name**: {project_name}
**Repository**: {github_url}
**Primary Language**: {metadata.primary_language}
**Project Type**: {metadata.project_type}
**Tech Stack**: {', '.join(metadata.tech_stack)}
**Frameworks**: {', '.join(metadata.frameworks) if metadata.frameworks else 'None detected'}

**EXISTING README** (for context):
<existing_readme>
{existing_readme[:2_000] if existing_readme else "No existing README found"}
</existing_readme>

**PROJECT FILES** (for technical depth):
<source_code>
{file_contents[:60_000]}
</source_code>

{user_preferences}

Now write the LinkedIn post.
"""

    return f"{system_context}\n{example}\n{instructions}\n{input_data}"


# ---------------------------------------------------------------------------
# Technical Article
# ---------------------------------------------------------------------------

def build_article_prompt(
    project_name: str,
    github_url: str,
    file_contents: str,
    existing_readme: str,
    metadata: ProjectMetadata,
    tone: str = "professional",
    article_style: str = "deep_dive",
    target_length: str = "medium",
    user_preferences: str = "",
) -> str:
    """Build a prompt that generates a full technical article."""

    style_guide = {
        "tutorial": (
            "Write as a step-by-step tutorial titled 'How I Built {project_name}'. "
            "Walk the reader through the decisions, setup, key implementation details, "
            "and lessons learned. Include code snippets from the actual codebase."
        ),
        "deep_dive": (
            "Write as an architectural deep-dive titled 'Inside the Architecture of {project_name}'. "
            "Explain the system design, data flow, patterns used, and engineering trade-offs. "
            "Target an audience of mid-to-senior engineers."
        ),
        "case_study": (
            "Write as a case study titled 'Solving [Problem] with {project_name}'. "
            "Start with the problem statement, walk through the solution's design, "
            "highlight the results, and extract reusable lessons."
        ),
    }

    length_guide = {
        "short": "Keep the article between 800-1200 words. Be concise and punchy.",
        "medium": "Target 1500-2500 words. Balance depth with readability.",
        "long": "Write a comprehensive 3000-4500 word article. Go deep on architecture and implementation.",
    }

    system_context = (
        "You are a senior technical writer who publishes on Medium, Dev.to, and Hashnode. "
        "Your articles are deeply technical yet highly readable. You explain complex concepts "
        f"with clarity in a {tone} tone and always back claims with real code examples."
    )

    style_instruction = style_guide.get(article_style, style_guide["deep_dive"]).format(
        project_name=project_name
    )

    example = """
### EXAMPLE OF GOOD ARTICLE STRUCTURE:

# Building a Real-Time Notification System That Actually Scales

When our team hit 10K concurrent WebSocket connections, everything broke. Here's how we rebuilt it.

## The Problem: Why Simple WebSockets Don't Scale

[2-3 paragraphs explaining the real problem with specific numbers]

## Architecture: Event-Driven with Redis Pub/Sub

[Explain the design with a clear data flow description]

```python
# The core message router — handles fan-out to connected clients
class MessageRouter:
    async def broadcast(self, channel: str, payload: dict):
        subscribers = self._registry.get(channel, [])
        await asyncio.gather(*[s.send(payload) for s in subscribers])
```

## The Tricky Part: Handling Reconnections Gracefully

[Deep dive into the hardest engineering challenge]

## What I'd Do Differently

1. **Start with SSE, not WebSockets** — For our use case, Server-Sent Events would have been simpler.
2. **Add backpressure earlier** — We learned this the hard way at 50K connections.
3. **Use protocol buffers** — JSON serialization became a bottleneck.
"""

    instructions = f"""
### TASK:
Write a complete technical article about this project.

### STYLE:
{style_instruction}

### LENGTH:
{length_guide.get(target_length, length_guide["medium"])}

### FORMAT RULES:
1. **Title**: A compelling, specific title (not generic like "Building a Web App").
2. **Introduction**: Hook the reader with the problem being solved in 2-3 sentences.
3. **Structure**: Use H2 and H3 headings. Each section should be scannable.
4. **Code Snippets**: Include 3-5 relevant code snippets from the actual project files. Fenced code blocks with language tags.
5. **Architecture**: At least one section explaining system architecture or data flow.
6. **Lessons Learned**: End with 3-5 concrete, specific takeaways (not generic advice).
7. **Conclusion**: Summary and link to the repository.
8. **Output raw markdown**. No ```markdown blocks. No scratchpad. No preamble.

### SELF-VERIFICATION:
Before outputting, check:
- Every code snippet comes from the actual source code provided
- No features are mentioned that don't exist in the codebase
- The article would teach a reader something genuinely useful
- Each section earns its place — no filler paragraphs
"""

    input_data = f"""
### INPUT DATA:
**Project Name**: {project_name}
**Repository**: {github_url}
**Primary Language**: {metadata.primary_language}
**Project Type**: {metadata.project_type}
**Tech Stack**: {', '.join(metadata.tech_stack)}
**Frameworks**: {', '.join(metadata.frameworks) if metadata.frameworks else 'None detected'}

**EXISTING README** (for context):
<existing_readme>
{existing_readme[:2_000] if existing_readme else "No existing README found"}
</existing_readme>

**PROJECT FILES**:
<source_code>
{file_contents[:80_000]}
</source_code>

{user_preferences}

Now write the article.
"""

    return f"{system_context}\n{example}\n{instructions}\n{input_data}"


# ---------------------------------------------------------------------------
# Resume Bullet Points
# ---------------------------------------------------------------------------

def build_resume_prompt(
    project_name: str,
    github_url: str,
    file_contents: str,
    existing_readme: str,
    metadata: ProjectMetadata,
    role_target: str = "Software Engineer",
    seniority: str = "mid",
    num_bullets: int = 5,
    include_metrics: bool = True,
    user_preferences: str = "",
) -> str:
    """Build a prompt that generates ATS-optimised resume bullet points."""

    metrics_instruction = ""
    if include_metrics:
        metrics_instruction = (
            "Where possible, include QUANTIFIABLE METRICS (e.g., number of API endpoints, "
            "files processed, concurrent users supported). If exact numbers aren't in the "
            "source code, make reasonable estimates based on codebase size and architecture, "
            "but keep them realistic."
        )

    seniority_guidance = {
        "intern": "Focus on learning and contributions. Verbs: 'Contributed', 'Assisted', 'Supported'.",
        "junior": "Emphasize feature implementation and technical skills. Verbs: 'Developed', 'Implemented', 'Built'.",
        "mid": "Highlight ownership and technical decisions. Verbs: 'Designed', 'Architected', 'Led', 'Optimized'.",
        "senior": "Showcase system design and leadership. Verbs: 'Architected', 'Spearheaded', 'Mentored', 'Drove'.",
        "staff": "Demonstrate strategic vision and cross-team influence. Verbs: 'Established', 'Pioneered', 'Influenced'.",
        "principal": "Emphasize company-wide strategy and innovation. Verbs: 'Defined', 'Pioneered', 'Evangelized'.",
    }

    seniority_context = seniority_guidance.get(seniority.lower(), seniority_guidance["mid"])

    system_context = (
        "You are a senior technical resume coach who has helped 500+ engineers land jobs "
        "at top tech companies. You write ATS-optimized bullet points that are specific, "
        "impactful, and tailored to the target role. Every bullet demonstrates a concrete "
        "technical contribution."
    )

    example = f"""
### EXAMPLE OUTPUT (for a mid-level Full Stack Engineer):

```json
{{
    "repo_description": "Full-stack task management platform with real-time collaboration, role-based access control, and automated workflow triggers",
    "bullets": [
        "Designed and implemented a real-time collaboration engine using WebSocket connections, supporting concurrent editing across 15+ task boards with sub-100ms latency",
        "Architected a role-based access control system with 4 permission tiers, securing 12 REST API endpoints and reducing unauthorized access incidents to zero",
        "Built an automated workflow trigger system processing 500+ daily task state transitions with configurable rules and Slack/email notification integration",
        "Optimized PostgreSQL query performance by implementing composite indexes and query batching, reducing average API response time from 800ms to 120ms",
        "Developed a responsive React dashboard with 8 interactive components, achieving 95+ Lighthouse performance score through code splitting and lazy loading"
    ],
    "skills_demonstrated": ["React", "Node.js", "PostgreSQL", "WebSocket", "REST API Design", "RBAC", "Performance Optimization"]
}}
```
"""

    instructions = f"""
### TASK:
Analyse this project's source code and generate resume-ready content.

### TARGET ROLE: {role_target}
### SENIORITY LEVEL: {seniority.upper()}

### SENIORITY GUIDANCE:
{seniority_context}

### REQUIREMENTS:
1. Generate exactly {num_bullets} bullet points for the experience/projects section.
2. Generate a 1-sentence project description for a resume header.
3. Extract demonstrated technical skills from the codebase.

### BULLET POINT RULES:
- Start each bullet with a STRONG ACTION VERB appropriate for {seniority.upper()} level.
- Each bullet: 1-2 lines (15-25 words ideal).
- Focus on IMPACT and COMPLEXITY appropriate for {seniority.upper()} {role_target}.
- {metrics_instruction if include_metrics else "Focus on technical complexity and scope."}
- Do NOT use first person (no "I" or "my").
- Every bullet must be backed by actual code in the source files.

### OUTPUT FORMAT:
Return ONLY a valid JSON object — no markdown wrapping, no commentary:
{{
    "repo_description": "One sentence describing the project",
    "bullets": ["First bullet...", "Second bullet..."],
    "skills_demonstrated": ["Skill1", "Skill2"]
}}

### SELF-VERIFICATION:
Before outputting, check:
- Every bullet references something actually in the codebase
- Metrics are realistic and defensible in an interview
- Skills listed match technologies actually used in the project
- The JSON is valid and parseable
"""

    input_data = f"""
### INPUT DATA:
**Project Name**: {project_name}
**Repository**: {github_url}
**Primary Language**: {metadata.primary_language}
**Project Type**: {metadata.project_type}
**Tech Stack**: {', '.join(metadata.tech_stack)}
**Frameworks**: {', '.join(metadata.frameworks) if metadata.frameworks else 'None detected'}

**EXISTING README** (for context):
<existing_readme>
{existing_readme[:2_000] if existing_readme else "No existing README found"}
</existing_readme>

**PROJECT FILES**:
<source_code>
{file_contents[:60_000]}
</source_code>

{user_preferences}

Now generate the resume content as JSON.
"""

    return f"{system_context}\n{example}\n{instructions}\n{input_data}"
