"""CSV 출력 — 구글시트 붙여넣기/엑셀 호환. 내부 DB·리포트의 1차 산출물.

utf-8-sig(BOM)로 저장해 엑셀/구글시트 한글 깨짐을 막는다.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Sequence

from sseomlab.concept.models import ProposalRecord
from sseomlab.demand.models import (
    AdRecommendation,
    DemandForecast,
    OpportunityReport,
    SupplyShortage,
)
from sseomlab.models import PlaceRecord
from sseomlab.sales.models import SalesKit


def write_csv(path: str | Path, header: Sequence[str], rows: Sequence[Sequence]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    return path


_SPACE_HEADER = [
    "연락우선순위", "등급", "공간명", "공간유형", "지역", "세부지역", "주소", "연락처",
    "인스타", "네이버리뷰", "종합점수", "웨딩적합도", "돌상적합도", "숨은공간", "협업가능성", "추천제안",
]


def _space_row(r: PlaceRecord) -> list:
    p, a, s = r.place, r.analysis, r.score
    return [
        r.contact_priority, s.grade.value, p.name, a.space_type.value, p.region, p.sub_area,
        p.road_address or p.address, p.phone, p.instagram_url, p.naver_review_count,
        s.composite_score, s.wedding_conversion_score, s.dolsang_conversion_score,
        s.hidden_space_score, s.collaboration_probability, s.recommended_offer,
    ]


def export_space_db(records: list[PlaceRecord], path: str | Path) -> Path:
    rows = [_space_row(r) for r in sorted(records, key=lambda r: r.contact_priority)]
    return write_csv(path, _SPACE_HEADER, rows)


def export_a_grade(records: list[PlaceRecord], path: str | Path) -> Path:
    a = [r for r in records if r.score.grade.value == "A"]
    rows = [_space_row(r) for r in sorted(a, key=lambda r: r.contact_priority)]
    return write_csv(path, _SPACE_HEADER, rows)


_PROPOSAL_HEADER = [
    "연락우선순위", "공간명", "지역", "공간유형", "컨셉카테고리", "웨딩적합도", "돌상적합도",
    "협업가능성", "예상고객층", "추천웨딩컨셉", "추천돌상컨셉", "필요한연출요소",
    "컬러팔레트", "레퍼런스키워드", "제안서컨셉문구", "리스크",
]


def export_proposals(proposals: list[ProposalRecord], path: str | Path) -> Path:
    def row(p: ProposalRecord) -> list:
        return [
            p.contact_priority, p.space_name, p.region, p.space_type, p.concept_category,
            p.wedding_fit, p.dolsang_fit, p.collaboration_probability, p.target_customer,
            " | ".join(p.wedding_concepts), " | ".join(p.dol_concepts), " | ".join(p.production_elements),
            ", ".join(p.color_palette), ", ".join(p.reference_keywords), p.proposal_copy,
            " | ".join(p.risks),
        ]
    rows = [row(p) for p in sorted(proposals, key=lambda p: p.contact_priority)]
    return write_csv(path, _PROPOSAL_HEADER, rows)


# --- 수요예측 / 공급부족 / 기회 리포트 ---------------------------------------
def export_demand(forecasts: list[DemandForecast], path: str | Path) -> Path:
    header = ["수요월", "지역", "출생월", "출생아수", "예상이벤트", "예상계약", "예상매출(원)", "신뢰도"]
    rows = [[
        f"{f.demand_year}-{f.demand_month:02d}", f.region,
        f"{f.source_birth_year}-{f.source_birth_month:02d}", f.births,
        f.expected_events, f.expected_jade_bookings, int(f.expected_revenue_krw),
        "관측기반" if f.confidence == "recorded" else "투영기반",
    ] for f in forecasts]
    return write_csv(path, header, rows)


def export_ad_plan(recs: list[AdRecommendation], path: str | Path) -> Path:
    header = ["수요월", "광고집중시작", "광고집중종료", "예상계약", "예산강도", "근거"]
    rows = [[
        f"{r.target_demand_year}-{r.target_demand_month:02d}", r.ad_window_start,
        r.ad_window_end, r.expected_jade_bookings, r.intensity, r.rationale,
    ] for r in recs]
    return write_csv(path, header, rows)


def export_supply(shortages: list[SupplyShortage], path: str | Path) -> Path:
    header = ["월", "지역", "성수기", "웨딩홀계수", "예상돌잔치수요", "웨딩홀수용가능",
              "숨은공간필요수요", "확보숨은공간", "부족분", "추천액션"]
    rows = [[
        f"{s.year}-{s.month:02d}", s.region, "성수기" if s.is_peak_season else "비수기",
        s.seasonality_factor, s.total_demand_events, s.hall_available,
        s.hidden_need, s.hidden_secured, s.shortfall, s.action_text,
    ] for s in shortages]
    return write_csv(path, header, rows)


_SALES_HEADER = [
    "연락우선순위", "등급", "공간명", "지역", "우선연락시점", "한줄평가", "적합이유",
    "핵심이익(사장님)", "평일유휴제안", "샘플촬영제안", "DM문구", "전화스크립트",
    "제안서제목", "추천상품명", "예상판매상품", "예상객단가(원)",
]


def export_sales(kits: list[SalesKit], path: str | Path) -> Path:
    rows = [[
        k.contact_priority, k.grade, k.space_name, k.region, k.contact_timing,
        k.one_line_eval, k.why_fit, k.owner_benefit, k.weekday_idle_offer,
        k.sample_shoot_offer, k.dm_message, k.phone_script, k.proposal_title,
        k.product_name, " | ".join(k.expected_products), k.expected_avg_price_krw,
    ] for k in sorted(kits, key=lambda k: k.contact_priority)]
    return write_csv(path, _SALES_HEADER, rows)


def export_opportunity(reports: list[OpportunityReport], path: str | Path) -> Path:
    header = ["지역", "연간숨은수요", "연간수용량", "연간부족", "성수기부족",
              "부족월수", "A등급후보수", "확보추천유형", "메모"]
    rows = [[
        r.region, r.annual_hidden_demand, r.annual_capacity, r.annual_shortfall,
        r.peak_shortfall, len(r.shortfall_months), r.a_grade_candidates,
        ", ".join(r.recommended_types), r.note,
    ] for r in reports]
    return write_csv(path, header, rows)
