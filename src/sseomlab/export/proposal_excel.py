"""제안서용 12필드 엑셀 출력. 공간 발굴 + 컨셉 추천을 합친 최종 영업 산출물."""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from sseomlab.concept.models import ProposalRecord

HEADERS = [
    "연락우선순위", "공간명", "지역", "공간유형", "컨셉카테고리",
    "웨딩적합도", "돌상적합도", "협업가능성", "예상고객층",
    "추천웨딩컨셉", "추천돌상컨셉", "필요한연출요소",
    "컬러팔레트", "레퍼런스키워드", "제안서컨셉문구", "리스크",
]


def _bullets(items: list[str]) -> str:
    return "\n".join(f"· {x}" for x in items)


def _row(p: ProposalRecord) -> list:
    return [
        p.contact_priority, p.space_name, p.region, p.space_type, p.concept_category,
        p.wedding_fit, p.dolsang_fit, p.collaboration_probability, p.target_customer,
        _bullets(p.wedding_concepts), _bullets(p.dol_concepts), _bullets(p.production_elements),
        ", ".join(p.color_palette), ", ".join(p.reference_keywords), p.proposal_copy,
        _bullets(p.risks),
    ]


def export(proposals: list[ProposalRecord], out_path: str | Path) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    proposals = sorted(proposals, key=lambda p: p.contact_priority)

    wb = Workbook()
    ws = wb.active
    ws.title = "제안서리스트"
    ws.append(HEADERS)
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="404040")
        c.alignment = Alignment(horizontal="center", vertical="center")

    wrap = Alignment(wrap_text=True, vertical="top")
    for p in proposals:
        ws.append(_row(p))
        for c in ws[ws.max_row]:
            c.alignment = wrap

    ws.freeze_panes = "B2"
    widths = [10, 18, 14, 12, 14, 9, 9, 9, 28, 24, 24, 30, 18, 24, 34, 30]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = w
    wb.save(out_path)
    return out_path
