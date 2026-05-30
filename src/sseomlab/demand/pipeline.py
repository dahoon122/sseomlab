"""수요예측 파이프라인.

출생아 수집 → 미래 투영 → 돌잔치 수요/매출 예측 → (실적 보정) → 광고 타이밍 → 엑셀.
dry_run 이면 KOSIS 없이 합성 출생 시계열로 전 구간을 검증한다.
"""

from __future__ import annotations

import math
from pathlib import Path

from sseomlab.config import get_demand
from sseomlab.demand import ad_timing, calibration, forecaster, kosis, opportunity, supply
from sseomlab.demand.actuals import load_actuals_csv
from sseomlab.demand.models import BirthRecord, DemandForecast
from sseomlab.export import csv_out, demand_excel


def _synthetic_births(regions: list[str]) -> list[BirthRecord]:
    """계절성 + 완만한 감소를 가진 24개월 합성 출생 시계열 (dry-run)."""
    base = {"대구": 900, "경북": 800, "부산": 1200, "경남": 1100, "강원": 350}
    out: list[BirthRecord] = []
    for region in regions:
        b0 = base.get(region, 600)
        for k in range(24):
            y, m = 2024 + k // 12, k % 12 + 1
            seasonal = 1 + 0.08 * math.cos((m - 2) / 12 * 2 * math.pi)
            trend = 0.96 ** (k / 12)
            out.append(BirthRecord(region=region, year=y, month=m,
                                   births=int(b0 * seasonal * trend), source="kosis"))
    return out


def run(
    regions: list[str] | None = None,
    actuals_csv: str | Path = "data/jade_actuals.csv",
    capacity_csv: str | Path = "data/venue_capacity.csv",
    out_path: str | Path = "data/output/demand_forecast.xlsx",
    a_grade_counts: dict[str, int] | None = None,
    dry_run: bool = False,
) -> Path:
    cfg = get_demand()
    region_list = regions or list(cfg["regions"].keys())

    # 1) 출생아 수집
    births = _synthetic_births(region_list) if dry_run else kosis.collect_births(region_list)

    # 2) 미래 출생 투영
    proj = cfg["projection"]
    births += forecaster.project_future_births(births, proj["horizon_months"], proj["birth_yoy_factor"])

    # 3) 1차 예측 (기본 깔때기)
    forecasts: list[DemandForecast] = forecaster.forecast(births)

    # 4) 실적 보정 → 재예측
    actuals = load_actuals_csv(actuals_csv)
    calib = calibration.calibrate(forecasts, actuals) if actuals else None
    if calib:
        forecasts = forecaster.forecast(births, calib.calibrated)

    # 5) 광고 타이밍
    ad_recs = ad_timing.recommend(forecasts)

    # 6) 공급 부족 예측 (웨딩 성수기 로직) + 지역별 기회 리포트
    shortages = supply.predict(forecasts, capacity_csv)
    opportunities = opportunity.build(shortages, a_grade_counts)

    # 7) 출력: 엑셀(다중시트) + 리포트 CSV
    out = demand_excel.export(forecasts, ad_recs, calib, out_path,
                              shortages=shortages, opportunities=opportunities)
    base = Path(out_path).parent
    csv_out.export_demand(forecasts, base / "수요예측.csv")
    csv_out.export_ad_plan(ad_recs, base / "광고계획.csv")
    csv_out.export_supply(shortages, base / "공급부족리포트.csv")
    csv_out.export_opportunity(opportunities, base / "지역별기회리포트.csv")
    return out
