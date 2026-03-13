# Smart README Generator — API Documentation 🚀

**Base URL:** `http://127.0.0.1:8000`

---

## Endpoints Overview

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| `POST` | `/generate-readme` | Generate a README.md |
| `POST` | `/generate-linkedin` | Generate a LinkedIn announcement post |
| `POST` | `/generate-article` | Generate a technical article |
| `POST` | `/generate-resume-points` | Generate resume bullet points (returns JSON) |
| `GET` | `/banner-options` | List available banner config options |
| `GET` | `/banner-preview/{owner}/{repo}` | Preview banners (query params: `font`, `theme`, `style`) |
| `GET` | `/files` | List saved READMEs |
| `GET` | `/files/{name}` | Read a saved README |
| `DELETE`| `/files/{name}` | Delete a saved README |
| `GET` | `/health` | Health check |
| `GET` | `/models` | List AI models |

---

## `POST /generate-readme`

```json
{
  "owner_name": "gowtham-2oo5",
  "repo_name": "CRT_Portal-server",
  "tone": "professional",
  "banner_config": {
    "include_banner": true,
    "font": "jetbrains",
    "theme": "github_dark",
    "style": "professional",
    "custom_title": null
  }
}
```

| Field | Default | Notes |
|-------|---------|-------|
| `tone` | `"professional"` | Any string: `professional`, `casual`, `developer`, `instructional`, `academic` |
| `banner_config.theme` | `"github_dark"` | `midnight`, `cyberpunk`, `obsidian`, `github_dark`, `matrix`, `neon`, `carbon` |
| `banner_config.style` | `"professional"` | `professional` (soft), `animated` (waving), `minimal` (rect) |
| `banner_config.font` | `"jetbrains"` | `jetbrains`, `default` |

**Response:** `ReadmeResponse` with `data.readme_content`, `data.processing_time`, `data.metadata`, etc.

---

## `POST /generate-linkedin`

```json
{
  "owner_name": "gowtham-2oo5",
  "repo_name": "CRT_Portal-server",
  "tone": "thought_leader",
  "focus": "business_value"
}
```

| Field | Default | Options |
|-------|---------|---------|
| `tone` | `"thought_leader"` | `thought_leader`, `casual`, `technical` |
| `focus` | `"business_value"` | `business_value`, `technical`, `hiring` |

---

## `POST /generate-article`

```json
{
  "owner_name": "gowtham-2oo5",
  "repo_name": "CRT_Portal-server",
  "tone": "professional",
  "article_style": "deep_dive",
  "target_length": "medium"
}
```

| Field | Default | Options |
|-------|---------|---------|
| `tone` | `"professional"` | Any string: `professional`, `conversational`, `academic` |
| `article_style` | `"deep_dive"` | `tutorial`, `deep_dive`, `case_study` |
| `target_length` | `"medium"` | `short` (800-1.2k words), `medium` (1.5-2.5k), `long` (3-4.5k) |

---

## `POST /generate-resume-points`

```json
{
  "owner_name": "gowtham-2oo5",
  "repo_name": "CRT_Portal-server",
  "role_target": "Backend Engineer",
  "seniority": "senior",
  "num_bullets": 5,
  "include_metrics": true
}
```

| Field | Default | Notes |
|-------|---------|-------|
| `role_target` | `"Software Engineer"` | Any role string — bullets are tailored to it |
| `seniority` | `"mid"` | Options: `intern`, `junior`, `mid`, `senior`, `staff`, `principal` |
| `num_bullets` | `5` | Min: 3, Max: 8 |
| `include_metrics` | `true` | Adds quantifiable metrics to bullets |

**⚠️ Frontend note:** The `content` field is a **JSON string**. Parse it:
```js
const parsed = JSON.parse(response.content);
// parsed.repo_description → "One-liner project summary"
// parsed.bullets          → ["Bullet 1", "Bullet 2", ...]
// parsed.skills_demonstrated → ["Java", "Spring Boot", ...]
```

---

## Response Shapes

**`/generate-readme`** returns `ReadmeResponse`:
```json
{ "success": true, "data": { "readme_content": "...", "processing_time": 12.4, ... } }
```

**`/generate-linkedin`, `/generate-article`, `/generate-resume-points`** return `ContentResponse`:
```json
{ "success": true, "content_type": "linkedin", "content": "...", "data": { "processing_time": 8.3, "metadata": { ... } } }
```

---

## Error Codes

| Code | When |
|------|------|
| `422` | Bad request body — missing required fields, invalid enum, `num_bullets` out of range |
| `500` | AI failure, rate limit hit, repo not found. Check `detail` in response |
