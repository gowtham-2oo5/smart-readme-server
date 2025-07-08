
<div align="center">
  <h1>🚀 Smart README Generator API Testing</h1>
  <p><em>Generate comprehensive README files for GitHub repositories using various AI models.</em></p>

  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Uvicorn-009688?style=for-the-badge&logo=uvicorn&logoColor=white" alt="Uvicorn">
  <img src="https://img.shields.io/badge/Pydantic-e8e23a?style=for-the-badge&logo=pydantic&logoColor=black" alt="Pydantic">
  <img src="https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge" alt="License">

  <br><br>

  <a href="#installation">🚀 Get Started</a> •
  <a href="#features">✨ Features</a> •
  <a href="#api-endpoints">🌐 API Endpoints</a>
</div>

<hr>

## 🌟 Overview

`smart-readme-server` is a powerful API built with FastAPI that leverages various AI models to automatically generate comprehensive README files for GitHub repositories. It streamlines the documentation process, saving developers time and ensuring consistent, high-quality READMEs.

## ✨ Features

- **Automated README Generation:** Generates detailed READMEs using AI models like Gemini, OpenRouter (Llama 3), and GPT-3.5.
- **AI Model Flexibility:** Supports multiple AI models, allowing users to choose the best option for their needs.
- **Local File Storage:** Saves generated README files locally for easy access and version control.
- **API Endpoints:** Provides a set of API endpoints for generating READMEs, listing files, and retrieving file content.
- **Configuration via Environment Variables:** Uses environment variables for API keys and other configuration settings, making it easy to deploy and manage.
- **Error Handling:** Implements robust error handling to provide informative feedback to users.
- **Asynchronous Operations:** Uses FastAPI's asynchronous capabilities for efficient handling of requests.

## ⚙️ Architecture

The `smart-readme-server` follows a modular architecture, with distinct services responsible for specific tasks:

- **API Layer (FastAPI):** Handles incoming requests, validates data, and returns responses.
- **ReadmeService:** Orchestrates the README generation process, coordinating with other services.
- **GitHubService:** Interacts with the GitHub API to retrieve repository information and file content.
- **AIService:** Provides an abstraction layer for interacting with different AI models.
- **FileService:** Handles local file operations, such as saving and retrieving README files.

The application uses a configuration class (`Config` in `config.py`) to manage environment variables and API keys. This allows for easy configuration and deployment across different environments.

## 🛠️ Installation

Follow these steps to set up and run the `smart-readme-server`:

### Prerequisites

- Python 3.7+
- [Optional] Git (for cloning the repository)
- API Keys for the desired AI models (Gemini, OpenAI, OpenRouter)

### Steps

1. **Clone the repository:**

   ```bash
   git clone https://github.com/gowtham-2oo5/smart-readme-server.git
   cd smart-readme-server
   ```

2. **Create a virtual environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Linux/macOS
   # venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**

   Create a `.env` file in the root directory with the following content (replace with your actual API keys):

   ```
   GITHUB_TOKEN=<YOUR_GITHUB_TOKEN>
   OPENAI_API_KEY=<YOUR_OPENAI_API_KEY>
   GEMINI_API_KEY=<YOUR_GEMINI_API_KEY>
   OPENROUTER_API_KEY=<YOUR_OPENROUTER_API_KEY>
   OUTPUT_DIR=./generated_readmes
   CLAUDE_SAMPLES_DIR=./claude_samples
   ```

   **Note:**  `GITHUB_TOKEN` is optional, but recommended for higher API rate limits.

5. **Run the application:**

   ```bash
   uvicorn main:app --reload
   ```

   This will start the server at `http://127.0.0.1:8000`.

## 🌐 API Endpoints

### 1. Root Endpoint (`/`)

- **Description:** Provides basic information about the API, including supported models and available endpoints.
- **Method:** `GET`
- **Response:**

  ```json
  {
    "message": "README Generator API",
    "version": "1.0.0",
    "supported_models": ["gemini", "openrouter-free", "gpt-3.5"],
    "endpoints": {
      "generate": "/generate-readme",
      "models": "/models",
      "files": "/files"
    }
  }
  ```

