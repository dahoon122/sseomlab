"""규칙기반 점수화 — config/scoring.yaml 가중치로 4대 점수를 계산(LLM 불필요).

각 항목을 0~1 신호로 환산 후 가중합 → 0~100.
웨딩 성수기 가산점(apply_peak_boost)으로 '성수기 숨은 공간 가치 상승'을 반영한다.
"""

from __future__ import annotations

from sseomlab.config import get_demand, get_scoring
from sseomlab.models import Grade, Place, PlaceAnalysis, PlaceScore
from sseomlab.score.scorer import _grade_from


def _sweetspot(reviews: int | None, lo: int, hi: int) -> float:
    if not reviews:
        return 0.3
    if lo <= reviews <= hi:
        return 1.0
    if reviews < lo:
        return max(0.2, reviews / lo)
    return max(0.2, hi / reviews)  # 너무 많으면(과노출) 감점


def _wsum(weights: dict, signals: dict) -> float:
    return sum(weights[k] * signals[k] for k in weights)


def _food_service(place: Place) -> float:
    cat = place.category or ""
    return 1.0 if any(k in cat for k in ("식당", "레스토랑", "한식", "베이커리")) else 0.8


def score(place: Place, analysis: PlaceAnalysis, soft_hits: list[str] | None = None,
          apply_peak_boost: bool = False) -> PlaceScore:
    cfg = get_scoring()
    a = analysis

    # --- 숨은공간 ---
    hs_w = cfg["hidden_space"]["weights"]
    lo, hi = cfg["hidden_space"]["naver_review_sweetspot_range"]
    hs = _wsum(hs_w, {
        "instagram_low_exposure": 1 - a.instagram_exposure,
        "naver_review_sweetspot": _sweetspot(place.naver_review_count, lo, hi),
        "outskirts_location": 1 - a.accessibility,
        "wedding_mention_absent": 1 - a.wedding_mention_level,
    })
    if apply_peak_boost:
        hs = min(1.0, hs * (1 + get_demand()["seasonality"]["peak_hidden_space_boost"]))

    # --- 웨딩 전환 ---
    wc_w = cfg["wedding_conversion"]["weights"]
    outdoor = 1.0 if a.outdoor_usable else (0.5 if (a.has_large_window or a.has_ocean_view) else 0.2)
    cap = min(1.0, (a.estimated_capacity or 60) / 150)
    wc = _wsum(wc_w, {
        "outdoor_feature": outdoor,
        "capacity_indoor": cap,
        "aesthetic_photo": a.photo_potential,
        "parking": a.parking_likelihood,
    })

    # --- 돌상 전환 ---
    dc_w = cfg["dolsang_conversion"]["weights"]
    dc = _wsum(dc_w, {
        "private_room": 1.0 if a.has_private_room else 0.3,
        "indoor_comfort": 0.85 if a.rain_alternative else 0.5,
        "food_service": _food_service(place),
        "parking": a.parking_likelihood,
    })

    # --- 협업 가능성 ---
    cb_w = cfg["collaboration"]["weights"]
    contactable = 1.0 if (place.phone or place.homepage or place.instagram_url) else 0.3
    cb = _wsum(cb_w, {
        "weekday_idle_capacity": a.weekday_idle_likelihood,
        "not_franchise": 0.0 if a.is_franchise else 1.0,
        "rental_signal": 1.0 if a.rental_signal else 0.3,
        "contactability": contactable,
    })

    hs100, wc100, dc100, cb100 = (round(x * 100) for x in (hs, wc, dc, cb))
    composite = round(0.30 * wc100 + 0.20 * dc100 + 0.20 * hs100 + 0.30 * cb100, 1)

    return PlaceScore(
        hidden_space_score=hs100,
        wedding_conversion_score=wc100,
        dolsang_conversion_score=dc100,
        collaboration_probability=cb100,
        composite_score=composite,
        grade=_grade_from(composite),
        recommended_offer=_offer(a, wc100, dc100),
    )


def _offer(a: PlaceAnalysis, wc: int, dc: int) -> str:
    focus = "웨딩" if wc >= dc else "돌잔치"
    hook = []
    if a.outdoor_usable:
        hook.append("야외 활용")
    if a.has_private_room:
        hook.append("단독 프라이빗")
    if a.has_ocean_view:
        hook.append("오션뷰")
    if a.has_hanok:
        hook.append("한옥 무드")
    tail = ", ".join(hook) or "공간 분위기"
    return f"평일 유휴시간 {focus} 대관 제휴 — {tail} 강점으로 제안"
