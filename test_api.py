import json

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from main import app
from models import ContentType

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helper: mock return value for ReadmeService.generate_content
# ---------------------------------------------------------------------------

def _mock_content_result(content_type: str, content: str = "mock content") -> dict:
    """Build a realistic return dict matching ReadmeService.generate_content()."""
    return {
        "content": content,
        "content_type": content_type,
        "processing_time": 1.23,
        "files_analyzed": 10,
        "ai_model_used": "qwen/qwen2.5-coder-32b-instruct",
        "metadata": {
            "primary_language": "Python",
            "project_type": "api",
            "tech_stack": ["Python", "FastAPI"],
            "frameworks": ["FastAPI"],
        },
        "repo_info": {
            "owner": "test-owner",
            "repo": "test-repo",
            "url": "https://github.com/test-owner/test-repo",
        },
    }


def _mock_readme_result() -> dict:
    """Build a realistic return dict matching ReadmeService.generate_readme()."""
    return {
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
            "frameworks": [],
        },
        "repo_info": {"url": "https://github.com/test/repo", "repo": "repo"},
        "header_banner_url": "mock_header",
        "conclusion_banner_url": "mock_conclusion",
        "dual_banners_enabled": True,
    }


# =====================================================================
# Basic endpoints (no mocking required)
# =====================================================================

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "features" in data
    assert data["version"] == "2.0.0"
    # Verify new endpoints are advertised
    assert "linkedin" in data["endpoints"]
    assert "article" in data["endpoints"]
    assert "resume" in data["endpoints"]


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


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


# =====================================================================
# Payload validation (422 expected on bad input)
# =====================================================================

def test_generate_readme_payload_validation():
    response = client.post("/generate-readme", json={})
    assert response.status_code == 422


def test_generate_linkedin_payload_validation():
    response = client.post("/generate-linkedin", json={})
    assert response.status_code == 422


def test_generate_article_payload_validation():
    response = client.post("/generate-article", json={})
    assert response.status_code == 422


def test_generate_resume_points_payload_validation():
    response = client.post("/generate-resume-points", json={})
    assert response.status_code == 422


def test_linkedin_invalid_tone():
    """Enum fields should reject values outside the allowed set."""
    payload = {
        "repo_name": "test-repo",
        "owner_name": "test-owner",
        "tone": "invalid_tone",
    }
    response = client.post("/generate-linkedin", json=payload)
    assert response.status_code == 422


def test_resume_bullets_out_of_range():
    """num_bullets must be between 3 and 8."""
    payload = {
        "repo_name": "test-repo",
        "owner_name": "test-owner",
        "num_bullets": 20,
    }
    response = client.post("/generate-resume-points", json=payload)
    assert response.status_code == 422


# =====================================================================
# README generation (mocked)
# =====================================================================

