from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from models import ReadmeRequest, ReadmeResponse, GeneratedReadme
from services.readme_service import ReadmeService
from services.file_service import FileService
import time

app = FastAPI(
    title="README Generator API",
    description="Generate comprehensive README files for GitHub repositories using various AI models",
    version="1.0.0"
)

readme_service = ReadmeService()
file_service = FileService()

@app.get("/")
async def root():
    return {
        "message": "README Generator API",
        "version": "1.0.0",
        "supported_models": readme_service.get_supported_models(),
        "endpoints": {
            "generate": "/generate-readme",
            "models": "/models",
            "files": "/files"
        }
    }

@app.get("/models")
async def get_supported_models():
    """Get list of supported AI models"""
    return {
        "supported_models": readme_service.get_supported_models(),
        "default_model": "gemini"
    }

@app.post("/generate-readme", response_model=ReadmeResponse)
async def generate_readme(request: ReadmeRequest):
    """Generate README for a GitHub repository"""
    try:
        print(f"🚀 Received request: {request.owner_name}/{request.repo_name} with {request.ai_model}")
        
        # Validate AI model
        if request.ai_model not in readme_service.get_supported_models():
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported AI model: {request.ai_model}. Supported models: {readme_service.get_supported_models()}"
            )
        
        # Generate README
        result = readme_service.generate_readme(
            owner=request.owner_name,
            repo=request.repo_name,
            ai_model=request.ai_model
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
