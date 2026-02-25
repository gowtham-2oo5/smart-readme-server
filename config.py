from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # silently ignore unknown env vars
    )

    # GitHub API
    github_token: str = ""

    # AI Model
    nvidia_api_key: str = ""
    ai_model: str = "qwen/qwen2.5-coder-32b-instruct"

    # Local storage
    output_dir: str = "./generated_readmes"
    claude_samples_dir: str = "./claude_samples"


# Singleton settings instance — import this everywhere
settings = Settings()
