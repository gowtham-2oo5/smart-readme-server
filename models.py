from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

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
