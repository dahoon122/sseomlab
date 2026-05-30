"""통계청 KOSIS 월별 출생아 수 수집기.

KOSIS OpenAPI(인구동향조사 - 출생)에서 시도/시군구별 월별 출생아 수를 가져온다.
공식 API 이므로 ToS 부담이 낮다. API 키는 KOSIS_API_KEY.

엔드포인트/통계표 ID 는 KOSIS 메타에서 확정해 채운다(TODO 표시).
키가 없거나 미구현이면 RuntimeError 로 안내한다.
"""

from __future__ import annotations

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from sseomlab.config import get_demand, get_settings
from sseomlab.demand.models import BirthRecord

KOSIS_ENDPOINT = "https://kosis.kr/openapi/Param/statisticsParameterData.do"
# TODO: 인구동향조사 출생 통계표의 orgId/tblId/itmId/objL 파라미터를 확정해 채운다.
KOSIS_PARAMS_TEMPLATE = {
    "method": "getList",
    "format": "json",
    "jsonVD": "Y",
    # "orgId": "101",
    # "tblId": "DT_1B8000F",   # 예시 — 실제 표 ID 확인 필요
}


@retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=2, min=2, max=16))
def _call(params: dict) -> list[dict]:
    with httpx.Client(timeout=15) as client:
        r = client.get(KOSIS_ENDPOINT, params=params)
        r.raise_for_status()
        return r.json()


def collect_births(regions: list[str] | None = None) -> list[BirthRecord]:
    """지정 지역의 월별 출생아 수를 수집한다."""
    s = get_settings()
    if not s.kosis_api_key:
        raise RuntimeError("KOSIS_API_KEY 가 없습니다. .env 를 설정하세요. (검증은 --dry-run)")

    region_cfg = get_demand()["regions"]
    targets = regions or list(region_cfg.keys())

    records: list[BirthRecord] = []
    for region in targets:
        params = dict(KOSIS_PARAMS_TEMPLATE)
        params["apiKey"] = s.kosis_api_key
        params["objL1"] = region_cfg[region]["kosis_code"]
        rows = _call(params)
        # TODO: KOSIS 응답 스키마(PRD_DE='YYYYMM', DT=값)에 맞춰 파싱
        for row in rows:
            prd = str(row.get("PRD_DE", ""))
            if len(prd) != 6:
                continue
            records.append(
                BirthRecord(
                    region=region,
                    year=int(prd[:4]),
                    month=int(prd[4:6]),
                    births=int(float(row.get("DT", 0))),
                    source="kosis",
                )
            )
    return records
