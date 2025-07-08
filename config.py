import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # GitHub API
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    
    # AI Model API Key
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # Local Storage
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', './generated_readmes')
    CLAUDE_SAMPLES_DIR = os.getenv('CLAUDE_SAMPLES_DIR', './claude_samples')
    
    # AI Model Configuration
    AI_MODEL = 'gemini-2.5-flash'
    
    @classmethod
    def get_model_config(cls) -> Dict[str, Any]:
        """Get configuration for Gemini 2.5 Flash"""
        return {
            'api_key': cls.GEMINI_API_KEY,
            'model_id': cls.AI_MODEL
        }
