"""수요예측 결과 엑셀 출력: 수요예측 / 광고계획 / 보정요약 시트."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from sseomlab.demand.models import (
    AdRecommendation,
    CalibrationResult,
    DemandForecast,
    OpportunityReport,
    SupplyShortage,
)

_HEADER_FILL = PatternFill("solid", fgColor="404040")
_PROJ_FILL = PatternFill("solid", fgColor="FFF2CC")  # 투영 구간 강조
_SHORT_FILL = PatternFill("solid", fgColor="F8CBAD")  # 공급부족 강조
_PEAK_FILL = PatternFill("solid", fgColor="FCE4D6")   # 성수기 강조


def _style_header(ws):
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = _HEADER_FILL
        c.alignment = Alignment(horizontal="center")
    ws.freeze_panes = "A2"


def _autosize(ws):
    for col in ws.columns:
        w = max((len(str(c.value)) for c in col if c.value), default=10)
        ws.column_dimensions[col[0].column_letter].width = min(w + 2, 40)


def export(
    forecasts: list[DemandForecast],
    ad_recs: list[AdRecommendation],
    calib: Optional[CalibrationResult],
    out_path: str | Path,
    shortages: Optional[list[SupplyShortage]] = None,
    opportunities: Optional[list[OpportunityReport]] = None,
) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()

    # --- 시트1: 수요예측 ---
    ws = wb.active
    ws.title = "수요예측"
    ws.append(["수요월", "지역", "출생월", "출생아수", "예상이벤트", "예상계약", "예상매출(원)", "신뢰도"])
    for f in forecasts:
        ws.append([
            f"{f.demand_year}-{f.demand_month:02d}", f.region,
            f"{f.source_birth_year}-{f.source_birth_month:02d}", f.births,
            f.expected_events, f.expected_jade_bookings, int(f.expected_revenue_krw),
            "관측기반" if f.confidence == "recorded" else "투영기반",
        ])
        if f.confidence == "projected":
            ws.cell(row=ws.max_row, column=8).fill = _PROJ_FILL
    _style_header(ws)
    _autosize(ws)

    # --- 시트2: 광고계획 ---
    ws2 = wb.create_sheet("광고계획")
    ws2.append(["수요월", "광고집중 시작", "광고집중 종료", "예상계약", "예산강도", "근거"])
    for r in ad_recs:
        ws2.append([
            f"{r.target_demand_year}-{r.target_demand_month:02d}",
            r.ad_window_start, r.ad_window_end, r.expected_jade_bookings, r.intensity, r.rationale,
        ])
    _style_header(ws2)
    _autosize(ws2)

    # --- 시트3: 보정요약 ---
    ws3 = wb.create_sheet("보정요약")
    ws3.append(["항목", "값"])
    if calib:
        c = calib.calibrated
        rows = [
            ("비교한 월 수", calib.months_compared),
            ("보정 capture_rate", c.capture_rate),
            ("보정 문의→계약", c.inquiry_to_contract),
            ("event_rate", c.event_rate),
            ("serviceable_share", c.serviceable_share),
            ("건당 평균매출(원)", c.avg_revenue_per_event_krw),
            ("메모", calib.note),
        ]
    else:
        rows = [("실적 비교", "data/jade_actuals.csv 없음 — 기본 가정값 사용")]
    for k, v in rows:
        ws3.append([k, v])
    _style_header(ws3)
    _autosize(ws3)

    # --- 시트4: 공급부족리포트 ---
    if shortages is not None:
        ws4 = wb.create_sheet("공급부족리포트")
        ws4.append(["월", "지역", "성수기", "웨딩홀계수", "예상수요", "웨딩홀수용가능",
                    "숨은공간필요", "확보숨은공간", "부족분", "추천액션"])
        for s in shortages:
            ws4.append([
                f"{s.year}-{s.month:02d}", s.region, "성수기" if s.is_peak_season else "비수기",
                s.seasonality_factor, s.total_demand_events, s.hall_available,
                s.hidden_need, s.hidden_secured, s.shortfall, s.action_text,
            ])
            if s.shortfall > 0:
                ws4.cell(row=ws4.max_row, column=9).fill = _SHORT_FILL
            if s.is_peak_season:
                ws4.cell(row=ws4.max_row, column=3).fill = _PEAK_FILL
        _style_header(ws4)
        _autosize(ws4)

    # --- 시트5: 지역별기회리포트 ---
    if opportunities is not None:
        ws5 = wb.create_sheet("지역별기회리포트")
        ws5.append(["지역", "연간숨은수요", "연간수용량", "연간부족", "성수기부족",
                    "부족월수", "A등급후보", "확보추천유형", "메모"])
        for r in opportunities:
            ws5.append([
                r.region, r.annual_hidden_demand, r.annual_capacity, r.annual_shortfall,
                r.peak_shortfall, len(r.shortfall_months), r.a_grade_candidates,
                ", ".join(r.recommended_types), r.note,
            ])
            if r.annual_shortfall > 0:
                ws5.cell(row=ws5.max_row, column=4).fill = _SHORT_FILL
        _style_header(ws5)
        _autosize(ws5)

    wb.save(out_path)
    return out_path
