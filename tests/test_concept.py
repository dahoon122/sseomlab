from sseomlab.concept import catalog, recommender
from sseomlab.models import (
    Grade,
    Place,
    PlaceAnalysis,
    PlaceRecord,
    PlaceScore,
    SpaceType,
)


def test_space_type_maps_to_category():
    assert catalog.category_for_space_type("한옥카페") == "한옥/고택형"
    assert catalog.category_for_space_type("오션뷰카페") == "오션뷰형"


def test_all_categories_have_required_fields():
    for cat in catalog.list_categories():
        p = catalog.get_profile(cat)
        assert p.wedding_concepts and p.dol_concepts
        assert p.color_palette and p.risks and p.reference_keywords
        assert p.proposal_copy


def _record(space_type: SpaceType, ocean=False) -> PlaceRecord:
    place = Place(source="t", name="테스트공간", region="부산", sub_area="기장")
    analysis = PlaceAnalysis(space_type=space_type, has_ocean_view=ocean, parking_likelihood=0.8)
    score = PlaceScore(hidden_space_score=70, wedding_conversion_score=80, dolsang_conversion_score=60,
                       collaboration_probability=72, composite_score=73, grade=Grade.A)
    return PlaceRecord(place=place, analysis=analysis, score=score, contact_priority=1)


def test_build_proposal_has_12_fields():
    rec = _record(SpaceType.오션뷰카페, ocean=True)
    p = recommender.build_proposal(rec, claude_refine=False)
    assert p.space_name == "테스트공간"
    assert p.concept_category == "오션뷰형"
    assert "선셋 웨딩" in p.wedding_concepts
    assert any("선셋" in e for e in p.production_elements)  # 오션뷰 신호 반영
    assert p.contact_priority == 1
