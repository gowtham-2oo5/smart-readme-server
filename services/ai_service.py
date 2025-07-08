import os
from abc import ABC, abstractmethod
from config import Config
from google import genai
from google.genai import types


class AIProvider(ABC):
    """Abstract base class for AI providers"""

    @abstractmethod
    def generate_readme(self, prompt: str) -> str:
        pass


class GeminiProvider(AIProvider):
    def __init__(self, model_version="gemini-2.5-flash"):
        self.api_key = Config.GEMINI_API_KEY
        self.model_version = model_version
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        # Initialize the Google GenAI client
        self.client = genai.Client(api_key=self.api_key)

    def generate_readme(self, prompt: str) -> str:
        try:
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=prompt),
                    ],
                ),
            ]
            
            # Optimized generation config for better performance
            generate_content_config = types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    thinking_budget=150,  # Further reduced thinking time
                ),
                response_mime_type="text/plain",
                temperature=0.2,  # Even lower temperature for more focused output
                max_output_tokens=8000  # Increased limit for comprehensive READMEs
            )

            # Use streaming to handle longer responses
            response_text = ""
            for chunk in self.client.models.generate_content_stream(
                model=self.model_version,
                contents=contents,
                config=generate_content_config,
            ):
                if chunk.text:
                    response_text += chunk.text
            
            return response_text

        except Exception as e:
            print(f"❌ Gemini generation failed: {e}")
            raise


class AIService:
    """Main AI service using Gemini 2.5 Flash"""

    def __init__(self):
        self.provider = GeminiProvider('gemini-2.5-flash')

    def generate_readme(self, prompt: str) -> str:
        """Generate README using Gemini 2.5 Flash"""
        return self.provider.generate_readme(prompt)

    def get_supported_models(self) -> list:
        """Get list of supported AI models"""
        return ['gemini-2.5-flash']
