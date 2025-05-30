"""
Configuration management for the Canva App Reviewer backend.
"""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional, List
import os


class Settings(BaseSettings):
    """Application settings."""
    
    # App settings
    app_name: str = "Canva App Reviewer"
    debug: bool = False
    version: str = "1.0.0"
    api_v1_prefix: str = "/api/v1"
    
    # File upload settings
    max_upload_size: int = 10 * 1024 * 1024  # 10MB (smaller for individual files)
    allowed_extensions: List[str] = [".js", ".tsx"]
    upload_dir: str = "/tmp/uploads"
    
    # Analysis settings
    timeout_seconds: int = 300
    max_concurrent_analyses: int = 5
    
    # External services
    anthropic_api_key: Optional[str] = None
    
    # Docker settings
    node_docker_image: str = "node:18-alpine"
    analysis_timeout: int = 180
    
    # CORS settings - configurable for different environments
    allowed_origins: List[str] = [
        "http://localhost:3000",  # Default for local development
    ]
    
    # Frontend URL for API responses
    frontend_url: str = "http://localhost:3000"
    
    # Backend URL (for self-reference in responses)
    backend_url: str = "http://localhost:8000"
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Parse ALLOWED_ORIGINS from environment if provided as comma-separated string
        if "ALLOWED_ORIGINS" in os.environ:
            origins_str = os.environ["ALLOWED_ORIGINS"]
            self.allowed_origins = [origin.strip() for origin in origins_str.split(",")]


# Global settings instance
settings = Settings() 