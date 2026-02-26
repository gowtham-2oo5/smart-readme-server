import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "features" in response.json()
    assert response.json()["version"] == "2.0.0"

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "2.0.0", "ai_model": "qwen/qwen2.5-coder-32b-instruct"}

def test_get_models():
    response = client.get("/models")
    assert response.status_code == 200
    data = response.json()
    assert "supported_models" in data
    assert "default_model" in data

def test_banner_options():
    response = client.get("/banner-options")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "fonts" in data["options"]
    assert "themes" in data["options"]

def test_generate_readme_payload_validation():
    # Test missing payload
    response = client.post("/generate-readme", json={})
    assert response.status_code == 422 # Validation Error

    # Test invalid tone (string is accepted, just arbitrary)
    payload = {
        "repo_name": "test-repo",
        "owner_name": "test-owner",
        "tone": "casual"
    }
    # This might fail at the generation stage if we don't mock the service,
    # but let's mock the service to just return a dummy response.

@patch('services.readme_service.ReadmeService.generate_readme')
def test_generate_readme_mocked(mock_generate_readme):
    # Mock the return value of the generation
    mock_generate_readme.return_value = {
        "readme_content": "# Mocked README",
        "readme_length": 15,
        "local_file_path": "./generated_readmes/mocked.md",
        "processing_time": 0.5,
        "files_analyzed": 5,
        "ai_model_used": "mocked-model",
        "branch_used": "main",
        "metadata": {
            "primary_language": "Python",
            "project_type": "api",
            "tech_stack": ["Python"],
            "frameworks": []
        },
        "repo_info": {"url": "https://github.com/test/repo", "repo": "repo"},
        "header_banner_url": "mock_header",
        "conclusion_banner_url": "mock_conclusion",
        "dual_banners_enabled": True
    }
    
    payload = {
        "repo_name": "test-repo",
        "owner_name": "test-owner",
        "tone": "casual",
        "banner_config": {
            "theme": "cyberpunk",
            "font": "jetbrains",
            "style": "animated",
            "include_banner": True
        }
    }
    
    response = client.post("/generate-readme", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["readme_content"] == "# Mocked README"
    
    # ensure it was called with tone
    mock_generate_readme.assert_called_once()
    args, kwargs = mock_generate_readme.call_args
    assert kwargs["owner"] == "test-owner"
    assert kwargs["repo"] == "test-repo"
    assert kwargs["tone"] == "casual"
    assert kwargs["banner_config"].theme == "cyberpunk"
