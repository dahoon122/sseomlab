# TODO — 막히거나 키가 필요해 보류한 작업

> 규칙: 키/외부의존으로 막히면 멈추지 말고 여기 기록 후 다음 작업으로 넘어간다.
> ✅ 완료 / 🔜 다음 / ⛔ 보류(사유)

## ⛔ 외부 API 키 필요 (목업으로 대체 구현됨)
- ⛔ **KOSIS 실연동** — `KOSIS_API_KEY` 필요. 현재 합성 출생데이터로 동작.
  - 보강: 인구동향조사 출생 통계표 `orgId/tblId/itmId/objL` 확정 필요 (`demand/kosis.py` TODO)
- ⛔ **네이버 지역검색 실연동** — `NAVER_CLIENT_ID/SECRET` 필요. 현재 샘플 CSV로 동작.
- ⛔ **Claude 점수/사진 분석** — `ANTHROPIC_API_KEY` 필요. 현재 규칙기반(heuristic) 점수로 동작.
- ⛔ **구글시트 출력** — 서비스계정 필요. 현재 CSV/엑셀로 출력. (`export/gsheet.py`)

## ⛔ 추가 데이터 소스 (설계만, 연동 대기)
- ⛔ 혼인 건수(KOSIS) — 수요 보정 변수. `demand/marriage.py` 미생성.
- ⛔ 인구/지역 성장추세 — 투영 정교화용. 현재 단순 YoY 계수.
- ⛔ 제이드 내부데이터(상담/계약/객단가/광고비/채널) — `data/jade_actuals.csv` 스키마로 시작, 채널/객단가 확장 필요.

## 🔜 다음 개발 (키 없이 가능)
- 🔜 컨셉 분류를 사진 기반 Claude 분류로 정밀화 (현재 공간유형 매핑)
- 🔜 공급부족 '추천 액션'(정원N·독채N) ↔ 발굴된 A/B등급 후보 자동 매칭(어느 공간을 확보할지까지)
- 🔜 지역×월 히트맵(성수기 기회) 시각화
- 🔜 수수밀소 등 기준 사례를 '레퍼런스 공간'으로 별도 관리
- 🔜 영업키트 결과를 제이드 실제 컨택 성사율로 피드백 학습(객단가·연락시점 보정)
- 🔜 협업점수 가중치를 실제 협업 성사 데이터로 calibration

## 보정 필요 (가정값 → 실데이터)
- supply: hall_base_capacity / hidden_secured_capacity / per_space_monthly_capacity / seasonality_factor
- sales: 카테고리별 avg_price_krw(객단가) / 상품 구성
- collaboration 가중치, demand 전환율(event_rate·serviceable·capture)

## 알려진 한계
- 전환율/수용량/시즌계수는 초기 가정값 — 제이드 실데이터로 calibration 필요.
- 공간 수용량 데이터가 지역 합계 수준 — 공간 단위로 세분화하면 정확.
