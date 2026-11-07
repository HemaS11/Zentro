
"""Shared configuration helpers for Zentro AI agents."""

import os
from pathlib import Path
from typing import Any, Dict

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args: Any, **kwargs: Any) -> bool:
        return False


# Load .env from ai-agents or project root
ROOT_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
_ENV_PATHS = [
    Path(__file__).resolve().with_name(".env"),
    ROOT_ENV_PATH,
]

for env_path in _ENV_PATHS:
    if env_path.exists():
        load_dotenv(env_path, override=False)
        break

if ROOT_ENV_PATH.exists():
    load_dotenv(ROOT_ENV_PATH, override=False)


def require_api_key(name: str, *alternates: str) -> str:
    for key in (name, *alternates):
        value = os.getenv(key)
        if value and value.strip():
            return value.strip()
    return ""


def get_agent_config() -> Dict[str, Any]:
    return {
        "provider": os.getenv("AI_PROVIDER", "gemini").strip().lower(),
        "openai_api_key": require_api_key(
            "OPENAI_API_KEY", "ZENTRO_OPENAI_API_KEY"
        ),
        "gemini_api_key": require_api_key(
            "GEMINI_API_KEY", "ZENTRO_GEMINI_API_KEY"
        ),
        "paypal_client_id": require_api_key(
            "PAYPAL_CLIENT_ID", "ZENTRO_PAYPAL_CLIENT_ID"
        ),
        "paypal_client_secret": require_api_key(
            "PAYPAL_CLIENT_SECRET", "ZENTRO_PAYPAL_CLIENT_SECRET"
        ),
        "model": os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
        "temperature": float(os.getenv("GEMINI_TEMPERATURE", "0.2")),
        "debug": os.getenv("DEBUG", "false").strip().lower()
        in {"1", "true", "yes", "on"},
    }


__all__ = ["require_api_key", "get_agent_config"]
