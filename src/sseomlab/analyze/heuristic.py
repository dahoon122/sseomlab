"""규칙기반(heuristic) 공간 분석 — LLM 키 없이 PlaceAnalysis 신호를 만든다.

Place.raw_text(상호+카테고리+features+notes)의 키워드로 공간 특성을 추정한다.
운영 단계에서 Claude 사진 분석으로 대체/보강할 수 있다(인터페이스 동일).
"""

from __future__ import annotations

from sseomlab.models import Place, PlaceAnalysis, SpaceType

# 공간유형 추정: 키워드 우선순위
_TYPE_RULES: list[tuple[str, SpaceType]] = [
    ("한옥", SpaceType.한옥카페),
    ("고택", SpaceType.한옥카페),
    ("오션뷰", SpaceType.오션뷰카페),
    ("바다", SpaceType.오션뷰카페),
    ("숲", SpaceType.숲속카페),
    ("독채", SpaceType.독채식당),
    ("베이커리", SpaceType.베이커리카페),
    ("브런치", SpaceType.브런치카페),
    ("갤러리", SpaceType.복합문화공간),
    ("복합문화", SpaceType.복합문화공간),
    ("정원", SpaceType.정원카페),
    ("가든", SpaceType.정원카페),
]


def _kw(text: str, *words: str) -> bool:
    return any(w in text for w in words)


def analyze(place: Place) -> PlaceAnalysis:
    t = place.raw_text or ""

    space_type = SpaceType.기타
    for kw, st in _TYPE_RULES:
        if kw in t:
            space_type = st
            break
    if space_type is SpaceType.기타 and _kw(t, "카페", "식당", "레스토랑"):
        space_type = SpaceType.브런치카페

    has_garden = _kw(t, "정원", "가든")
    has_yard = _kw(t, "마당")
    has_terrace = _kw(t, "테라스")
    has_hanok = _kw(t, "한옥", "고택")
    has_ocean = _kw(t, "오션뷰", "바다")
    has_forest = _kw(t, "숲")
    has_window = _kw(t, "통창")
    has_private = _kw(t, "독채", "룸")
    outdoor = has_garden or has_yard or has_terrace or _kw(t, "야외", "목장", "농장")

    # 노출도: 인스타 핸들 있고 리뷰 많으면 노출 높음
    reviews = place.naver_review_count or 0
    insta = 0.7 if place.instagram_url else 0.2
    if reviews > 400:
        insta = min(1.0, insta + 0.2)

    wedding_mention = 1.0 if _kw(t, "웨딩", "예식", "하우스웨딩") else (0.3 if _kw(t, "대관") else 0.0)

    return PlaceAnalysis(
        space_type=space_type,
        has_garden=has_garden,
        has_yard=has_yard,
        has_terrace=has_terrace,
        has_hanok=has_hanok,
        has_ocean_view=has_ocean,
        has_forest=has_forest,
        has_large_window=has_window,
        has_private_room=has_private,
        parking_likelihood=0.8 if _kw(t, "주차") else 0.4,
        accessibility=0.4 if _kw(t, "외곽") else (0.8 if _kw(t, "도심") else 0.6),
        outdoor_usable=outdoor,
        rain_alternative=_kw(t, "실내대체", "통창") or not outdoor,
        photo_potential=0.85 if _kw(t, "포토존", "오션뷰", "통창", "정원") else 0.55,
        private_event_possible=has_private or _kw(t, "독채"),
        instagram_exposure=insta,
        wedding_mention_level=wedding_mention,
        is_franchise=_kw(t, "체인", "프랜차이즈"),
        rental_signal=_kw(t, "대관", "단체", "독채"),
        weekday_idle_likelihood=0.7 if _kw(t, "외곽") else 0.5,
        estimated_capacity=120 if _kw(t, "대형") else (40 if _kw(t, "소형") else 80),
        notes="heuristic 분석(키워드 기반)",
    )
