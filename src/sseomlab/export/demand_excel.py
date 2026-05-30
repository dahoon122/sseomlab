"""수요예측 결과 엑셀 출력: 수요예측 / 광고계획 / 보정요약 시트."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from sseomlab.demand.models import AdRecommendation, CalibrationResult, DemandForecast

_HEADER_FILL = PatternFill("solid", fgColor="404040")
_PROJ_FILL = PatternFill("solid", fgColor="FFF2CC")  # 투영 구간 강조


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

    wb.save(out_path)
    return out_path
