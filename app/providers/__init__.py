from ..config import settings
from .base import VisionProvider


def get_provider() -> VisionProvider:
    if settings.vision_provider == "anthropic":
        if not settings.anthropic_api_key:
            raise RuntimeError("VISION_PROVIDER=anthropic needs ANTHROPIC_API_KEY. Set it, or use VISION_PROVIDER=mock.")
        from .anthropic_provider import AnthropicProvider
        return AnthropicProvider(settings.anthropic_api_key, settings.anthropic_model)
    from .mock_provider import MockProvider
    return MockProvider()
