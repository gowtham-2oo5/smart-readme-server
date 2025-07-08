from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from models import ReadmeRequest, ReadmeResponse, GeneratedReadme
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
        "endpoints": {
            "generate": "/generate-readme",
            "files": "/files"
        }
    }

@app.post("/generate-readme", response_model=ReadmeResponse)
async def generate_readme(request: ReadmeRequest):
    """Generate README for a GitHub repository using Gemini 2.5 Flash"""
    try:
        print(f"🚀 Received request: {request.owner_name}/{request.repo_name}")
        
        # Generate README using Gemini 2.5 Flash
        result = readme_service.generate_readme(
            owner=request.owner_name,
            repo=request.repo_name
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
