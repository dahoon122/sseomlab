# sseomlab — 웨딩/돌상 전환 가능 '숨은 공간' 발굴 시스템

전국(**대구·경북·부산·경남·강원**)의 카페·식당·복합문화공간 중
**웨딩 전문 공간이 아니면서**, 웨딩 또는 돌잔치 공간으로 **전환 가능성이 높은
숨은 장소**를 자동으로 발굴·점수화하고 **연락 우선순위**를 만들어 엑셀/구글시트로 출력한다.

> 우리는 웨딩홀을 찾지 않는다. "카페·식당으로 운영 중이지만 웨딩/돌상으로 바꿀 수 있는 공간"을 찾는다.

---

## 무엇을 하나 (6대 기능)

| # | 기능 | 모듈 |
|---|------|------|
| 1 | 지역별 공간 자동 수집 | `collect/naver_local.py` |
| 2 | 웹사이트/네이버/인스타 정보 분석 | `collect/enrich.py`, `score/scorer.py` |
| 3 | 공간 사진 분석 (야외요소·분위기·수용력) | `analyze/photo` + Claude Vision |
| 4 | 웨딩/돌상 전환 가능성 점수화 | `score/scorer.py`, `score/prompts.py` |
| 5 | 협업 가능성 점수화 | `score/scorer.py` |
| 6 | 연락 우선순위 자동 생성 + 엑셀/시트 출력 | `pipeline.py`, `export/excel.py` |

## 빠른 시작

```bash
# 1) 설치
python -m venv .venv && source .venv/bin/activate
pip install -e .

# 2) 외부 API 없이 배선부터 검증 (가짜 데이터로 엑셀 생성)
python -m sseomlab run --dry-run --out data/output/demo.xlsx

# 3) 실제 실행 (.env 에 NAVER / ANTHROPIC 키 필요)
cp .env.example .env   # 키 입력
python -m sseomlab run --region 대구 --region 경북 --out data/output/대구경북.xlsx
```

## 동작 흐름

```
수집(네이버 지역검색) → 1차 제외필터(키워드) → 정보보강(블로그/홈피/사진)
   → Claude 판정·점수(텍스트 1차 → 유망후보만 사진 정밀) → 우선순위 → 엑셀/시트
```

비용 절감을 위해 **2단계 스크리닝**을 쓴다: 대량 후보는 저렴한 모델로 1차 걸러내고,
유망 후보만 상위 모델 + 사진으로 정밀 판정한다.

## 출력 점수 스키마 (장소 1건)

```json
{
  "exclude": false,
  "exclude_reason": "",
  "space_type": "숲속카페",
  "hidden_space_score": 70,
  "wedding_conversion_score": 78,
  "dolsang_conversion_score": 66,
  "collaboration_probability": 72,
  "grade": "A",
  "recommended_offer": "평일 오후 유휴시간 웨딩/돌상 대관 제휴 제안"
}
```

## 프로젝트 구조

```
config/            지역·공간유형·점수가중치 (코드 수정 없이 정책 조정)
src/sseomlab/
  collect/         1. 수집 + 2. 정보보강
  analyze/         규칙기반 제외필터 + 사진분석
  score/           Claude 프롬프트 + 점수화
  export/          엑셀 / 구글시트 출력
  pipeline.py      전 단계 오케스트레이션 (dry-run 지원)
  cli.py           명령행 진입점
docs/              로드맵 · 아키텍처 · 데이터출처/법적주의
tests/             제외필터 · dry-run 파이프라인 테스트
```

## 문서
- [개발 로드맵](docs/ROADMAP.md) — 단계별 마일스톤
- [아키텍처](docs/ARCHITECTURE.md) — 데이터 흐름 / 모델 / 비용 전략
- [데이터 출처와 법적 주의](docs/DATA_SOURCES.md) — API/스크래핑 ToS 준수 원칙

## 주의
네이버/인스타그램 등 외부 데이터는 **공식 API 우선**, ToS·robots·rate limit 을 준수한다.
자세한 내용은 [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) 참고.
