"""CSV 기반 공간 수집기 (목업/오프라인 모드).

네이버 API 키 없이도 전 구간을 돌리기 위한 입력원.
샘플: data/sample_candidates.csv
컬럼: name,region,sub_area,category,address,phone,instagram_url,homepage,
      naver_review_count,features,notes
features 는 ';' 구분 토큰(정원;통창;주차;독채 ...)으로, 분석기가 신호로 해석한다.
"""

from __future__ import annotations

import csv
from pathlib import Path

from sseomlab.models import Place

DEFAULT_SAMPLE = "data/sample_candidates.csv"


def load(path: str | Path = DEFAULT_SAMPLE) -> list[Place]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"공간 후보 CSV 없음: {path}")
    out: list[Place] = []
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            features = (row.get("features") or "").replace(";", " ")
            out.append(
                Place(
                    source="csv",
                    name=row["name"].strip(),
                    category=(row.get("category") or "").strip() or None,
                    region=(row.get("region") or "").strip() or None,
                    sub_area=(row.get("sub_area") or "").strip() or None,
                    address=(row.get("address") or "").strip() or None,
                    road_address=(row.get("address") or "").strip() or None,
                    phone=(row.get("phone") or "").strip() or None,
                    homepage=(row.get("homepage") or "").strip() or None,
                    instagram_url=(row.get("instagram_url") or "").strip() or None,
                    naver_review_count=int(row["naver_review_count"]) if row.get("naver_review_count") else None,
                    raw_text=f"{row['name']} {row.get('category','')} {features} {row.get('notes','')}".strip(),
                )
            )
    return out
