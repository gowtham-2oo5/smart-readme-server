import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # GitHub API
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    
    # AI Model API Keys
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
    
    # Local Storage
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', './generated_readmes')
    CLAUDE_SAMPLES_DIR = os.getenv('CLAUDE_SAMPLES_DIR', './claude_samples')
    
    # Supported AI Models (removed claude-sonnet)
    SUPPORTED_MODELS = {
        'gemini': 'google-gemini-pro',
        'openrouter-free': 'openrouter-free-model',
        'gpt-3.5': 'openai-gpt-3.5-turbo'
    }
    
    @classmethod
    def get_model_config(cls, model_name: str) -> Dict[str, Any]:
        """Get configuration for specific AI model"""
        configs = {
            'gemini': {
                'api_key': cls.GEMINI_API_KEY,
                'base_url': 'https://generativelanguage.googleapis.com/v1beta',
                'model_id': 'gemini-pro'
            },
            'openrouter-free': {
                'api_key': cls.OPENROUTER_API_KEY,
                'base_url': 'https://openrouter.ai/api/v1',
                'model_id': 'meta-llama/llama-3.2-3b-instruct:free'
            },
            'gpt-3.5': {
                'api_key': cls.OPENAI_API_KEY,
                'base_url': 'https://api.openai.com/v1',
                'model_id': 'gpt-3.5-turbo'
            }
        }
        return configs.get(model_name, {})
