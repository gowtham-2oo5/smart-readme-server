import json
import requests
from abc import ABC, abstractmethod
from typing import Dict, Any
from config import Config

class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    @abstractmethod
    def generate_readme(self, prompt: str) -> str:
        pass

class GeminiProvider(AIProvider):
    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
    
    def generate_readme(self, prompt: str) -> str:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "maxOutputTokens": 4000,
                    "temperature": 0.7
                }
            }
            
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            return data['candidates'][0]['content']['parts'][0]['text']
            
        except Exception as e:
            print(f"❌ Gemini generation failed: {e}")
            raise

class OpenRouterProvider(AIProvider):
    def __init__(self):
        self.api_key = Config.OPENROUTER_API_KEY
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")
    
    def generate_readme(self, prompt: str) -> str:
        try:
            url = "https://openrouter.ai/api/v1/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "meta-llama/llama-3.2-3b-instruct:free",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 4000,
                "temperature": 0.7
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            return data['choices'][0]['message']['content']
            
        except Exception as e:
            print(f"❌ OpenRouter generation failed: {e}")
            raise


class GPTProvider(AIProvider):
    def __init__(self):
        self.api_key = Config.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
    
    def generate_readme(self, prompt: str) -> str:
        try:
            url = "https://api.openai.com/v1/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 4000,
                "temperature": 0.7
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            return data['choices'][0]['message']['content']
            
        except Exception as e:
            print(f"❌ GPT generation failed: {e}")
            raise

class AIService:
    """Main AI service that manages different providers"""
    
    def __init__(self):
        self.providers = {
            'gemini': GeminiProvider,
            'openrouter-free': OpenRouterProvider,
            'gpt-3.5': GPTProvider
        }
    
    def get_provider(self, model_name: str) -> AIProvider:
        """Get AI provider instance by model name"""
        if model_name not in self.providers:
            raise ValueError(f"Unsupported AI model: {model_name}")
        
        return self.providers[model_name]()
    
    def generate_readme(self, model_name: str, prompt: str) -> str:
        """Generate README using specified AI model"""
        provider = self.get_provider(model_name)
        return provider.generate_readme(prompt)
    
    def get_supported_models(self) -> list:
        """Get list of supported AI models"""
        return list(self.providers.keys())
