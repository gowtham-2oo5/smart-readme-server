"""
Prompt templates for each content generation type.

Each builder receives a standardised `RepoContext` dict (from the shared
retrieval pipeline) and content-type-specific options, then returns a
fully-assembled prompt string ready for the AI service.
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
            "and the measurable impact (users served, time saved, processes automated). "
            "Translate technical features into business outcomes."
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

    instructions = f"""
### TASK:
Write a LinkedIn post announcing/showcasing this project. The post should feel authentic
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
10. Output ONLY the post text. No commentary, no wrapping.
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

Now write the LinkedIn post.
"""

    return f"{system_context}\n\n{instructions}\n\n{input_data}"


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
        "You are a senior technical writer who publishes on platforms like Medium, Dev.to, "
        "and Hashnode. Your articles are known for being deeply technical yet highly readable, "
        f"with a {tone} tone. You explain complex concepts with clarity and always back "
        "claims with concrete code examples from the actual project."
    )

    style_instruction = style_guide.get(article_style, style_guide["deep_dive"]).format(
        project_name=project_name
    )

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
4. **Code Snippets**: Include 3-5 relevant code snippets from the actual project files. Always specify the language in fenced code blocks.
5. **Architecture**: Include at least one section explaining the system architecture or data flow.
6. **Lessons Learned**: End with 3-5 concrete, specific takeaways (not generic advice).
7. **Conclusion**: End with a summary and link to the repository.
8. **Output raw markdown**. Do NOT wrap in ```markdown blocks.
9. Do NOT include a scratchpad or reasoning block — output the article directly.
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

Now write the article.
"""

    return f"{system_context}\n\n{instructions}\n\n{input_data}"


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
) -> str:
    """Build a prompt that generates ATS-optimised resume bullet points."""

    metrics_instruction = ""
    if include_metrics:
        metrics_instruction = (
            "Where possible, include QUANTIFIABLE METRICS (e.g., number of API endpoints, "
            "files processed, concurrent users supported, response time improvements). "
            "If exact numbers aren't in the source code, make reasonable estimates based "
            "on the codebase size and architecture, but keep them realistic."
        )

    # Seniority-specific guidance
    seniority_guidance = {
        "intern": "Focus on learning, contributions to team projects, and foundational technical skills. Use verbs like 'Contributed', 'Assisted', 'Learned', 'Supported'.",
        "junior": "Emphasize feature implementation, bug fixes, and growing technical skills. Use verbs like 'Developed', 'Implemented', 'Fixed', 'Built'.",
        "mid": "Highlight ownership of features/modules, technical decisions, and cross-functional collaboration. Use verbs like 'Designed', 'Architected', 'Led', 'Optimized'.",
        "senior": "Showcase system design, technical leadership, mentorship, and business impact. Use verbs like 'Architected', 'Spearheaded', 'Mentored', 'Drove'.",
        "staff": "Demonstrate strategic technical vision, cross-team influence, and organizational impact. Use verbs like 'Established', 'Pioneered', 'Influenced', 'Transformed'.",
        "principal": "Emphasize company-wide technical strategy, innovation, and industry leadership. Use verbs like 'Defined', 'Pioneered', 'Evangelized', 'Revolutionized'.",
    }
    
    seniority_context = seniority_guidance.get(seniority.lower(), seniority_guidance["mid"])

    system_context = (
        "You are a senior technical resume coach who has helped 500+ engineers land jobs "
        "at top tech companies. You write ATS-optimized bullet points that are specific, "
        "impactful, and tailored to the target role. You NEVER write generic filler — "
        "every bullet point demonstrates a concrete technical contribution."
    )

    instructions = f"""
### TASK:
Analyse this project's source code and generate resume-ready content.

### TARGET ROLE: {role_target}
### SENIORITY LEVEL: {seniority.upper()}

### SENIORITY GUIDANCE:
{seniority_context}

### REQUIREMENTS:
1. Generate exactly {num_bullets} bullet points for the experience/projects section of a resume.
2. Generate a 1-sentence project description suitable for a resume header.
3. Extract a list of demonstrated technical skills from the codebase.

### BULLET POINT RULES:
- Start each bullet with a STRONG ACTION VERB appropriate for {seniority.upper()} level.
- Each bullet should be 1-2 lines long (15-25 words ideal).
- Focus on IMPACT and COMPLEXITY appropriate for a {seniority.upper()} {role_target}.
- {metrics_instruction if include_metrics else "Focus on the technical complexity and scope."}
- Tailor the language and emphasis to a **{role_target}** position at **{seniority.upper()}** level.
- Do NOT use first person (no "I" or "my").

### OUTPUT FORMAT:
Return ONLY a valid JSON object with this exact structure (no markdown wrapping, no commentary):
{{
    "repo_description": "One sentence describing the project for a resume header",
    "bullets": [
        "First bullet point...",
        "Second bullet point..."
    ],
    "skills_demonstrated": ["Skill1", "Skill2", "Skill3"]
}}
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

Now generate the resume content as JSON.
"""

    return f"{system_context}\n\n{instructions}\n\n{input_data}"
