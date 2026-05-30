"""광고 투입 시점 추천.

가족은 돌 D-planning_lead 개월에 문의를 시작하고, 광고는 ad_lead 개월 먼저 효과가 난다.
따라서 수요월 T 를 잡으려면 광고 집중 구간 ≈ [T-(planning_lead+ad_lead), T-planning_lead].
예상 계약 수가 큰 달일수록 예산 강도(intensity)를 높인다.
"""

from __future__ import annotations

from sseomlab.config import get_demand
from sseomlab.demand._dates import add_months, month_index, ym_label
from sseomlab.demand.models import AdRecommendation, DemandForecast


def recommend(forecasts: list[DemandForecast]) -> list[AdRecommendation]:
    cfg = get_demand()["ad_timing"]
    plan_lead = cfg["planning_lead_months"]
    ad_lead = cfg["ad_lead_months"]

    # 수요월별 예상 계약 합산 (전 지역)
    by_month: dict[int, tuple[int, int, float]] = {}
    for f in forecasts:
        idx = month_index(f.demand_year, f.demand_month)
        cur = by_month.get(idx, (f.demand_year, f.demand_month, 0.0))
        by_month[idx] = (f.demand_year, f.demand_month, cur[2] + f.expected_jade_bookings)

    if not by_month:
        return []
    peak = max(v[2] for v in by_month.values()) or 1.0

    recs: list[AdRecommendation] = []
    for idx in sorted(by_month):
        y, m, bookings = by_month[idx]
        ws_y, ws_m = add_months(y, m, -(plan_lead + ad_lead))
        we_y, we_m = add_months(y, m, -plan_lead)
        recs.append(
            AdRecommendation(
                target_demand_year=y,
                target_demand_month=m,
                ad_window_start=ym_label(ws_y, ws_m),
                ad_window_end=ym_label(we_y, we_m),
                expected_jade_bookings=round(bookings, 1),
                intensity=round(bookings / peak, 2),
                rationale=(
                    f"{ym_label(y, m)} 돌 수요(예상 계약 {bookings:.1f}건)를 잡으려면 "
                    f"{ym_label(ws_y, ws_m)}~{ym_label(we_y, we_m)}에 광고 집중."
                ),
            )
        )
    return recs
