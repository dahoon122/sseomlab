"""SalesKit 생성 — PlaceRecord(점수) + ProposalRecord(컨셉)에서 영업 문구를 만든다.

기본은 템플릿 기반 결정적 생성(LLM 불필요). 선택적으로 Claude 로 DM/전화 문구를
공간 맞춤으로 다듬을 수 있다(refine_with_claude).
"""

from __future__ import annotations

from sseomlab.concept.models import ProposalRecord
from sseomlab.config import get_sales
from sseomlab.models import PlaceRecord
from sseomlab.sales.models import SalesKit

# 우선 연락 시점: 등급별 긴급도
_URGENCY = {
    "A": "즉시 컨택 (1주 내)",
    "B": "2주 내 컨택",
    "C": "관찰 후 비수기 진입 전 컨택",
    "D": "보류 (재평가 대상)",
}


def _strengths(analysis) -> list[str]:
    a = analysis
    out = []
    if a.has_garden or a.has_yard:
        out.append("정원·마당")
    if a.has_large_window:
        out.append("통창")
    if a.has_ocean_view:
        out.append("오션뷰")
    if a.has_hanok:
        out.append("한옥 분위기")
    if a.has_forest:
        out.append("숲 뷰")
    if a.has_private_room or a.private_event_possible:
        out.append("단독 프라이빗")
    if a.parking_likelihood >= 0.6:
        out.append("주차 용이")
    if a.outdoor_usable:
        out.append("야외 활용")
    return out or ["공간 분위기"]


def build_sales_kit(record: PlaceRecord, proposal: ProposalRecord, claude_refine: bool = False) -> SalesKit:
    cfg = get_sales()
    place, a, s = record.place, record.analysis, record.score
    cat = proposal.concept_category
    cat_cfg = cfg["categories"].get(cat, next(iter(cfg["categories"].values())))
    idle_window = cfg["default"]["weekday_idle_window"]
    prep = cfg["default"]["prep_lead_months"]

    strengths = _strengths(a)
    strengths_txt = "·".join(strengths[:3])   # 핵심 강점 3개만 노출
    name = place.name
    focus = "웨딩" if s.wedding_conversion_score >= s.dolsang_conversion_score else "돌잔치"
    price = cat_cfg["avg_price_krw"]
    product = cat_cfg["product_name"]

    one_line = (
        f"{place.region or ''} {a.space_type.value} · {cat} — "
        f"웨딩 {s.wedding_conversion_score}/돌상 {s.dolsang_conversion_score}, "
        f"협업 {s.collaboration_probability} ({s.grade.value}등급)"
    ).strip()

    why_fit = (
        f"{strengths_txt} 등으로 {cat} 컨셉의 웨딩·돌잔치 연출에 적합합니다. "
        f"추천 컨셉: {', '.join(proposal.wedding_concepts[:2])} / {', '.join(proposal.dol_concepts[:2])}."
    )

    owner_benefit = (
        f"{idle_window}의 유휴 시간대를 {focus} 대관으로 전환해 "
        f"비수기·평일 추가 매출을 만들 수 있습니다. 예상 객단가 약 {price // 10000}만원, "
        f"제이드가 송객·연출·운영을 전담하므로 사장님 추가 리스크는 거의 없습니다."
    )

    weekday_idle_offer = (
        f"{idle_window} 사이 2~3시간 단위 돌잔치/스몰웨딩 대관. "
        f"평일 1~2건만 추가해도 월 매출이 의미있게 늘어납니다."
    )

    sample_shoot_offer = (
        f"제이드 연출팀이 무료 샘플 촬영을 진행해 '{name}'의 {focus} 포텐셜을 "
        f"콘텐츠로 만들어 드립니다. 사장님은 결과물을 인스타·네이버 홍보에 그대로 쓰실 수 있어요."
    )

    dm_message = (
        f"안녕하세요 '{name}' 사장님, 웨딩·돌잔치 디렉팅을 하는 제이드컴퍼니입니다. "
        f"공간의 {strengths_txt} 분위기가 {cat} 웨딩·돌잔치에 정말 잘 어울려 연락드렸어요. "
        f"평일 유휴 시간대 대관 협업을 제안드리고 싶은데, 부담 없이 무료 샘플 촬영부터 "
        f"함께 해보실 수 있을까요? 😊"
    )

    phone_script = (
        f"[오프닝] 안녕하세요, '{name}' 사장님이실까요? 웨딩·돌잔치 디렉팅 업체 제이드컴퍼니입니다. "
        f"[훅] 공간이 {strengths_txt}이 있어서 웨딩·돌잔치 손님들이 좋아하실 분위기더라고요. "
        f"[제안] 저희가 평일 유휴 시간대에 손님을 모셔오고 연출·운영까지 맡는 대관 협업을 드리고 싶습니다. "
        f"사장님은 공간만 빌려주시면 추가 매출이 생기는 구조예요. "
        f"[클로징] 먼저 무료 샘플 촬영으로 결과물을 보여드릴게요. 이번 주 중 잠깐 들러도 될까요?"
    )

    proposal_title = f"[{name}] {cat} 웨딩·돌잔치 공간 상품화 제안"

    contact_timing = f"{_URGENCY[s.grade.value]} · 웨딩 성수기 대비 약 {prep}개월 전 확보 목표"

    kit = SalesKit(
        space_name=name,
        region=f"{place.region or ''} {place.sub_area or ''}".strip(),
        grade=s.grade.value,
        contact_priority=record.contact_priority,
        one_line_eval=one_line,
        why_fit=why_fit,
        owner_benefit=owner_benefit,
        weekday_idle_offer=weekday_idle_offer,
        sample_shoot_offer=sample_shoot_offer,
        dm_message=dm_message,
        phone_script=phone_script,
        proposal_title=proposal_title,
        product_name=product,
        expected_products=cat_cfg["expected_products"],
        expected_avg_price_krw=price,
        contact_timing=contact_timing,
    )
    if claude_refine:
        _refine(kit, record)
    return kit


def _refine(kit: SalesKit, record: PlaceRecord) -> None:
    """선택적 Claude 다듬기. 키 없으면 그대로 둔다."""
    from sseomlab.config import get_settings

    s = get_settings()
    if not s.anthropic_api_key:
        return
    from anthropic import Anthropic

    client = Anthropic(api_key=s.anthropic_api_key)
    prompt = (
        f"다음 DM 초안을 사장님이 답장하고 싶게 더 자연스럽고 친근한 한국어로 다듬어라. "
        f"한 문단, 이모지 1개 이하. 초안: {kit.dm_message}"
    )
    resp = client.messages.create(
        model=s.anthropic_screening_model, max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    kit.dm_message = resp.content[0].text.strip()
