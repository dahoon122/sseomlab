"""컨셉 카탈로그 접근: 공간유형 → 컨셉 카테고리 분류, 카테고리 → 프로파일 조회."""

from __future__ import annotations

from sseomlab.concept.models import ConceptProfile
from sseomlab.config import get_concepts


def list_categories() -> list[str]:
    return list(get_concepts()["categories"].keys())


def category_for_space_type(space_type: str) -> str:
    """공간유형을 컨셉 카테고리로 매핑. 매핑 없으면 기본값."""
    cfg = get_concepts()
    mapping = cfg["space_type_to_category"]
    return mapping.get(space_type, mapping.get("기타", list_categories()[0]))


def get_profile(category: str) -> ConceptProfile:
    cfg = get_concepts()
    cats = cfg["categories"]
    if category not in cats:
        category = list(cats.keys())[0]
    return ConceptProfile(category=category, **cats[category])
