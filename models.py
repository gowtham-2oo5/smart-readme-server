from pydantic import BaseModel
from typing import Dict, List, Optional

class BannerConfig(BaseModel):
    """🎨 Banner configuration for README generation"""
    include_banner: bool = True
    font: str = 'jetbrains'  # jetbrains, fira, source, roboto, inter, poppins
    theme: str = 'github_dark'  # github_dark, midnight, cyberpunk, obsidian, matrix, neon, carbon
    style: str = 'professional'  # professional, animated, minimal
    custom_title: Optional[str] = None

class ReadmeRequest(BaseModel):
    repo_name: str
    owner_name: str
    banner_config: Optional[BannerConfig] = BannerConfig()

class ProjectMetadata(BaseModel):
    primary_language: str
    project_type: str
    tech_stack: List[str]
    frameworks: List[str]

class ReadmeResponse(BaseModel):
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None

class GeneratedReadme(BaseModel):
    readme_content: str
    readme_length: int
    local_file_path: str
    processing_time: float
    files_analyzed: int
    ai_model_used: str
    branch_used: str
    metadata: ProjectMetadata
    repo_info: Dict[str, str]
