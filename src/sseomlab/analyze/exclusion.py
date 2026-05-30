"""규칙 기반 1차 제외 필터.

Claude 호출(비용) 전에, 명백한 웨딩 전문 공간을 키워드로 걸러낸다.
hard 키워드 적중 → 즉시 제외. soft 키워드는 점수 단계에서 감점 신호로 전달.
"""

from __future__ import annotations

from dataclasses import dataclass

from sseomlab.config import get_space_types
from sseomlab.models import Place


@dataclass
class ExclusionResult:
    exclude: bool
    reason: str
    soft_hits: list[str]


def _haystack(place: Place) -> str:
    parts = [place.name or "", place.category or "", place.raw_text or ""]
    return " ".join(parts)


def screen(place: Place) -> ExclusionResult:
    """이름/카테고리/본문 텍스트에서 제외 키워드를 검사한다."""
    cfg = get_space_types()
    hard = cfg.get("exclusion_keywords", {}).get("hard", [])
    soft = cfg.get("exclusion_keywords", {}).get("soft", [])

    text = _haystack(place)

    hard_hits = [kw for kw in hard if kw in text]
    if hard_hits:
        return ExclusionResult(
            exclude=True,
            reason=f"웨딩 전문 공간 키워드 적중: {', '.join(hard_hits)}",
            soft_hits=[],
        )

    soft_hits = [kw for kw in soft if kw in text]
    return ExclusionResult(exclude=False, reason="", soft_hits=soft_hits)
