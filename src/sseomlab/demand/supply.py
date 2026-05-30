"""공급 부족 예측 — 웨딩 성수기 로직 반영.

핵심 시장 규칙(대구 기준):
  웨딩 성수기(3-5월, 9-11월)에는 호텔/웨딩홀이 웨딩에 집중 →
  돌잔치 고객이 카페·독채·한옥 등 '숨은 공간'으로 이동 →
  숨은 공간을 필요로 하는 돌잔치 수요 비중(hidden_share)이 평월보다 커진다.

따라서 hidden_demand = 전체 돌잔치 이벤트 × hidden_share(월),
shortfall = max(0, hidden_demand - 숨은공간 수용량).
"""

from __future__ import annotations

import csv
from pathlib import Path

from sseomlab.config import get_demand
from sseomlab.demand._dates import month_index
from sseomlab.demand.models import DemandForecast, SupplyShortage


def load_capacity_csv(path: str | Path) -> dict[str, float]:
    """region,monthly_hidden_capacity CSV → {region: capacity}. 없으면 빈 dict."""
    path = Path(path)
    if not path.exists():
        return {}
    out: dict[str, float] = {}
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            out[row["region"].strip()] = float(row["monthly_hidden_capacity"])
    return out


def predict(
    forecasts: list[DemandForecast],
    capacity_csv: str | Path = "data/venue_capacity.csv",
) -> list[SupplyShortage]:
    cfg = get_demand()
    seas = cfg["seasonality"]
    peak_months = set(seas["wedding_peak_months"])
    share_base, share_peak = seas["hidden_share_base"], seas["hidden_share_peak"]
    rec_types = cfg["supply"]["acquisition_recommend_types"]
    default_cap = cfg["supply"]["default_monthly_hidden_capacity"]
    cap_override = load_capacity_csv(capacity_csv)

    # (지역, 월) 별 전체 돌잔치 이벤트 수요 집계
    agg: dict[tuple[str, int], tuple[int, int, float]] = {}
    for f in forecasts:
        idx = month_index(f.demand_year, f.demand_month)
        cur = agg.get((f.region, idx), (f.demand_year, f.demand_month, 0.0))
        agg[(f.region, idx)] = (f.demand_year, f.demand_month, cur[2] + f.expected_events)

    out: list[SupplyShortage] = []
    for (region, _idx), (y, m, events) in agg.items():
        is_peak = m in peak_months
        share = share_peak if is_peak else share_base
        hidden = events * share
        capacity = float(cap_override.get(region, default_cap.get(region, 0)))
        shortfall = max(0.0, hidden - capacity)
        out.append(
            SupplyShortage(
                region=region, year=y, month=m, is_peak_season=is_peak,
                total_demand_events=round(events, 1),
                hidden_demand=round(hidden, 1),
                capacity=capacity,
                shortfall=round(shortfall, 1),
                recommended_types=rec_types if shortfall > 0 else [],
            )
        )
    out.sort(key=lambda s: (month_index(s.year, s.month), s.region))
    return out
