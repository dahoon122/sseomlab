"""수요예측 서브시스템 데이터 모델."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class BirthRecord(BaseModel):
    """KOSIS 월별 출생아 수 한 건."""

    region: str
    year: int
    month: int
    births: int
    source: Literal["kosis", "projected", "dry_run"] = "kosis"


class FunnelRates(BaseModel):
    """출생 → 돌잔치 이벤트 → 제이드 계약 → 매출 전환 가정값."""

    event_rate: float
    serviceable_share: float
    capture_rate: float
    inquiry_to_contract: float
    avg_revenue_per_event_krw: int


class DemandForecast(BaseModel):
    """특정 (지역, 수요월)의 돌잔치 수요/매출 예측."""

    region: str
    demand_year: int
    demand_month: int
    source_birth_year: int
    source_birth_month: int
    births: int
    expected_events: float           # 지역 전체 돌잔치 이벤트 수요
    expected_jade_bookings: float    # 제이드가 잡을 계약 수
    expected_revenue_krw: float
    confidence: Literal["recorded", "projected"]  # 출생 실측 기반 vs 출생 투영 기반


class JadeActuals(BaseModel):
    """제이드컴퍼니 실제 실적 (월·지역별)."""

    year: int
    month: int
    region: Optional[str] = None
    inquiries: int = 0
    contracts: int = 0
    revenue_krw: int = 0


class CalibrationResult(BaseModel):
    """실적 대비 보정 결과."""

    calibrated: FunnelRates
    implied_capture_rate: float
    implied_inquiry_to_contract: float
    months_compared: int
    note: str = ""


class AdRecommendation(BaseModel):
    """수요월 T 를 겨냥한 광고 투입 권고."""

    target_demand_year: int
    target_demand_month: int
    ad_window_start: str   # "YYYY-MM"
    ad_window_end: str
    expected_jade_bookings: float
    intensity: float = Field(ge=0, le=1, description="권장 예산 강도(피크=1.0 기준 정규화)")
    rationale: str = ""
