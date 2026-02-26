# Smart README Generator - API Documentation 🚀

Welcome to the API documentation for the **Smart README Generator**. This guide is designed for the frontend team to understand how to interact with the API, construct properly serialized requests, and configure the visual presentation (banners, fonts, themes, and tone).

---

## 🔗 Base URL
`http://127.0.0.1:8000` (Local Development)

---

## 📚 Endpoints

### 1. Generate README (`POST /generate-readme`)
Generates a comprehensive `README.md` for a given GitHub repository using the specified aesthetic and tonal configurations.

**Request Body (`application/json`)**
The request body perfectly maps to the `ReadmeRequest` Pydantic model.

| Field | Type | Required | Default | Description |
| ---- | ---- | -------- | ------- | ----------- |
| `repo_name` | `string` | **Yes** | | The name of the GitHub repository. |
| `owner_name` | `string` | **Yes** | | The owner (user/organisation) of the repository. |
| `tone` | `string` | No | `"professional"` | The stylistic tone the AI should use (e.g., `"casual"`, `"developer"`, `"academic"`, `"humorous"`). |
| `banner_config` | `object` | No | *See below* | Defines the styling of the generated banners. |

**`banner_config` Object Structure**

| Field | Type | Required | Default | Description |
| ---- | ---- | -------- | ------- | ----------- |
| `include_banner` | `boolean` | No | `true` | Whether to include header/conclusion banners. |
| `font` | `string` | No | `"jetbrains"` | The font family. Valid options: `"jetbrains"`, `"default"`. |
| `theme` | `string` | No | `"github_dark"` | The color palette. *See Available Themes below.* |
| `style` | `string` | No | `"professional"` | The banner shape/animation. *See Available Styles below.* |
| `custom_title` | `string` | No | `null` | Optional explicit title to display in the banner. |

**Example Request:**
```json
{
  "owner_name": "gowtham-2oo5",
  "repo_name": "smart-readme-server",
  "tone": "developer",
  "banner_config": {
    "include_banner": true,
    "font": "jetbrains",
    "theme": "cyberpunk",
    "style": "animated"
  }
}
```

**Example Response (`200 OK`)**
```json
{
  "success": true,
  "data": {
    "readme_content": "# Smart README\\n...",
    "readme_length": 5200,
    "local_file_path": "./generated_readmes/...",
    "processing_time": 12.4,
    "files_analyzed": 14,
    "ai_model_used": "qwen/qwen2.5-coder-32b-instruct",
    "branch_used": "main",
    "metadata": {
      "primary_language": "Python",
      "project_type": "api",
      "tech_stack": ["Python", "FastAPI"],
      "frameworks": ["FastAPI"]
    },
    ...
  }
}
```

---

### 2. Get Banner Configuration Options (`GET /banner-options`)
Fetches all supported configurations explicitly from the server instance.

**Example Response (`200 OK`)**
```json
{
  "success": true,
  "options": {
    "fonts": {
      "jetbrains": "JetBrains Mono",
      "default": "Default Font"
    },
    "themes": {
      "midnight": "0:0f0f23,100:1a1a2e",
      "cyberpunk": "0:0f3460,100:16213e",
      "obsidian": "0:1e1e1e,100:2d2d2d",
      "github_dark": "0:0d1117,100:21262d",
      "matrix": "0:0a0a0a,100:1a1a1a",
      "neon": "0:0f0f23,100:1a1a2e",
      "carbon": "0:161618,100:23252a"
    },
    "styles": {
      "professional": "Multi-line professional banner with tech stack (Soft capsule)",
      "animated": "Single-line animated banner with neon effects (Waving capsule)",
      "minimal": "Clean minimal banner with essential info (Rectangular)"
    }
  },
  "defaults": {
    "font": "jetbrains",
    "theme": "github_dark",
    "style": "professional"
  }
}
```

---

### 3. Preview Banner (`GET /banner-preview/{owner}/{repo}`)
Returns the banner image URLs and their raw HTML for previewing on the frontend prior to README generation. **Query Parameters** map identically to the `banner_config` options (e.g., `?font=jetbrains&theme=matrix&style=minimal`).

---

## 🎨 Configuration Values Reference

### Tones
The `tone` property accepts a string. Here are highly recommended tones to offer users on the frontend:
- **`professional`** (Default): Clinical, precise, structured (Great for corporate/enterprise).
- **`casual`**: Friendly, easy-to-read, using basic analogies.
- **`developer`**: Highly technical, focused on architecture, patterns, and code configuration.
- **`instructional`**: Perfect for tutorials or educational repos, very step-by-step focused.
- **`academic`**: Suitable for research or data-science papers.

### Themes (Color Palettes)
Pass these text values under `banner_config -> theme`.
- `midnight`
- `cyberpunk`
- `obsidian`
- `github_dark` (Default)
- `matrix`
- `neon`
- `carbon`

### Styles (Banner Animation/Shape)
Pass these text values under `banner_config -> style`.
- `professional`: Traditional rounded (Soft) capsule banner, includes descriptions.
- `animated`: Waving wave effect at the bottom of the banner. 
- `minimal`: A strict, clean rectangular banner with no fuss.

### Fonts
Pass these text values under `banner_config -> font`.
- `jetbrains`: Recommended. Perfect for code.
- `default`: Native browser font.

---

## 🛡️ Error Handling
The API returns straightforward standard HTTP status codes:
- `422 Unprocessable Entity`: The request body structure or types are invalid (e.g., `owner_name` is missing).
- `500 Internal Server Error`: Thrown when AI service fails, hitting rate limits, or failing repository pulls. Check the `detail` property in the response body.
