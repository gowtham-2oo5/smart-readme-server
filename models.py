from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ContentType(str, Enum):
    README = "readme"
    LINKEDIN = "linkedin"
    ARTICLE = "article"
    RESUME = "resume"


class LinkedInTone(str, Enum):
    THOUGHT_LEADER = "thought_leader"
    CASUAL = "casual"
    TECHNICAL = "technical"


class LinkedInFocus(str, Enum):
    BUSINESS_VALUE = "business_value"
    TECHNICAL = "technical"
    HIRING = "hiring"


class ArticleStyle(str, Enum):
    TUTORIAL = "tutorial"
    DEEP_DIVE = "deep_dive"
    CASE_STUDY = "case_study"


class ArticleLength(str, Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class BannerConfig(BaseModel):
    """🎨 Banner configuration for README generation"""
    model_config = ConfigDict(extra="ignore")

    include_banner: bool = Field(default=True, description="Whether to include banners")
    font: str = Field(default="jetbrains", description="Font choice (e.g., jetbrains, fira, roboto)")
    theme: str = Field(default="github_dark", description="Visual theme for the banner")
    style: str = Field(default="professional", description="Style of the banner (professional, animated, minimal)")
    custom_title: Optional[str] = Field(default=None, description="Optional custom title to display in the banner")

class ReadmeRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    repo_name: str = Field(..., description="Name of the GitHub repository")
    owner_name: str = Field(..., description="Owner of the GitHub repository")
    tone: str = Field(default="professional", description="Tone of the README (e.g., professional, casual, developer, instructional)")
    banner_config: BannerConfig = Field(default_factory=BannerConfig, description="Banner customization settings")

class ProjectMetadata(BaseModel):
    model_config = ConfigDict(extra="ignore")

    primary_language: str
    project_type: str
    tech_stack: List[str]
    frameworks: List[str]

class ReadmeResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class GeneratedReadme(BaseModel):
    model_config = ConfigDict(extra="ignore")

    readme_content: str
    readme_length: int
    local_file_path: str
    processing_time: float
    files_analyzed: int
    ai_model_used: str
    branch_used: str
    metadata: ProjectMetadata
    repo_info: Dict[str, str]


# ---------------------------------------------------------------------------
# New Content-Type Requests
# ---------------------------------------------------------------------------

class LinkedInRequest(BaseModel):
    """Request model for LinkedIn post generation."""
    model_config = ConfigDict(extra="ignore")

    repo_name: str = Field(..., description="Name of the GitHub repository")
    owner_name: str = Field(..., description="Owner of the GitHub repository")
    tone: LinkedInTone = Field(default=LinkedInTone.THOUGHT_LEADER, description="Tone of the LinkedIn post")
    focus: LinkedInFocus = Field(default=LinkedInFocus.BUSINESS_VALUE, description="Focus area of the post")


class ArticleRequest(BaseModel):
    """Request model for technical article generation."""
    model_config = ConfigDict(extra="ignore")

    repo_name: str = Field(..., description="Name of the GitHub repository")
    owner_name: str = Field(..., description="Owner of the GitHub repository")
    tone: str = Field(default="professional", description="Tone (professional, conversational, academic)")
    article_style: ArticleStyle = Field(default=ArticleStyle.DEEP_DIVE, description="Style of the article")
    target_length: ArticleLength = Field(default=ArticleLength.MEDIUM, description="Target length of the article")


class ResumeRequest(BaseModel):
    """Request model for resume bullet point generation."""
    model_config = ConfigDict(extra="ignore")

    repo_name: str = Field(..., description="Name of the GitHub repository")
    owner_name: str = Field(..., description="Owner of the GitHub repository")
    role_target: str = Field(default="Software Engineer", description="Target role to tailor bullets for")
    num_bullets: int = Field(default=5, ge=3, le=8, description="Number of bullet points to generate")
    include_metrics: bool = Field(default=True, description="Include quantifiable metrics in bullets")


class ContentResponse(BaseModel):
    """Unified response for all content generation endpoints."""
    model_config = ConfigDict(extra="ignore")

    success: bool
    content_type: ContentType
    content: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
