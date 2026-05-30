"""구글시트 출력 (스텁).

내부 대시보드 대안으로, 산출물을 구글시트에 업서트한다.
서비스 계정(GOOGLE_SERVICE_ACCOUNT_JSON) + 시트ID(GOOGLE_SHEET_ID) 필요.
gspread 로 구현하며, 키 없으면 명확히 안내한다.
"""

from __future__ import annotations

from typing import Sequence

from sseomlab.config import get_settings


def push_rows(worksheet_name: str, header: Sequence[str], rows: Sequence[Sequence]) -> None:
    """지정 워크시트를 header+rows 로 덮어쓴다. (TODO: 구현)"""
    s = get_settings()
    if not (s.google_service_account_json and s.google_sheet_id):
        raise RuntimeError(
            "GOOGLE_SERVICE_ACCOUNT_JSON / GOOGLE_SHEET_ID 가 없습니다. "
            "엑셀 출력을 사용하거나 .env 를 설정하세요."
        )
    # TODO: gspread 인증 → 시트 열기 → worksheet 업서트 → values 일괄 업데이트
    raise NotImplementedError("구글시트 출력은 Phase 5 에서 구현 예정 (export/excel 사용 가능).")
