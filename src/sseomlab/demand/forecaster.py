"""출생아 수 → 12개월 뒤 돌잔치 수요/매출 예측.

핵심: 돌 수요(demand_month) = 출생월 + dol_age_months(=12).
이미 집계된 출생아로 채워지는 구간은 confidence='recorded',
미래 출생을 투영(projection)해 채우는 구간은 confidence='projected'.
"""

from __future__ import annotations

from sseomlab.config import get_demand
from sseomlab.demand._dates import add_months, from_index, month_index
from sseomlab.demand.models import BirthRecord, DemandForecast, FunnelRates


def load_funnel() -> FunnelRates:
    f = get_demand()["funnel"]
    return FunnelRates(**f)


def project_future_births(records: list[BirthRecord], horizon_months: int, yoy_factor: float) -> list[BirthRecord]:
    """집계 구간 밖 미래 출생아 수를 전년동월×계수로 투영한다.

    저출산 추세를 단순 반영하는 1차 모델. 운영 시 더 정교한 인구추계로 대체 가능.
    """
    out: list[BirthRecord] = []
    by_region: dict[str, dict[int, int]] = {}
    for r in records:
        by_region.setdefault(r.region, {})[month_index(r.year, r.month)] = r.births

    for region, series in by_region.items():
        last_idx = max(series)
        for step in range(1, horizon_months + 1):
            idx = last_idx + step
            prev_year_idx = idx - 12
            if prev_year_idx in series:
                base = series[prev_year_idx]
            else:
                base = series[last_idx]  # 전년 데이터 없으면 마지막값 유지
            projected = int(round(base * yoy_factor))
            series[idx] = projected
            y, m = from_index(idx)
            out.append(BirthRecord(region=region, year=y, month=m, births=projected, source="projected"))
    return out


def forecast(records: list[BirthRecord], funnel: FunnelRates | None = None) -> list[DemandForecast]:
    """출생 기록(실측+투영)으로 돌잔치 수요/매출을 산출한다."""
    cfg = get_demand()
    dol = cfg["dol_age_months"]
    funnel = funnel or load_funnel()

    out: list[DemandForecast] = []
    for r in records:
        dy, dm = add_months(r.year, r.month, dol)
        events = r.births * funnel.event_rate * funnel.serviceable_share
        bookings = events * funnel.capture_rate
        revenue = bookings * funnel.avg_revenue_per_event_krw
        out.append(
            DemandForecast(
                region=r.region,
                demand_year=dy,
                demand_month=dm,
                source_birth_year=r.year,
                source_birth_month=r.month,
                births=r.births,
                expected_events=round(events, 1),
                expected_jade_bookings=round(bookings, 2),
                expected_revenue_krw=round(revenue),
                confidence="recorded" if r.source == "kosis" else "projected",
            )
        )
    out.sort(key=lambda f: (month_index(f.demand_year, f.demand_month), f.region))
    return out
