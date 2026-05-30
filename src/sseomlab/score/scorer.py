"""Claude 호출로 장소를 판정하고 PlaceScore 를 만든다.

전략: 비용 절감을 위해 2단계.
  1) screening_model(haiku)로 텍스트만으로 1차 판정 → 명백 제외/저점은 조기 탈락
  2) 유망 후보만 main_model(opus)로 사진 포함 정밀 판정

이 모듈은 API 연동 골격이다. 실제 키가 있으면 동작하며,
키가 없으면 NotImplementedError 대신 명확한 안내를 던진다.
"""

from __future__ import annotations

import json

from sseomlab.config import get_scoring, get_settings
from sseomlab.models import Grade, Place, PlaceAnalysis, PlaceScore, SpaceType
from sseomlab.score.prompts import SYSTEM_PROMPT, build_user_message


def _summarize(place: Place) -> str:
    fields = {
        "이름": place.name,
        "카테고리": place.category,
        "지역": f"{place.region or ''} {place.sub_area or ''}".strip(),
        "주소": place.road_address or place.address,
        "네이버리뷰수": place.naver_review_count,
        "블로그리뷰수": place.blog_review_count,
        "홈페이지": place.homepage,
        "인스타": place.instagram_url,
        "본문": (place.raw_text or "")[:1500],
    }
    return "\n".join(f"- {k}: {v}" for k, v in fields.items() if v)


def _grade_from(score: float) -> Grade:
    cut = get_scoring()["grade_cutoffs"]
    if score >= cut["A"]:
        return Grade.A
    if score >= cut["B"]:
        return Grade.B
    if score >= cut["C"]:
        return Grade.C
    return Grade.D


def _composite(d: dict) -> float:
    """4개 점수를 종합 우선순위 점수로 결합 (협업가능성 가중)."""
    return round(
        0.30 * d["wedding_conversion_score"]
        + 0.20 * d["dolsang_conversion_score"]
        + 0.20 * d["hidden_space_score"]
        + 0.30 * d["collaboration_probability"],
        1,
    )


def score_place(place: Place, soft_hits: list[str], image_b64: list[str] | None = None) -> tuple[PlaceAnalysis, PlaceScore]:
    """Claude 로 판정. image_b64 는 base64 JPEG 리스트(선택)."""
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY 가 없습니다. .env 를 설정하세요. "
            "(설계 검증용 dry-run 은 pipeline.run(dry_run=True) 사용)"
        )

    from anthropic import Anthropic  # 지연 임포트

    client = Anthropic(api_key=settings.anthropic_api_key)

    content: list[dict] = [{"type": "text", "text": build_user_message(_summarize(place), soft_hits)}]
    for b64 in (image_b64 or [])[:4]:  # 사진은 4장까지
        content.append(
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}}
        )

    model = settings.anthropic_model if image_b64 else settings.anthropic_screening_model
    resp = client.messages.create(
        model=model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
    )
    data = json.loads(resp.content[0].text)
    return _to_models(data)


def _to_models(data: dict) -> tuple[PlaceAnalysis, PlaceScore]:
    analysis = PlaceAnalysis(
        exclude=data.get("exclude", False),
        exclude_reason=data.get("exclude_reason", ""),
        space_type=SpaceType(data.get("space_type", "기타")),
    )
    composite = _composite(data)
    score = PlaceScore(
        hidden_space_score=data["hidden_space_score"],
        wedding_conversion_score=data["wedding_conversion_score"],
        dolsang_conversion_score=data["dolsang_conversion_score"],
        collaboration_probability=data["collaboration_probability"],
        composite_score=composite,
        grade=Grade(data.get("grade") or _grade_from(composite).value),
        recommended_offer=data.get("recommended_offer", ""),
    )
    return analysis, score
