from pydantic import BaseModel
from typing import Dict, List, Optional

class ReadmeRequest(BaseModel):
    repo_name: str
    owner_name: str

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
