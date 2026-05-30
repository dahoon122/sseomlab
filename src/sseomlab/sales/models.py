"""영업 자료(SalesKit) 모델 — 공간 1곳당 실제 영업에 쓰는 12개 필드."""

from __future__ import annotations

from pydantic import BaseModel


class SalesKit(BaseModel):
    space_name: str
    region: str
    grade: str
    contact_priority: int

    one_line_eval: str           # 1. 공간 한줄 평가
    why_fit: str                 # 2. 왜 웨딩/돌잔치에 적합한지
    owner_benefit: str           # 3. 사장님에게 제안할 핵심 이익
    weekday_idle_offer: str      # 4. 평일 유휴시간 활용 제안
    sample_shoot_offer: str      # 5. 샘플 촬영 제안 문구
    dm_message: str              # 6. DM 첫 연락 문구
    phone_script: str            # 7. 전화 스크립트
    proposal_title: str          # 8. 제안서 제목
    product_name: str            # 9. 추천 상품명
    expected_products: list[str] # 10. 예상 판매 상품
    expected_avg_price_krw: int  # 11. 예상 객단가
    contact_timing: str          # 12. 우선 연락 시점
