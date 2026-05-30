# 내 PC에서 실제 데이터로 실행하기 (네이버 키만 필요)

클라우드(Claude Code 웹) 환경은 보안상 네이버 접속이 막혀 있어, **실제 공간 수집은 본인 PC에서** 합니다.
PC는 인터넷 제한이 없어 네이버 API가 바로 동작합니다. **Claude 키는 필요 없습니다**(규칙기반 점수 사용).

---

## 0. 준비물
- **Python 3.11 이상** (https://www.python.org/downloads → 설치 시 "Add to PATH" 체크)
- **Git** (https://git-scm.com)
- 네이버 개발자센터 키: `Client ID`, `Client Secret`

## 1. 코드 내려받기 (터미널/PowerShell에서)
> 맥: `터미널`, 윈도우: `PowerShell` 실행 후 한 줄씩 붙여넣기

```bash
git clone https://github.com/dahoon122/sseomlab.git
cd sseomlab
git checkout claude/venue-sourcing-wedding-dolsang-Lecqz
```

## 2. 네이버 키 입력 (.env 파일 만들기)
프로젝트 폴더(`sseomlab`) 안에 `.env` 파일을 만들고 아래를 넣습니다. (키는 본인 값으로)

```
NAVER_CLIENT_ID=여기에_본인_ID
NAVER_CLIENT_SECRET=여기에_본인_시크릿
```

> 맥/리눅스 한 번에:
> ```bash
> printf 'NAVER_CLIENT_ID=본인ID\nNAVER_CLIENT_SECRET=본인시크릿\n' > .env
> ```
> `.env`는 깃에 올라가지 않습니다(안전).

## 3. 설치
```bash
python -m venv .venv
# 맥/리눅스:
source .venv/bin/activate
# 윈도우(PowerShell):
.venv\Scripts\Activate.ps1

pip install -e .
```

## 4. 실제 공간 수집·분석 실행 ⭐
처음엔 **한 지역만** 작게 시작하길 권장합니다(쿼리 수가 많아 2~3분 소요).

```bash
# 대구 정원카페만 빠르게 테스트
python -m sseomlab run --source naver --region 대구 --space-type 정원카페

# 대구 전체 유형
python -m sseomlab run --source naver --region 대구

# 5개 지역 전체 (10분 이상 소요)
python -m sseomlab run --source naver
```

끝나면 결과가 `data/output/` 에 생성됩니다:
- `sseomlab_result.csv` — 실제 공간 점수표
- `space_db_A등급.csv` — A등급 공간 DB
- `sseomlab_proposals.csv` — 제안서 12필드
- `영업키트.csv` — 공간별 DM·전화스크립트·객단가·연락시점

엑셀로 보려면 같은 폴더의 `.xlsx` 파일을 열면 됩니다.

## 5. 수요·공급 예측 (선택)
출생아 수(KOSIS)는 아직 합성 데이터입니다. 그대로도 공급부족/광고타이밍 로직은 확인됩니다.
```bash
python -m sseomlab forecast --dry-run
```

---

## 자주 묻는 문제
| 증상 | 해결 |
|------|------|
| `python` 없다고 나옴 | `python3` 로 시도 (맥/리눅스) |
| `NAVER_CLIENT_ID 가 없습니다` | `.env` 파일 위치(프로젝트 폴더 안)·철자 확인 |
| `401 Unauthorized` | 네이버 키(ID/Secret) 오타, 또는 앱에 '검색' API 추가 안 됨 |
| 결과가 너무 적음 | 네이버 지역검색은 쿼리당 최대 5건 — 여러 지역/유형으로 폭을 넓히세요 |
| 점수가 거칠다 | 1차는 키워드 기반. 사진/블로그 보강(Phase 2~4)·Claude 점수(`--scoring llm`)로 정밀화 |

## 한 단계 더 (정밀 점수, 선택)
Claude(Anthropic) 키가 있으면 사진/문맥 기반 정밀 판정도 가능합니다.
`.env`에 `ANTHROPIC_API_KEY=...` 추가 후:
```bash
python -m sseomlab run --source naver --region 대구 --scoring llm
```
