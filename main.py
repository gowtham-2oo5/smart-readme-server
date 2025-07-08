from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from models import ReadmeRequest, ReadmeResponse, GeneratedReadme, BannerConfig
from services.readme_service import ReadmeService
from services.file_service import FileService
import time

app = FastAPI(
    title="README Generator API",
    description="Generate comprehensive README files for GitHub repositories using Gemini 2.5 Flash",
    version="2.0.0"
)

readme_service = ReadmeService()
file_service = FileService()

@app.get("/")
async def root():
    return {
        "message": "README Generator API - Powered by Gemini 2.5 Flash",
        "version": "2.0.0",
        "ai_model": "gemini-2.5-flash",
        "features": {
            "professional_banners": "🎨 Animated typing banners with JetBrains Mono",
            "dark_themes": "🌙 Professional dark themes optimized for GitHub",
            "custom_fonts": "🔤 Multiple professional fonts available",
            "ai_generation": "🤖 AI-powered comprehensive README generation"
        },
        "endpoints": {
            "generate": "/generate-readme",
            "files": "/files",
            "banner_preview": "/banner-preview/{owner}/{repo}",
            "banner_options": "/banner-options"
        }
    }

@app.post("/generate-readme", response_model=ReadmeResponse)
async def generate_readme(request: ReadmeRequest):
    """Generate README for a GitHub repository using Gemini 2.5 Flash with professional banner"""
    try:
        print(f"🚀 Received request: {request.owner_name}/{request.repo_name}")
        
        # 🎨 Log banner configuration
        if request.banner_config and request.banner_config.include_banner:
            print(f"🎨 Banner config: {request.banner_config.style} style, {request.banner_config.font} font, {request.banner_config.theme} theme")
        
        # Generate README using Gemini 2.5 Flash with banner
        result = readme_service.generate_readme(
            owner=request.owner_name,
            repo=request.repo_name,
            banner_config=request.banner_config
        )
        
        return ReadmeResponse(
            success=True,
            data=result
        )
        
    except Exception as e:
        print(f"❌ Error generating README: {e}")
        return ReadmeResponse(
            success=False,
            error=str(e)
        )

@app.get("/files")
async def list_generated_files():
    """List all generated README files"""
    try:
        files = file_service.list_generated_readmes()
        return {
            "success": True,
            "files": files,
            "total_files": len(files)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/files/{file_name}")
async def get_file_content(file_name: str):
    """Get content of a specific README file"""
    try:
        file_path = f"./generated_readmes/{file_name}"
        content = file_service.read_readme(file_path)
        file_info = file_service.get_file_info(file_path)
        
        return {
            "success": True,
            "content": content,
            "file_info": file_info
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/banner-preview/{owner}/{repo}")
async def preview_banner(
    owner: str, 
    repo: str, 
    font: str = 'jetbrains',
    theme: str = 'github_dark',
    style: str = 'professional'
):
    """🎨 Preview DUAL professional banners for a repository"""
    try:
        print(f"🎨 Generating DUAL banner preview for {owner}/{repo}")
        
        # Get basic repo info
        repo_info = readme_service.github_service.get_repo_info(owner, repo)
        
        # Get repository structure for metadata analysis
        default_branch = readme_service.github_service.get_default_branch(owner, repo)
        repo_structure = readme_service.github_service.get_repo_structure(owner, repo, default_branch)
        source_files = readme_service.github_service.fetch_source_files(owner, repo, repo_structure, default_branch)
        
        # Analyze metadata with fallback
        try:
            if source_files:
                metadata = readme_service._analyze_project_metadata(source_files, repo_structure)
            else:
                raise Exception("No source files found")
        except Exception as e:
            print(f"⚠️ Using fallback metadata: {e}")
            # Fallback metadata
            metadata = ProjectMetadata(
                primary_language="Python",
                project_type="api", 
                tech_stack=["Python"],
                frameworks=[]
            )
        
        # Generate DUAL banners with error handling
        try:
            header_banner_url, conclusion_banner_url = readme_service.banner_service.generate_dual_banners(
                repo_info=repo_info,
                metadata=metadata,
                font=font,
                theme=theme,
                style=style
            )
        except Exception as e:
            print(f"❌ Banner generation failed: {e}")
            return {"success": False, "error": f"Banner generation failed: {str(e)}"}
        
        # Generate preview HTML for both banners
        try:
            header_preview = readme_service.banner_service.get_banner_preview_html(
                header_banner_url, f"Header - {style.title()} Capsule Banner"
            )
            conclusion_preview = readme_service.banner_service.get_banner_preview_html(
                conclusion_banner_url, "Conclusion - Typing SVG Banner"
            )
        except Exception as e:
            print(f"⚠️ Preview HTML generation failed: {e}")
            header_preview = f'<img src="{header_banner_url}" alt="Header Banner">'
            conclusion_preview = f'<img src="{conclusion_banner_url}" alt="Conclusion Banner">'
        
        return {
            "success": True,
            "dual_banners": {
                "header": {
                    "url": header_banner_url,
                    "type": "Capsule Render",
                    "preview_html": header_preview
                },
                "conclusion": {
                    "url": conclusion_banner_url,
                    "type": "Typing SVG",
                    "preview_html": conclusion_preview
                }
            },
            "metadata": {
                "primary_language": metadata.primary_language,
                "tech_stack": metadata.tech_stack,
                "project_type": metadata.project_type
            },
            "config": {
                "font": font,
                "theme": theme,
                "style": style
            }
        }
        
    except Exception as e:
        print(f"❌ Banner preview error: {e}")
        return {"success": False, "error": str(e)}

@app.get("/banner-options")
async def get_banner_options():
    """🎨 Get available banner configuration options"""
    try:
        return {
            "success": True,
            "options": {
                "fonts": readme_service.banner_service.get_supported_fonts(),
                "themes": readme_service.banner_service.get_supported_themes(),
                "styles": {
                    "professional": "Multi-line professional banner with tech stack",
                    "animated": "Single-line animated banner with neon effects", 
                    "minimal": "Clean minimal banner with essential info"
                }
            },
            "defaults": {
                "font": "jetbrains",
                "theme": "github_dark",
                "style": "professional"
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/files/{file_name}")
async def delete_file(file_name: str):
    """Delete a generated README file"""
    try:
        file_path = f"./generated_readmes/{file_name}"
        success = file_service.delete_readme(file_path)
        
        if success:
            return {"success": True, "message": f"File {file_name} deleted successfully"}
        else:
            return {"success": False, "error": "File not found"}
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
