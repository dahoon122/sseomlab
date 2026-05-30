"""PlaceRecord(공간 발굴 결과) → ProposalRecord(제안서 12필드).

기본은 concepts.yaml 기반 결정적 추천(=Claude 없이도 동작).
공간 분석 신호(정원/오션뷰/통창 등)를 반영해 '필요한 연출 요소'를 가감한다.
선택적으로 Claude 로 proposal_copy 를 공간 맞춤 1줄로 다듬을 수 있다(refine_with_claude).
"""

from __future__ import annotations

from sseomlab.concept import catalog
from sseomlab.concept.models import ProposalRecord
from sseomlab.models import PlaceRecord


def _production_elements(profile, analysis) -> list[str]:
    """카테고리 기본 연출 + 공간 신호 기반 가감."""
    elems = [
        f"플라워: {profile.flower_direction}",
        f"테이블: {profile.table_setting}",
        f"의자: {profile.chair_style}",
        f"포토존: {', '.join(profile.photozone_ideas)}",
    ]
    if analysis.has_large_window:
        elems.append("통창 자연광 활용 — 별도 조명 최소화")
    if analysis.has_ocean_view:
        elems.append("일몰 시간표 기준 타임라인 (선셋 연출)")
    if analysis.has_garden or analysis.has_yard:
        elems.append("우천 대비 실내 대체동선/타프 준비")
    if analysis.has_hanok:
        elems.append("좌식 보조석(어르신·임산부) 및 화기 제한 확인")
    if analysis.has_private_room:
        elems.append("단독 룸 기준 룸별 세팅")
    if analysis.parking_likelihood < 0.4:
        elems.append("주차 대안(발렛/인근 주차장) 안내 필요")
    return elems


def build_proposal(record: PlaceRecord, claude_refine: bool = False) -> ProposalRecord:
    place, analysis, score = record.place, record.analysis, record.score
    category = catalog.category_for_space_type(analysis.space_type.value)
    profile = catalog.get_profile(category)

    copy = profile.proposal_copy
    if claude_refine:
        copy = refine_with_claude(place.name, profile, analysis)

    return ProposalRecord(
        space_name=place.name,
        region=f"{place.region or ''} {place.sub_area or ''}".strip(),
        space_type=analysis.space_type.value,
        wedding_fit=score.wedding_conversion_score,
        dolsang_fit=score.dolsang_conversion_score,
        collaboration_probability=score.collaboration_probability,
        concept_category=category,
        target_customer=profile.target_customer,
        wedding_concepts=profile.wedding_concepts,
        dol_concepts=profile.dol_concepts,
        production_elements=_production_elements(profile, analysis),
        reference_keywords=profile.reference_keywords,
        proposal_copy=copy,
        contact_priority=record.contact_priority,
        color_palette=profile.color_palette,
        risks=profile.risks,
    )


def refine_with_claude(space_name: str, profile, analysis) -> str:
    """공간 맞춤 제안서 컨셉 문구 1줄을 Claude 로 생성(선택). 키 없으면 기본 문구 반환."""
    from sseomlab.config import get_settings

    s = get_settings()
    if not s.anthropic_api_key:
        return profile.proposal_copy

    from anthropic import Anthropic

    client = Anthropic(api_key=s.anthropic_api_key)
    prompt = (
        f"공간명 '{space_name}', 컨셉 카테고리 '{profile.category}', "
        f"추천 웨딩 컨셉 {profile.wedding_concepts}. "
        "제이드컴퍼니 제안서에 넣을 감성적이고 설득력 있는 컨셉 문구를 한국어 한 줄로만 써라."
    )
    resp = client.messages.create(
        model=s.anthropic_screening_model,
        max_tokens=120,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text.strip()
