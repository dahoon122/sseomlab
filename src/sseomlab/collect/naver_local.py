"""네이버 지역 검색 API 기반 1차 수집기.

지역(sub_area) × 공간유형(search_keyword) 조합으로 검색어를 만들어 장소를 모은다.

주의(법적/운영):
- 네이버 '지역 검색 API'(공식)를 사용한다. https://developers.naver.com
- 네이버 플레이스 페이지 직접 스크래핑은 robots/ToS 위반 소지가 있으므로
  공식 API 우선, 부족한 필드는 사람이 수동 보강하거나 별도 합의된 경로로 처리.
- request_delay_seconds 로 호출 간격을 두어 차단/과부하를 피한다.
"""

from __future__ import annotations

import re
import time

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from sseomlab.config import get_regions, get_settings, get_space_types
from sseomlab.models import Place

NAVER_LOCAL_ENDPOINT = "https://openapi.naver.com/v1/search/local.json"
_TAG = re.compile(r"<[^>]+>")


def _clean(s: str) -> str:
    return _TAG.sub("", s or "").strip()


@retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=2, min=2, max=16))
def _call(query: str, display: int = 5) -> list[dict]:
    s = get_settings()
    headers = {
        "X-Naver-Client-Id": s.naver_client_id,
        "X-Naver-Client-Secret": s.naver_client_secret,
    }
    params = {"query": query, "display": display, "sort": "comment"}
    with httpx.Client(timeout=10) as client:
        r = client.get(NAVER_LOCAL_ENDPOINT, headers=headers, params=params)
        r.raise_for_status()
        return r.json().get("items", [])


def collect(regions: list[str] | None = None, space_types: list[str] | None = None) -> list[Place]:
    """지정 지역/공간유형 조합으로 장소를 수집한다."""
    s = get_settings()
    if not s.naver_client_id:
        raise RuntimeError("NAVER_CLIENT_ID/SECRET 가 없습니다. .env 를 설정하세요.")

    region_cfg = get_regions()
    type_cfg = {t["type"]: t for t in get_space_types()["space_types"]}

    target_regions = regions or list(region_cfg.keys())
    target_types = space_types or list(type_cfg.keys())

    seen: set[str] = set()
    results: list[Place] = []

    for region in target_regions:
        for sub in region_cfg[region]["sub_areas"]:
            for st in target_types:
                for kw in type_cfg[st]["search_keywords"]:
                    query = f"{sub} {kw}"
                    for item in _call(query):
                        name = _clean(item.get("title", ""))
                        key = f"{name}|{_clean(item.get('address',''))}"
                        if not name or key in seen:
                            continue
                        seen.add(key)
                        results.append(
                            Place(
                                source="naver_local",
                                name=name,
                                category=item.get("category"),
                                region=region,
                                sub_area=sub,
                                address=_clean(item.get("address", "")),
                                road_address=_clean(item.get("roadAddress", "")),
                                phone=item.get("telephone") or None,
                                homepage=item.get("link") or None,
                                naver_place_url=item.get("link") or None,
                                search_keyword=kw,
                                raw_text=f"{name} {item.get('category','')} {_clean(item.get('description',''))}",
                            )
                        )
                    time.sleep(s.request_delay_seconds)
    return results
