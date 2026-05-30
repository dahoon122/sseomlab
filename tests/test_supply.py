"""공급부족(웨딩 성수기 로직) + 기회 리포트 테스트."""

from sseomlab.demand import opportunity, supply
from sseomlab.demand.models import DemandForecast


def _fc(region, year, month, events) -> DemandForecast:
    return DemandForecast(
        region=region, demand_year=year, demand_month=month,
        source_birth_year=year - 1, source_birth_month=month,
        births=int(events * 4), expected_events=events,
        expected_jade_bookings=events * 0.04, expected_revenue_krw=events * 0.04 * 3_000_000,
        confidence="recorded",
    )


def test_peak_season_raises_hidden_demand():
    # 동일 이벤트 수라도 성수기(5월)가 평월(7월)보다 숨은공간 수요가 크다.
    peak = supply.predict([_fc("대구", 2027, 5, 400)], capacity_csv="__none__")[0]
    off = supply.predict([_fc("대구", 2027, 7, 400)], capacity_csv="__none__")[0]
    assert peak.is_peak_season and not off.is_peak_season
    assert peak.hidden_demand > off.hidden_demand


def test_shortfall_and_recommendation():
    # 수요 큰 성수기 → 수용량 초과 → 부족 + 확보 추천 유형 제시
    s = supply.predict([_fc("대구", 2027, 5, 500)], capacity_csv="__none__")[0]
    assert s.shortfall > 0
    assert s.recommended_types  # 비어있지 않음


def test_opportunity_ranks_by_shortfall():
    fcs = [_fc("경남", 2027, 5, 500), _fc("강원", 2027, 5, 100)]
    shortages = supply.predict(fcs, capacity_csv="__none__")
    reports = opportunity.build(shortages, a_grade_counts={"경남": 2})
    assert reports[0].region == "경남"  # 부족 큰 지역이 먼저
    assert reports[0].a_grade_candidates == 2
