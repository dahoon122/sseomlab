from sseomlab.analyze import exclusion
from sseomlab.models import Place


def test_hard_keyword_excluded():
    p = Place(source="t", name="해운대 그랜드 웨딩홀", raw_text="예식장 본식 전문")
    r = exclusion.screen(p)
    assert r.exclude is True
    assert "웨딩홀" in r.reason


def test_normal_cafe_not_excluded():
    p = Place(source="t", name="가창 숲속정원 카페", raw_text="정원과 통창이 있는 카페")
    r = exclusion.screen(p)
    assert r.exclude is False
    assert r.soft_hits == []


def test_soft_keyword_flagged_not_excluded():
    p = Place(source="t", name="포레스트 카페", raw_text="가끔 웨딩촬영 오시는 분들 있어요")
    r = exclusion.screen(p)
    assert r.exclude is False
    assert "웨딩촬영" in r.soft_hits
