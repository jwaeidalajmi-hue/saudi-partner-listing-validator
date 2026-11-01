"""Claude as the language and vision model."""
from __future__ import annotations

import base64

from anthropic import AsyncAnthropic

from ..models import Claim, ImageAnalysis
from .base import VisionProvider, clean_analysis, clean_claims, parse_json
from .prompts import claims_prompt, image_prompt


class AnthropicProvider(VisionProvider):
    def __init__(self, api_key: str, model: str):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
        self.name = f"anthropic:{model}"

    async def _ask(self, content: list[dict], max_tokens: int = 1200) -> dict:
        msg = await self.client.messages.create(
            model=self.model, max_tokens=max_tokens,
            messages=[{"role": "user", "content": content}],
        )
        text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
        return parse_json(text)

    async def extract_claims(self, description: str, provider_type: str, std: dict) -> list[Claim]:
        if not description.strip():
            return []
        raw = await self._ask([{"type": "text", "text": claims_prompt(description, provider_type, std)}])
        return clean_claims(raw, std)

    async def analyze_image(self, data: bytes, mime: str, filename: str, provider_type: str,
                            std: dict, claims: list[Claim]) -> ImageAnalysis:
        prompt = image_prompt(provider_type, std, [c.model_dump() for c in claims], filename)
        raw = await self._ask([
            {"type": "image", "source": {"type": "base64", "media_type": mime,
                                         "data": base64.b64encode(data).decode()}},
            {"type": "text", "text": prompt},
        ], max_tokens=800)
        return clean_analysis(raw, std, {c.id for c in claims})
