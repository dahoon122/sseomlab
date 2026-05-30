from sseomlab.demand import ad_timing, calibration, forecaster
from sseomlab.demand._dates import add_months
from sseomlab.demand.models import BirthRecord, FunnelRates, JadeActuals


def test_dol_shift_is_12_months():
    rec = BirthRecord(region="대구", year=2024, month=3, births=1000, source="kosis")
    out = forecaster.forecast([rec], FunnelRates(
        event_rate=0.5, serviceable_share=0.5, capture_rate=0.04,
        inquiry_to_contract=0.3, avg_revenue_per_event_krw=3_000_000))
    f = out[0]
    assert (f.demand_year, f.demand_month) == (2025, 3)  # +12개월
    # 1000 * 0.5 * 0.5 = 250 이벤트, * 0.04 = 10 계약
    assert f.expected_events == 250.0
    assert f.expected_jade_bookings == 10.0
    assert f.confidence == "recorded"


def test_projection_marked_projected():
    recs = [BirthRecord(region="대구", year=2024, month=m, births=1000, source="kosis")
            for m in range(1, 13)]
    proj = forecaster.project_future_births(recs, horizon_months=6, yoy_factor=0.9)
    assert len(proj) == 6
    assert all(p.source == "projected" for p in proj)
    assert proj[0].births == 900  # 1000 * 0.9


def test_ad_window_precedes_demand():
    rec = BirthRecord(region="대구", year=2024, month=1, births=1000, source="kosis")
    fc = forecaster.forecast([rec])
    recs = ad_timing.recommend(fc)
    r = recs[0]
    # 수요월 2025-01, planning_lead=3 + ad_lead=1 → 광고 시작 2024-09, 종료 2024-10
    assert r.ad_window_start == "2024-09"
    assert r.ad_window_end == "2024-10"


def test_calibration_backs_out_capture():
    rec = BirthRecord(region="대구", year=2024, month=1, births=1000, source="kosis")
    fc = forecaster.forecast([rec])  # demand 2025-01
    events = fc[0].expected_events
    actuals = [JadeActuals(year=2025, month=1, region="대구", inquiries=100, contracts=10)]
    result = calibration.calibrate(fc, actuals)
    assert result.months_compared == 1
    assert abs(result.implied_capture_rate - 10 / events) < 1e-4  # 5자리 반올림 허용
    assert result.implied_inquiry_to_contract == 0.1


def test_add_months_wraps_year():
    assert add_months(2024, 11, 3) == (2025, 2)
    assert add_months(2025, 1, -4) == (2024, 9)
