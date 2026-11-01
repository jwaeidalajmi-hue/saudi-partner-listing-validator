"""Settings from environment variables (see .env.example)."""
import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv  # optional
    load_dotenv()
except Exception:
    pass


@dataclass(frozen=True)
class Settings:
    vision_provider: str = os.getenv("VISION_PROVIDER", "anthropic" if os.getenv("ANTHROPIC_API_KEY") else "mock")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")
    max_photos: int = int(os.getenv("MAX_PHOTOS", "20"))
    max_upload_mb: float = float(os.getenv("MAX_UPLOAD_MB", "15"))   # hard cap per file for the API itself
    concurrency: int = int(os.getenv("VISION_CONCURRENCY", "4"))


settings = Settings()
