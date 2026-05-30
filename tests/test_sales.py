"""영업 키트 생성 테스트 — 12개 필드가 공간 정보로 채워지는지."""

from sseomlab.concept import recommender
from sseomlab.models import (
    Grade,
    Place,
    PlaceAnalysis,
    PlaceRecord,
    PlaceScore,
    SpaceType,
)
from sseomlab.sales import generator


def _record() -> PlaceRecord:
    place = Place(source="t", name="가창 정원카페", region="대구", sub_area="가창", phone="053-1")
    analysis = PlaceAnalysis(space_type=SpaceType.정원카페, has_garden=True,
                             has_large_window=True, parking_likelihood=0.8, outdoor_usable=True)
    score = PlaceScore(hidden_space_score=70, wedding_conversion_score=82, dolsang_conversion_score=64,
                       collaboration_probability=78, composite_score=76, grade=Grade.A)
    return PlaceRecord(place=place, analysis=analysis, score=score, contact_priority=1)


def test_sales_kit_has_all_fields_filled():
    rec = _record()
    prop = recommender.build_proposal(rec, claude_refine=False)
    kit = generator.build_sales_kit(rec, prop, claude_refine=False)

    assert kit.space_name == "가창 정원카페"
    assert "가창 정원카페" in kit.dm_message            # DM에 상호 포함
    assert "제이드컴퍼니" in kit.phone_script           # 전화 스크립트
    assert kit.product_name                             # 추천 상품명
    assert kit.expected_products                        # 예상 상품
    assert kit.expected_avg_price_krw > 0               # 예상 객단가
    assert "즉시" in kit.contact_timing                 # A등급 → 즉시 컨택
    assert kit.proposal_title.startswith("[가창 정원카페]")


def test_dm_reflects_space_strengths():
    rec = _record()
    prop = recommender.build_proposal(rec, claude_refine=False)
    kit = generator.build_sales_kit(rec, prop, claude_refine=False)
    # 정원/통창/주차 강점이 적합이유/DM에 반영
    assert any(w in kit.why_fit for w in ("정원", "통창", "주차", "야외"))
