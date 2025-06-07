"""
Configuration module for Agentic Skill Builder
Handles environment variables, logging, and application settings
"""

import os
import logging
from typing import Optional
from dataclasses import dataclass

@dataclass
class AzureOpenAIConfig:
    """Configuration for Azure OpenAI service"""
    endpoint: str
    api_key: str
    api_version: str
    llm_deployment: str
    llm_model: str
    embeddings_deployment: str
    embeddings_model: str
    
    @classmethod
    def from_env(cls) -> 'AzureOpenAIConfig':
        """Create configuration from environment variables"""
        return cls(
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "").replace('"', ''),
            api_key=os.getenv("AZURE_OPENAI_KEY", "").replace('"', ''),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview").replace('"', ''),
            llm_deployment=os.getenv("AZURE_OPENAI_LLM_DEPLOYMENT", "gpt-4.1").replace('"', ''),
            llm_model=os.getenv("AZURE_OPENAI_LLM_MODEL", "gpt-4.1").replace('"', ''),
            embeddings_deployment=os.getenv("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT", "text-embedding-3-small").replace('"', ''),
            embeddings_model=os.getenv("AZURE_OPENAI_EMBEDDINGS_MODEL", "text-embedding-3-small").replace('"', '')
        )
    
    def validate(self) -> bool:
        """Validate that all required settings are present"""
        required_fields = [self.endpoint, self.api_key, self.llm_deployment]
        return all(field.strip() for field in required_fields)

@dataclass
class AppConfig:
    """Main application configuration"""
    debug: bool = False
    log_level: str = "INFO"
    gradio_port: int = 7860
    mcp_port: int = 8000
    max_quiz_questions: int = 5
    default_lesson_duration: int = 5
    azure_openai: Optional[AzureOpenAIConfig] = None
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """Create configuration from environment variables"""
        return cls(
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            gradio_port=int(os.getenv("GRADIO_PORT", "7860")),
            mcp_port=int(os.getenv("MCP_PORT", "8000")),
            max_quiz_questions=int(os.getenv("MAX_QUIZ_QUESTIONS", "5")),
            default_lesson_duration=int(os.getenv("DEFAULT_LESSON_DURATION", "5")),
            azure_openai=AzureOpenAIConfig.from_env()
        )

def setup_logging(config: AppConfig):
    """Setup application logging"""
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('agentic_skill_builder.log')
        ]
    )

def get_config() -> AppConfig:
    """Get application configuration"""
    config = AppConfig.from_env()
    
    # Validate Azure OpenAI configuration
    if not config.azure_openai or not config.azure_openai.validate():
        raise ValueError(
            "Azure OpenAI configuration is incomplete. "
            "Please check your .env file for AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY, and AZURE_OPENAI_LLM_DEPLOYMENT"
        )
    
    return config
