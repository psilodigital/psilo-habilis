"""
Gateway configuration.
Loaded from environment variables with sensible defaults.
"""

import os
from pathlib import Path

from pydantic_settings import BaseSettings


def _find_repo_root() -> Path:
    """Walk up from this file to find the repo root (contains docker-compose.yml)."""
    current = Path(__file__).resolve().parent
    for _ in range(10):
        if (current / "docker-compose.yml").exists():
            return current
        current = current.parent
    # Fallback: assume /app in container, repo root mounted or paths configured via env
    return Path(os.getenv("HABILIS_REPO_ROOT", "/app"))


class Settings(BaseSettings):
    port: int = 8080
    log_level: str = "INFO"

    # Repo root — used to locate worker-packs/ and clients/ on disk
    repo_root: str = str(_find_repo_root())

    # Agent Zero
    agentzero_base_url: str = "http://agentzero:80"
    agentzero_api_token: str = ""
    agentzero_auth_login: str = "admin"
    agentzero_auth_password: str = ""

    # LiteLLM
    litellm_base_url: str = "http://litellm:4000"
    litellm_master_key: str = ""

    # Paperclip
    paperclip_base_url: str = "http://paperclip:3100"

    model_config = {"env_file": ".env", "case_sensitive": False}


settings = Settings()