### 2. Get Supported Models (`/models`)

- **Description:** Retrieves a list of supported AI models.
- **Method:** `GET`
- **Response:**

  ```json
  {
    "supported_models": ["gemini", "openrouter-free", "gpt-3.5"],
    "default_model": "gemini"
  }
  ```

### 3. Generate README (`/generate-readme`)

- **Description:** Generates a README file for a given GitHub repository.
- **Method:** `POST`
- **Request Body:**

  ```json
  {
    "repo_name": "repository_name",
    "owner_name": "owner_username",
    "ai_model": "gemini"  // Can be "gemini", "openrouter-free", or "gpt-3.5"
  }
  ```

- **Response:**

  ```json
  {
    "success": true,
    "data": {
      "readme_content": "Generated README content...",
      "readme_length": 1234,
      "local_file_path": "./generated_readmes/owner-repo-1678886400.md",
      "processing_time": 5.2,
      "files_analyzed": 10,
      "ai_model_used": "gemini",
      "branch_used": "main",
      "metadata": {
        "primary_language": "Python",
        "project_type": "api",
        "tech_stack": ["FastAPI", "Uvicorn", "Pydantic"],
        "frameworks": ["FastAPI"]
      },
      "repo_info": {
        "owner": "owner_username",
        "repo": "repository_name",
        "url": "https://github.com/owner_username/repository_name"
      }
    }
  }
  ```

### 4. List Generated Files (`/files`)

- **Description:** Lists all generated README files.
- **Method:** `GET`
- **Response:**

  ```json
  {
    "success": true,
    "files": [
      {
        "name": "owner-repo-1678886400.md",
        "path": "/path/to/generated_readmes/owner-repo-1678886400.md",
        "size": 2345,
        "created": 1678886400.0
      }
    ],
    "total_files": 1
  }
  ```

### 5. Get File Content (`/files/{file_name}`)

- **Description:** Retrieves the content of a specific README file.
- **Method:** `GET`
- **Parameters:**
  - `file_name`: The name of the file to retrieve (e.g., `owner-repo-1678886400.md`).
- **Response:**

  ```json
  {
    "success": true,
    "content": "Content of the README file...",
    "file_info": {
      "file_path": "/path/to/generated_readmes/owner-repo-1678886400.md",
      "file_name": "owner-repo-1678886400.md",
      "file_size": 2345,
      "created_at": 1678886400.0,
      "modified_at": 1678886400.0
    }
  }
  ```

## 🧪 Testing

To test the API endpoints, you can use tools like `curl`, `Postman`, or `insomnia`.  Here's an example using `curl` to generate a README:

```bash
curl -X POST \
  http://127.0.0.1:8000/generate-readme \
  -H 'Content-Type: application/json' \
  -d '{
    "repo_name": "smart-readme-server",
    "owner_name": "gowtham-2oo5",
    "ai_model": "gemini"
  }'
```

## 🐛 Troubleshooting

- **Missing API Keys:** Ensure that you have set the required API keys in the `.env` file.
- **Network Errors:** Check your internet connection and verify that the AI model APIs are accessible.
- **File Permissions:**  Make sure the application has write permissions to the `OUTPUT_DIR`.
- **Model Not Supported:** Double-check if the `ai_model` you are using is supported. You can get the list of supported models from the `/models` endpoint.

## 🤝 Contributing

We welcome contributions to `smart-readme-server`!  Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add some feature'`)
5. Push to the branch (`git push origin feature/your-feature`)
6. Open a pull request

## 🎉 Conclusion

`smart-readme-server` simplifies the process of generating README files, allowing developers to focus on building great software.  By leveraging the power of AI, it ensures consistent and comprehensive documentation for your projects.

### 🌟 What's Next?

- [ ] Implement caching to improve performance.
- [ ] Add support for more AI models.
- [ ] Implement a UI for easier interaction.

### 📞 Support & Contact

- 🐛 Issues: Report bugs via GitHub Issues
- 💬 Questions: Open a discussion or issue

---

<div align="center">
  <strong>⭐ Star this repo if you find it helpful!</strong>
  <br>
  <em>Made with ❤️ for the developer community</em>
</div>
