"""지역별 사업 기회 리포트 — 공급부족 + 발굴 현황을 종합한다.

부족이 큰 지역 = 공간 확보 우선 지역. 성수기 부족이 크면 성수기 집중 확보 신호.
"""

from __future__ import annotations

from sseomlab.config import get_demand
from sseomlab.demand._dates import ym_label
from sseomlab.demand.models import OpportunityReport, SupplyShortage


def build(
    shortages: list[SupplyShortage],
    a_grade_counts: dict[str, int] | None = None,
) -> list[OpportunityReport]:
    a_grade_counts = a_grade_counts or {}
    peak_months = set(get_demand()["seasonality"]["wedding_peak_months"])

    by_region: dict[str, list[SupplyShortage]] = {}
    for s in shortages:
        by_region.setdefault(s.region, []).append(s)

    reports: list[OpportunityReport] = []
    for region, items in by_region.items():
        annual_hidden = sum(s.hidden_need for s in items)
        annual_cap = sum(s.hidden_secured for s in items)
        annual_short = sum(s.shortfall for s in items)
        peak_short = sum(s.shortfall for s in items if s.month in peak_months)
        short_months = [ym_label(s.year, s.month) for s in items if s.shortfall > 0]
        rec_types = next((s.recommended_types for s in items if s.recommended_types), [])

        if annual_short <= 0:
            note = "공급 충분 — 신규 확보 우선순위 낮음."
        elif peak_short > annual_short * 0.5:
            note = f"성수기 부족 집중({peak_short:.0f}건) — 성수기 대비 숨은 공간 선확보 권장."
        else:
            note = f"연중 상시 부족({annual_short:.0f}건) — 지속 확보 필요."

        reports.append(
            OpportunityReport(
                region=region,
                annual_hidden_demand=round(annual_hidden, 1),
                annual_capacity=round(annual_cap, 1),
                annual_shortfall=round(annual_short, 1),
                peak_shortfall=round(peak_short, 1),
                shortfall_months=short_months,
                a_grade_candidates=a_grade_counts.get(region, 0),
                recommended_types=rec_types,
                note=note,
            )
        )
    reports.sort(key=lambda r: r.annual_shortfall, reverse=True)
    return reports
