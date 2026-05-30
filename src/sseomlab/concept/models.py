"""컨셉/제안서 데이터 모델."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ConceptProfile(BaseModel):
    """컨셉 카테고리 하나의 기획 레퍼런스 (concepts.yaml 1건)."""

    category: str
    target_customer: str
    wedding_concepts: list[str]
    dol_concepts: list[str]
    color_palette: list[str]
    flower_direction: str
    table_setting: str
    chair_style: str = ""
    photozone_ideas: list[str] = []
    photo_points: list[str]
    risks: list[str]
    reference_keywords: list[str]
    proposal_copy: str


class ProposalRecord(BaseModel):
    """제안서/영업 시트 한 행 — 사용자 요구 12개 필드."""

    # 1~5: 공간·점수
    space_name: str                          # 1. 공간명
    region: str                              # 2. 지역
    space_type: str                          # 3. 공간 유형
    wedding_fit: int                         # 4-a. 웨딩 적합도
    dolsang_fit: int                         # 4-b. 돌상 적합도
    collaboration_probability: int           # 5. 협업 가능성
    # 6~11: 컨셉 기획
    concept_category: str                    # (분류) 컨셉 카테고리
    target_customer: str                     # 6. 예상 고객층
    wedding_concepts: list[str]              # 7. 추천 웨딩 컨셉
    dol_concepts: list[str]                  # 8. 추천 돌상 컨셉
    production_elements: list[str]           # 9. 필요한 연출 요소
    reference_keywords: list[str]            # 10. 참고 레퍼런스 키워드
    proposal_copy: str                       # 11. 제안서 컨셉 문구
    # 12: 우선순위
    contact_priority: int = Field(description="1이 가장 먼저 연락")

    # 부가
    color_palette: list[str] = []
    risks: list[str] = []
