from pathlib import Path

from openpyxl import load_workbook

from sseomlab.pipeline import run


def test_dry_run_produces_excel(tmp_path: Path):
    out = tmp_path / "result.xlsx"
    path = run(dry_run=True, out_path=out)
    assert path.exists()

    wb = load_workbook(path)
    ws = wb.active
    # 헤더 + 유망 후보 1건 (웨딩홀은 제외되어야 함)
    assert ws.max_row == 2
    assert ws.cell(row=2, column=2).value == "A"  # 등급
    assert ws.cell(row=2, column=1).value == 1     # 우선순위
