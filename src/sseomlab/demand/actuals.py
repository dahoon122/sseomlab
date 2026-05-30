"""제이드 실적 CSV 로더.

기대 컬럼: year, month, region(선택), inquiries, contracts, revenue_krw
"""

from __future__ import annotations

import csv
from pathlib import Path

from sseomlab.demand.models import JadeActuals


def load_actuals_csv(path: str | Path) -> list[JadeActuals]:
    path = Path(path)
    if not path.exists():
        return []
    out: list[JadeActuals] = []
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            out.append(
                JadeActuals(
                    year=int(row["year"]),
                    month=int(row["month"]),
                    region=(row.get("region") or "").strip() or None,
                    inquiries=int(row.get("inquiries") or 0),
                    contracts=int(row.get("contracts") or 0),
                    revenue_krw=int(row.get("revenue_krw") or 0),
                )
            )
    return out
