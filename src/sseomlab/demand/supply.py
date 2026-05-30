"""돌잔치 공급 부족 예측 (고도화) — 웨딩홀 겸업 seasonality 반영.

대구 시장 구조: 돌잔치 공간 상당수가 웨딩홀/호텔과 겸업.
  - 웨딩 성수기(3-5,9-11월): 웨딩홀이 웨딩에 집중 → 돌잔치 수용량 40~60%로 감소
  - 웨딩 비수기: 웨딩홀이 돌잔치 적극 수용 → 80~100% 회복

계산:
  예상 돌잔치 수요(total)            = expected_events
  웨딩홀/호텔 수용가능(hall_available) = hall_base_capacity × seasonality_factor(월)
  숨은공간 필요 수요(hidden_need)     = max(0, total - hall_available)
  현재 확보 숨은공간(hidden_secured)  = 제이드 확보 수용량
  부족분(shortfall)                  = max(0, hidden_need - hidden_secured)
  추천 액션                          = 부족분 ÷ 1곳당 수용량 → acquisition_mix 비율로 분배
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

from sseomlab.config import get_demand
from sseomlab.demand._dates import month_index
from sseomlab.demand.models import DemandForecast, SupplyShortage


def load_secured_capacity_csv(path: str | Path) -> dict[str, float]:
    """확보 숨은공간 수용량 CSV → {region: capacity}. 없으면 빈 dict.

    컬럼: region, hidden_secured_capacity (구 monthly_hidden_capacity 도 허용).
    """
    path = Path(path)
    if not path.exists():
        return {}
    out: dict[str, float] = {}
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            val = row.get("hidden_secured_capacity") or row.get("monthly_hidden_capacity")
            if val:
                out[row["region"].strip()] = float(val)
    return out


def _recommend_action(shortfall: float, per_space: float, mix: dict[str, int]) -> dict[str, int]:
    """부족분을 확보할 공간 수로 환산 후 유형별 비율로 분배 (최대잉여법)."""
    if shortfall <= 0:
        return {}
    total_spaces = max(1, math.ceil(shortfall / per_space))
    weight_sum = sum(mix.values())
    # 1차 배분 + 잔여를 가중치 큰 순으로 분배
    raw = {t: total_spaces * w / weight_sum for t, w in mix.items()}
    floored = {t: int(v) for t, v in raw.items()}
    remainder = total_spaces - sum(floored.values())
    for t in sorted(raw, key=lambda x: raw[x] - floored[x], reverse=True)[:remainder]:
        floored[t] += 1
    return {t: c for t, c in floored.items() if c > 0}


def predict(
    forecasts: list[DemandForecast],
    capacity_csv: str | Path = "data/venue_capacity.csv",
) -> list[SupplyShortage]:
    cfg = get_demand()
    sup = cfg["supply"]
    peak_months = set(cfg["seasonality"]["wedding_peak_months"])
    factor_peak = sup["seasonality_factor"]["peak"]
    factor_off = sup["seasonality_factor"]["offseason"]
    hall_base = sup["hall_base_capacity"]
    secured_default = sup["hidden_secured_capacity"]
    per_space = sup["per_space_monthly_capacity"]
    mix = sup["acquisition_mix"]
    secured_override = load_secured_capacity_csv(capacity_csv)

    # (지역, 월) 별 예상 돌잔치 수요 집계
    agg: dict[tuple[str, int], tuple[int, int, float]] = {}
    for f in forecasts:
        idx = month_index(f.demand_year, f.demand_month)
        cur = agg.get((f.region, idx), (f.demand_year, f.demand_month, 0.0))
        agg[(f.region, idx)] = (f.demand_year, f.demand_month, cur[2] + f.expected_events)

    out: list[SupplyShortage] = []
    for (region, _idx), (y, m, demand) in agg.items():
        is_peak = m in peak_months
        factor = factor_peak if is_peak else factor_off
        hall_available = hall_base.get(region, 0) * factor
        hidden_need = max(0.0, demand - hall_available)
        secured = float(secured_override.get(region, secured_default.get(region, 0)))
        shortfall = max(0.0, hidden_need - secured)
        out.append(
            SupplyShortage(
                region=region, year=y, month=m, is_peak_season=is_peak,
                seasonality_factor=factor,
                total_demand_events=round(demand, 1),
                hall_available=round(hall_available, 1),
                hidden_need=round(hidden_need, 1),
                hidden_secured=secured,
                shortfall=round(shortfall, 1),
                recommended_action=_recommend_action(shortfall, per_space, mix),
            )
        )
    out.sort(key=lambda s: (month_index(s.year, s.month), s.region))
    return out
