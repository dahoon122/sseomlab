# 아키텍처

## 데이터 흐름

```
                 config/*.yaml (지역·공간유형·점수가중치)   .env (키·옵션)
                              │                                │
                              ▼                                ▼
 [1 수집]  naver_local.collect ───────────────────────────► list[Place]
                              │
 [필터]    analyze.exclusion.screen  (hard 키워드 즉시 제외)
                              │  (통과분만)
 [2 보강]  collect.enrich.enrich  (블로그/홈피/사진/인스타노출)
                              │
 [3·4·5]   score.scorer.score_place
              ├─ 1차: screening_model(haiku), 텍스트만 → 조기 탈락
              └─ 2차: main_model(opus), 사진 포함 → 정밀 판정
                              │  → PlaceAnalysis + PlaceScore
 [6 우선]   pipeline._assign_priority (종합점수 내림차순 → 우선순위 1..N)
                              │
 [출력]    export.excel / export.gsheet ──────────────────► .xlsx / Google Sheet
```

## 모델 (`models.py`)
정보가 단계별로 누적되는 단방향 파이프라인:

- **Place** — 수집 원천 데이터(상호·주소·카테고리·리뷰수·사진URL·raw_text)
- **PlaceAnalysis** — 제외 판정 + 사진/텍스트에서 뽑은 정성 신호(정원·통창·룸·주차 등)
- **PlaceScore** — 4대 점수 + 종합점수 + 등급 + 추천 제안
- **PlaceRecord** — 위 셋 + 연락 우선순위. 엑셀 한 행에 대응.

## 점수 결합 전략
최종 점수 = **Claude 정성 판단** + **규칙기반 정량 신호**(`config/scoring.yaml` 가중).

- Claude: "이 사진/설명이 웨딩에 어울리나?" 같은 정성 판단에 강함
- 규칙: 리뷰 50~500 스윗스팟, 외곽 여부, 체인 여부 등 명시적 신호는 코드로 안정적으로 계산
- 두 축을 결합해 모델 편차를 줄이고 정책 조정(가중치)을 코드 수정 없이 가능하게 함

종합점수(연락 우선순위용) 기본 가중:
`0.30·웨딩전환 + 0.20·돌상전환 + 0.20·숨은공간 + 0.30·협업가능성`
→ "전환 적합 + 실제 성사 가능성"을 동시에 본다. (`scorer._composite`)

## 비용 전략 (대량 처리 핵심)
1. **규칙 필터 우선** — 명백한 웨딩홀은 Claude 호출 전에 키워드로 제거
2. **2단계 스크리닝** — haiku로 대량 1차, opus는 유망 후보만
3. **사진은 상위 후보만** — Vision 토큰이 비싸므로 점수 상위에만 정밀 적용
4. **증분 실행** — 이미 평가한 곳은 캐시로 skip (Phase 6)

## 설정 분리 원칙
- 정책(어디서·무엇을·어떻게 점수)은 전부 `config/*.yaml` — 비개발자도 조정
- 비밀키·런타임 옵션은 `.env` — 절대 커밋 금지
- 코드는 정책을 '실행'만 한다

## 확장 포인트
- 새 수집원: `collect/` 에 `collect()->list[Place]` 모듈 추가 후 pipeline 에 연결
- 새 공간유형/지역: `config/*.yaml` 만 수정
- 새 출력형식: `export/` 에 `export(records, out)` 모듈 추가
