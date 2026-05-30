"""전체 파이프라인 오케스트레이션.

수집 → 1차 제외필터 → 정보보강 → Claude 판정/점수 → 우선순위 → 엑셀 출력

dry_run=True 면 외부 API 없이 가짜 데이터로 전 구간 배선을 검증한다(설계 확인용).
"""

from __future__ import annotations

from pathlib import Path

from sseomlab.analyze import exclusion
from sseomlab.collect import enrich, naver_local
from sseomlab.concept import recommender
from sseomlab.export import excel, proposal_excel
from sseomlab.models import Grade, Place, PlaceAnalysis, PlaceRecord, PlaceScore, SpaceType
from sseomlab.score import scorer


def _assign_priority(records: list[PlaceRecord]) -> list[PlaceRecord]:
    """종합점수 내림차순으로 연락 우선순위(1..N) 부여."""
    ranked = sorted(records, key=lambda r: r.score.composite_score, reverse=True)
    for i, r in enumerate(ranked, start=1):
        r.contact_priority = i
    return ranked


def _fake_places() -> list[Place]:
    return [
        Place(source="dry_run", name="가창 숲속정원 카페", category="카페", region="대구",
              sub_area="가창", road_address="대구 달성군 가창면 ...", naver_review_count=180,
              raw_text="넓은 정원과 통창, 주차 가능. 평일 한산. 단체 모임 환영."),
        Place(source="dry_run", name="해운대 그랜드 웨딩홀", category="예식장", region="부산",
              sub_area="해운대", naver_review_count=1200, raw_text="예식장 웨딩홀 본식 전문"),
    ]


def run(
    regions: list[str] | None = None,
    space_types: list[str] | None = None,
    out_path: str | Path = "data/output/sseomlab_result.xlsx",
    proposal_path: str | Path | None = "data/output/sseomlab_proposals.xlsx",
    dry_run: bool = False,
    limit: int | None = None,
) -> Path:
    # 1) 수집
    places = _fake_places() if dry_run else naver_local.collect(regions, space_types)
    if limit:
        places = places[:limit]

    records: list[PlaceRecord] = []
    for place in places:
        # 2) 규칙 기반 1차 제외
        scr = exclusion.screen(place)
        if scr.exclude:
            continue

        # 3) 정보 보강
        place = place if dry_run else enrich.enrich(place)

        # 4) Claude 판정/점수
        if dry_run:
            analysis, score = _dry_score(place)
        else:
            analysis, score = scorer.score_place(place, scr.soft_hits)

        if analysis.exclude:
            continue

        records.append(PlaceRecord(place=place, analysis=analysis, score=score, contact_priority=0))

    # 5) 우선순위
    records = _assign_priority(records)

    # 6) 출력: 점수표 + 컨셉 제안서(12필드)
    out = excel.export(records, out_path)
    if proposal_path:
        proposals = [recommender.build_proposal(r, claude_refine=not dry_run) for r in records]
        proposal_excel.export(proposals, proposal_path)
    return out


def _dry_score(place: Place) -> tuple[PlaceAnalysis, PlaceScore]:
    """dry_run 용 결정적 가짜 점수."""
    good = "정원" in place.raw_text or "통창" in place.raw_text
    s = dict(
        hidden_space_score=70 if good else 20,
        wedding_conversion_score=78 if good else 10,
        dolsang_conversion_score=66 if good else 10,
        collaboration_probability=72 if good else 15,
    )
    composite = round(0.3 * s["wedding_conversion_score"] + 0.2 * s["dolsang_conversion_score"]
                      + 0.2 * s["hidden_space_score"] + 0.3 * s["collaboration_probability"], 1)
    analysis = PlaceAnalysis(exclude=not good, exclude_reason="" if good else "전환요소 부족",
                             space_type=SpaceType.숲속카페 if good else SpaceType.기타)
    score = PlaceScore(**s, composite_score=composite,
                       grade=Grade.A if composite >= 70 else Grade.D,
                       recommended_offer="평일 오후 웨딩/돌상 대관 제휴 제안" if good else "")
    return analysis, score
