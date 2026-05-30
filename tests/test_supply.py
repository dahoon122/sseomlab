"""공급부족(웨딩홀 겸업 seasonality) + 기회 리포트 테스트."""

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


def test_peak_lowers_hall_capacity_and_raises_hidden_need():
    # 같은 수요라도 성수기(5월)엔 웨딩홀 수용↓ → 숨은공간 필요수요↑
    peak = supply.predict([_fc("대구", 2027, 5, 400)], capacity_csv="__none__")[0]
    off = supply.predict([_fc("대구", 2027, 7, 400)], capacity_csv="__none__")[0]
    assert peak.is_peak_season and not off.is_peak_season
    assert peak.seasonality_factor < off.seasonality_factor   # 0.5 < 0.9
    assert peak.hall_available < off.hall_available
    assert peak.hidden_need > off.hidden_need


def test_shortfall_breakdown_matches_demand_minus_supply():
    s = supply.predict([_fc("대구", 2027, 5, 500)], capacity_csv="__none__")[0]
    # 수요 - 웨딩홀수용 = 숨은공간필요; - 확보 = 부족분
    assert round(s.total_demand_events - s.hall_available, 1) == s.hidden_need
    assert round(s.hidden_need - s.hidden_secured, 1) == s.shortfall
    assert s.shortfall > 0


def test_recommended_action_uses_acquisition_mix():
    s = supply.predict([_fc("대구", 2027, 5, 500)], capacity_csv="__none__")[0]
    act = s.recommended_action
    assert act  # 비어있지 않음
    # 정원형이 가장 많이 추천(비율 3:2:1)
    assert act.get("정원형", 0) >= act.get("한옥/고택형", 0)
    assert "곳" in s.action_text


def test_offseason_may_have_no_shortfall():
    # 비수기 + 작은 수요 → 웨딩홀이 충분히 수용 → 부족 없음 가능
    s = supply.predict([_fc("대구", 2027, 7, 120)], capacity_csv="__none__")[0]
    assert s.shortfall == 0
    assert s.recommended_action == {}


def test_opportunity_ranks_by_shortfall():
    fcs = [_fc("경남", 2027, 5, 500), _fc("강원", 2027, 5, 120)]
    shortages = supply.predict(fcs, capacity_csv="__none__")
    reports = opportunity.build(shortages, a_grade_counts={"경남": 2})
    assert reports[0].region == "경남"
    assert reports[0].a_grade_candidates == 2
