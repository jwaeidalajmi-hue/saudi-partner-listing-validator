"""The Claude adapter end to end with a stand-in client: prompts go out, the JSON
replies are cleaned, and a two-word Arabic description is matched to a photo by
meaning. No API key or network needed."""
import asyncio
import json
import types

from app import standards
from app.pipeline import validate_listing
from app.providers.anthropic_provider import AnthropicProvider


class FakeMessages:
    def __init__(self, replies):
        self.replies, self.prompts = replies, []

    async def create(self, **kw):
        content = kw["messages"][0]["content"]
        self.prompts.append(content[-1]["text"])
        reply = self.replies.pop(0)
        return types.SimpleNamespace(content=[types.SimpleNamespace(type="text", text=reply)])


def provider(replies):
    p = AnthropicProvider(api_key="test", model="claude-test")
    p.client = types.SimpleNamespace(messages=FakeMessages(replies))
    return p


def test_claude_reads_criteria_and_matches_a_diving_photo(photo):
    criteria = {"claims": [{"id": "c1", "label": "رحلة غطس", "label_en": "diving trip", "label_ar": "رحلة غطس",
                            "kind": "experience", "core": True, "scene": "activity",
                            "evidence_en": "a person diving underwater", "evidence_ar": "شخص يغوص تحت الماء"}]}
    seen = {"scenes": ["activity", "place", "nonsense"], "scene": "activity", "supports": ["c1", "c9"],
            "objects": ["diver", "coral reef"], "quality": 4, "caption_en": "a diver over a reef",
            "caption_ar": "غوّاص فوق شعاب"}
    p = provider([f"```json\n{json.dumps(criteria, ensure_ascii=False)}\n```",
                  "Here you go: " + json.dumps(seen, ensure_ascii=False)])
    report = asyncio.run(validate_listing(p, "activities", "رحلة غطس", [("IMG_2041.jpg", photo())]))
    sent = p.client.messages.prompts
    assert "رحلة غطس" in sent[0] and "diving trip" in sent[1] and "a person diving underwater" in sent[1]
    assert report.engine == "anthropic:claude-test" and report.photos_checked == 1
    assert [(c.claim.label, c.status) for c in report.claims] == [("رحلة غطس", "shown")]
    assert report.photos[0].analysis.scenes == ["activity", "place"]          # unknown scene dropped
    assert report.photos[0].analysis.supports == ["c1"]                        # unknown id dropped
    assert {r.code: r.status for r in report.rules}["cover"] == "pass"


def test_a_bad_model_reply_is_not_checked_not_a_failure(photo):
    p = provider(["sorry, I can't help with that"])     # empty description: no criteria call
    report = asyncio.run(validate_listing(p, "fnb", "", [("a.jpg", photo())]))
    assert report.photos_checked == 0 and report.verdict in ("partly_checked", "needs_changes")
    assert all(c.claim.source == "standard" for c in report.claims)
    assert all(c.status == "unchecked" for c in report.claims)
    assert standards.provider("fnb")["fallback_required"] == [c.claim.scene for c in report.claims]
