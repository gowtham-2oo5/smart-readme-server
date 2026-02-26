import logging
import httpx

from config import settings

log = logging.getLogger(__name__)


class AIService:
    """NVIDIA API provider for the configured AI model."""

    def __init__(self):
        if not settings.nvidia_api_key:
            raise ValueError("NVIDIA_API_KEY is not set in environment / .env")
        
        self.model_version = settings.ai_model
        self.api_key = settings.nvidia_api_key
        self.invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"

    async def generate_readme(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }

        payload = {
            "model": self.model_version,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 8192,
            "temperature": 0.4,
            "top_p": 0.9,
            "stream": False,
        }

        log.info("Sending request to %s via NVIDIA API...", self.model_version)
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(self.invoke_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            response_text = data["choices"][0]["message"]["content"]
            
            log.info("Generation complete \u2014 %d chars total", len(response_text))
            return response_text

    def get_supported_models(self) -> list[str]:
        return [self.model_version]
