"""
Application configuration and settings management.
"""

import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App settings
    app_name: str = "Canva App Reviewer"
    app_version: str = "1.0.0"
    version: str = "1.0.0"  # Alias for app_version
    app_description: str = "AI-powered code review tool for Canva applications (.js with visual and code analysis, .jsx/.tsx with code-only analysis)"
    debug: bool = False
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    allowed_origins: list = [
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://13.211.45.190:3000",
        "https://13.211.45.190:3000",
        "http://13.211.45.190",
        "https://13.211.45.190"
    ]  # For CORS
    
    # Database settings
    database_url: str = "sqlite:///./app_reviewer.db"
    
    # File upload settings
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    supported_file_types: list = [
        '.js',              # JavaScript
        '.jsx',             # React/JSX  
        '.tsx'              # TypeScript React
    ]
    upload_dir: str = "uploads"
    
    # Analysis settings
    max_analysis_time: int = 300  # 5 minutes in seconds
    
    # AI/Claude settings
    anthropic_api_key: Optional[str] = None
    claude_model: str = "claude-sonnet-4-20250514"
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings() 