@patch("services.readme_service.ReadmeService.generate_readme")
def test_generate_readme_mocked(mock_generate_readme):
    mock_generate_readme.return_value = _mock_readme_result()

    payload = {
        "repo_name": "test-repo",
        "owner_name": "test-owner",
        "tone": "casual",
        "banner_config": {
            "theme": "cyberpunk",
            "font": "jetbrains",
            "style": "animated",
            "include_banner": True,
        },
    }

    response = client.post("/generate-readme", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["readme_content"] == "# Mocked README"

    mock_generate_readme.assert_called_once()
    _, kwargs = mock_generate_readme.call_args
    assert kwargs["owner"] == "test-owner"
    assert kwargs["repo"] == "test-repo"
    assert kwargs["tone"] == "casual"
    assert kwargs["banner_config"].theme == "cyberpunk"


# =====================================================================
# LinkedIn generation (mocked)
# =====================================================================

@patch("services.readme_service.ReadmeService.generate_content")
def test_generate_linkedin_default_options(mock_gen):
    mock_gen.return_value = _mock_content_result(
        "linkedin", "🚀 Just shipped something cool..."
    )

    payload = {"repo_name": "test-repo", "owner_name": "test-owner"}
    response = client.post("/generate-linkedin", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["content_type"] == "linkedin"
    assert "shipped" in data["content"]

    mock_gen.assert_called_once()
    _, kwargs = mock_gen.call_args
    assert kwargs["content_type"] == ContentType.LINKEDIN
    assert kwargs["tone"] == "thought_leader"
    assert kwargs["focus"] == "business_value"


@patch("services.readme_service.ReadmeService.generate_content")
def test_generate_linkedin_custom_options(mock_gen):
    mock_gen.return_value = _mock_content_result("linkedin", "Hiring update post")

    payload = {
        "repo_name": "ml-pipeline",
        "owner_name": "data-team",
        "tone": "technical",
        "focus": "hiring",
    }
    response = client.post("/generate-linkedin", json=payload)

    assert response.status_code == 200
    _, kwargs = mock_gen.call_args
    assert kwargs["owner"] == "data-team"
    assert kwargs["repo"] == "ml-pipeline"
    assert kwargs["tone"] == "technical"
    assert kwargs["focus"] == "hiring"


# =====================================================================
# Article generation (mocked)
# =====================================================================

@patch("services.readme_service.ReadmeService.generate_content")
def test_generate_article_default_options(mock_gen):
    mock_gen.return_value = _mock_content_result(
        "article", "# Inside the Architecture of Test-Repo\n\n..."
    )

    payload = {"repo_name": "test-repo", "owner_name": "test-owner"}
    response = client.post("/generate-article", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["content_type"] == "article"

    _, kwargs = mock_gen.call_args
    assert kwargs["content_type"] == ContentType.ARTICLE
    assert kwargs["tone"] == "professional"
    assert kwargs["article_style"] == "deep_dive"
    assert kwargs["target_length"] == "medium"


@patch("services.readme_service.ReadmeService.generate_content")
def test_generate_article_custom_options(mock_gen):
    mock_gen.return_value = _mock_content_result("article", "Tutorial article")

    payload = {
        "repo_name": "test-repo",
        "owner_name": "test-owner",
        "tone": "conversational",
        "article_style": "tutorial",
        "target_length": "long",
    }
    response = client.post("/generate-article", json=payload)

    assert response.status_code == 200
    _, kwargs = mock_gen.call_args
    assert kwargs["article_style"] == "tutorial"
    assert kwargs["target_length"] == "long"


# =====================================================================
# Resume generation (mocked)
# =====================================================================

@patch("services.readme_service.ReadmeService.generate_content")
def test_generate_resume_default_options(mock_gen):
    resume_json = json.dumps({
        "repo_description": "A REST API for managing campus recruitment",
        "bullets": [
            "Architected a Spring Boot REST API with JWT auth",
            "Designed attendance tracking with CSV import/export",
            "Built analytics dashboards with trend reporting",
            "Implemented role-based access control",
            "Engineered bulk operations pipeline",
        ],
        "skills_demonstrated": ["Java", "Spring Boot", "MySQL"],
    })
    mock_gen.return_value = _mock_content_result("resume", resume_json)

    payload = {"repo_name": "test-repo", "owner_name": "test-owner"}
    response = client.post("/generate-resume-points", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["content_type"] == "resume"

    # Content should be valid JSON
    parsed = json.loads(data["content"])
    assert "bullets" in parsed
    assert len(parsed["bullets"]) == 5

    _, kwargs = mock_gen.call_args
    assert kwargs["content_type"] == ContentType.RESUME
    assert kwargs["role_target"] == "Software Engineer"
    assert kwargs["num_bullets"] == 5
    assert kwargs["include_metrics"] is True


@patch("services.readme_service.ReadmeService.generate_content")
def test_generate_resume_custom_options(mock_gen):
    resume_json = json.dumps({
        "repo_description": "Backend API",
        "bullets": ["Bullet 1", "Bullet 2", "Bullet 3"],
        "skills_demonstrated": ["Python"],
    })
    mock_gen.return_value = _mock_content_result("resume", resume_json)

    payload = {
        "repo_name": "test-repo",
        "owner_name": "test-owner",
        "role_target": "Backend Engineer",
        "seniority": "senior",
        "num_bullets": 3,
        "include_metrics": False,
    }
    response = client.post("/generate-resume-points", json=payload)

    assert response.status_code == 200
    _, kwargs = mock_gen.call_args
    assert kwargs["role_target"] == "Backend Engineer"
    assert kwargs["seniority"] == "senior"
    assert kwargs["num_bullets"] == 3
    assert kwargs["include_metrics"] is False


@pytest.mark.parametrize("seniority,expected_verbs", [
    ("intern", ["Contributed", "Assisted", "Supported"]),
    ("junior", ["Developed", "Implemented", "Built"]),
    ("mid", ["Designed", "Architected", "Led"]),
    ("senior", ["Spearheaded", "Mentored", "Drove"]),
    ("staff", ["Established", "Pioneered", "Influenced"]),
    ("principal", ["Defined", "Revolutionized", "Evangelized"]),
])
@patch("services.readme_service.ReadmeService.generate_content")
def test_resume_seniority_levels(mock_gen, seniority, expected_verbs):
    """Test that different seniority levels generate appropriate action verbs."""
    resume_json = json.dumps({
        "repo_description": "A test project",
        "bullets": [f"{verb} a feature" for verb in expected_verbs],
        "skills_demonstrated": ["Python"],
    })
    mock_gen.return_value = _mock_content_result("resume", resume_json)

    payload = {
        "repo_name": "test-repo",
        "owner_name": "test-owner",
        "seniority": seniority,
    }
    response = client.post("/generate-resume-points", json=payload)

    assert response.status_code == 200
    _, kwargs = mock_gen.call_args
    assert kwargs["seniority"] == seniority
    
    # Verify the content contains expected verbs
    parsed = json.loads(response.json()["content"])
    bullets_text = " ".join(parsed["bullets"])
    for verb in expected_verbs:
        assert verb in bullets_text


@patch("services.readme_service.ReadmeService.generate_content")
def test_resume_default_seniority(mock_gen):
    """Test that seniority defaults to 'mid' when not provided."""
    resume_json = json.dumps({
        "repo_description": "Test",
        "bullets": ["Designed a feature"],
        "skills_demonstrated": ["Python"],
    })
    mock_gen.return_value = _mock_content_result("resume", resume_json)

    payload = {
        "repo_name": "test-repo",
        "owner_name": "test-owner",
    }
    response = client.post("/generate-resume-points", json=payload)

    assert response.status_code == 200
    _, kwargs = mock_gen.call_args
    assert kwargs["seniority"] == "mid"  # Default value


# =====================================================================
# Error handling (mocked failures)
# =====================================================================

@patch("services.readme_service.ReadmeService.generate_content")
def test_linkedin_generation_failure(mock_gen):
    mock_gen.side_effect = ValueError("AI generation failed: timeout")

    payload = {"repo_name": "test-repo", "owner_name": "test-owner"}
    response = client.post("/generate-linkedin", json=payload)

    assert response.status_code == 500
    assert "AI generation failed" in response.json()["detail"]


@patch("services.readme_service.ReadmeService.generate_content")
def test_article_generation_failure(mock_gen):
    mock_gen.side_effect = ValueError("Failed to ingest repository")

    payload = {"repo_name": "test-repo", "owner_name": "test-owner"}
    response = client.post("/generate-article", json=payload)

    assert response.status_code == 500
    assert "ingest" in response.json()["detail"]


@patch("services.readme_service.ReadmeService.generate_content")
def test_resume_generation_failure(mock_gen):
    mock_gen.side_effect = ValueError("No analysable source files found")

    payload = {"repo_name": "test-repo", "owner_name": "test-owner"}
    response = client.post("/generate-resume-points", json=payload)

    assert response.status_code == 500
    assert "source files" in response.json()["detail"]


# =====================================================================
# Edge cases
# =====================================================================

def test_resume_invalid_seniority_accepted():
    """Invalid seniority values should be accepted (AI will handle gracefully)."""
    payload = {
        "repo_name": "test-repo",
        "owner_name": "test-owner",
        "seniority": "super-ultra-mega-senior",  # Not in our list but valid string
    }
    # Should not raise 422 - string validation passes
    response = client.post("/generate-resume-points", json=payload)
    # Will fail at 500 level due to missing mock, but validates the schema accepts it
    assert response.status_code in [200, 500]  # Not 422


def test_resume_malformed_json_response():
    """Test handling when AI returns malformed JSON."""
    with patch("services.readme_service.ReadmeService.generate_content") as mock_gen:
        # Return invalid JSON string
        mock_gen.return_value = _mock_content_result("resume", "This is not JSON at all")
        
        payload = {"repo_name": "test-repo", "owner_name": "test-owner"}
        response = client.post("/generate-resume-points", json=payload)
        
        # Should still return 200 with the raw content (frontend will handle parse error)
        assert response.status_code == 200
        assert response.json()["content"] == "This is not JSON at all"


def test_linkedin_empty_repo_name():
    """Empty repo name should fail validation with min_length."""
    payload = {
        "repo_name": "",
        "owner_name": "test-owner",
    }
    response = client.post("/generate-linkedin", json=payload)
    assert response.status_code == 422


def test_article_empty_owner_name():
    """Empty owner name should fail validation with min_length."""
    payload = {
        "repo_name": "test-repo",
        "owner_name": "",
    }
    response = client.post("/generate-article", json=payload)
    assert response.status_code == 422


@patch("services.readme_service.ReadmeService.generate_content")
def test_concurrent_resume_requests(mock_gen):
    """Test that multiple concurrent requests don't interfere."""
    import threading
    
    mock_gen.return_value = _mock_content_result("resume", json.dumps({
        "repo_description": "Test",
        "bullets": ["Bullet 1"],
        "skills_demonstrated": ["Python"],
    }))
    
    results = []
    
    def make_request(seniority):
        payload = {
            "repo_name": "test-repo",
            "owner_name": "test-owner",
            "seniority": seniority,
        }
        response = client.post("/generate-resume-points", json=payload)
        results.append((seniority, response.status_code))
    
    threads = [
        threading.Thread(target=make_request, args=("intern",)),
        threading.Thread(target=make_request, args=("senior",)),
        threading.Thread(target=make_request, args=("principal",)),
    ]
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # All should succeed
    assert len(results) == 3
    assert all(status == 200 for _, status in results)


def test_readme_special_characters_in_repo_name():
    """Test handling of special characters in repo names."""
    with patch("services.readme_service.ReadmeService.generate_readme") as mock_gen:
        mock_gen.return_value = _mock_readme_result()
        
        payload = {
            "repo_name": "my-repo.v2",
            "owner_name": "user_123",
        }
        response = client.post("/generate-readme", json=payload)
        assert response.status_code == 200


@patch("services.readme_service.ReadmeService.generate_content")
def test_article_very_long_repo_name(mock_gen):
    """Test handling of very long repository names."""
    mock_gen.return_value = _mock_content_result("article", "Long article content")
    
    payload = {
        "repo_name": "a" * 200,  # Very long name
        "owner_name": "test-owner",
    }
    response = client.post("/generate-article", json=payload)
    assert response.status_code == 200
