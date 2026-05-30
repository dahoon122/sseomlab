"""제이드 실적과 비교해 깔때기 전환율을 보정한다.

예측이 만든 '지역 전체 돌잔치 이벤트 수요'(expected_events)와
제이드 실제 계약/문의를 같은 월에 맞춰 비교 →
  implied_capture_rate = Σ실제계약 / Σ예상이벤트
  implied_inquiry_to_contract = Σ계약 / Σ문의
보정된 FunnelRates 를 돌려준다. 이후 forecast 를 이 값으로 재실행하면 정확도가 오른다.
"""

from __future__ import annotations

from sseomlab.demand._dates import month_index
from sseomlab.demand.forecaster import load_funnel
from sseomlab.demand.models import (
    CalibrationResult,
    DemandForecast,
    FunnelRates,
    JadeActuals,
)


def calibrate(forecasts: list[DemandForecast], actuals: list[JadeActuals]) -> CalibrationResult:
    base = load_funnel()

    # 예상 이벤트를 (지역, 월) 및 (월) 단위로 집계
    by_region_month: dict[tuple[str, int], float] = {}
    by_month: dict[int, float] = {}
    for f in forecasts:
        idx = month_index(f.demand_year, f.demand_month)
        by_region_month[(f.region, idx)] = by_region_month.get((f.region, idx), 0.0) + f.expected_events
        by_month[idx] = by_month.get(idx, 0.0) + f.expected_events

    total_contracts = 0
    total_inquiries = 0
    matched_events = 0.0
    months = set()

    for a in actuals:
        idx = month_index(a.year, a.month)
        if a.region:
            exp = by_region_month.get((a.region, idx))
        else:
            exp = by_month.get(idx)
        if exp is None:
            continue  # 비교 대상 예측 없음
        matched_events += exp
        total_contracts += a.contracts
        total_inquiries += a.inquiries
        months.add(idx)

    implied_capture = (total_contracts / matched_events) if matched_events else base.capture_rate
    implied_i2c = (total_contracts / total_inquiries) if total_inquiries else base.inquiry_to_contract

    calibrated = FunnelRates(
        event_rate=base.event_rate,
        serviceable_share=base.serviceable_share,
        capture_rate=round(implied_capture, 5),
        inquiry_to_contract=round(implied_i2c, 4),
        avg_revenue_per_event_krw=base.avg_revenue_per_event_krw,
    )
    note = (
        f"{len(months)}개 월 실적과 비교. "
        f"capture {base.capture_rate}→{calibrated.capture_rate}, "
        f"문의→계약 {base.inquiry_to_contract}→{calibrated.inquiry_to_contract}."
        if months
        else "겹치는 월이 없어 기본값 유지."
    )
    return CalibrationResult(
        calibrated=calibrated,
        implied_capture_rate=calibrated.capture_rate,
        implied_inquiry_to_contract=calibrated.inquiry_to_contract,
        months_compared=len(months),
        note=note,
    )
