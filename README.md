# 한일문화교류서비스 MVP

Python(FastAPI) + Claude API로 구현한 한일 문화교류 서비스 프로토타입입니다.
구글 폼/시트로 실제 수집 중인 설문 응답을 그대로 근거 데이터로 사용해, 사용자는
**채팅 화면 하나**에서 질문하고 답변·추천을 받으며, **관리자 화면**에서는 데이터
동기화 상태와 국적 자동판별 결과를 점검·보정합니다.

## 1. 실행 방법

```bash
cd kj-culture-exchange
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # .env 파일을 열어 ANTHROPIC_API_KEY 입력
python -m app.dev_import_sample    # (선택) 오프라인 테스트용 샘플 응답 10건 임포트
uvicorn app.main:app --reload      # http://localhost:8000 접속
```

`.env`에 `ANTHROPIC_API_KEY`를 넣지 않아도 서버는 정상 구동되고 데이터 동기화/관리
기능도 그대로 쓸 수 있지만, AI 채팅 답변만 안내 메시지로 대체됩니다. 키는
[console.anthropic.com](https://console.anthropic.com)에서 발급받을 수 있습니다.

### 자주 겪는 오류: Windows에서 `pip install -r requirements.txt` 실패 / `uvicorn` 명령을 찾을 수 없음

Windows PowerShell에서 `pip install -r requirements.txt` 도중 `Failed to build wheel`류
오류가 나면서 중간에 설치가 멈추면, 그 뒤에 나열된 패키지(uvicorn 포함)는 하나도 설치되지
않습니다. 그래서 `uvicorn app.main:app --reload`를 실행하면 `'uvicorn' 용어가 cmdlet,
함수... 인식되지 않습니다` 오류가 뜹니다. 해결 방법:

```powershell
pip install -r requirements.txt
```

위 명령의 **출력을 위로 스크롤해서** 정확히 어떤 패키지에서 실패했는지 확인하세요.
그 패키지 이름을 알려주시면 원인을 봐드릴게요. 우선 아래를 시도해보세요.

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

## 2. 구글 시트 연동 (실제 데이터 연결하기)

이 앱은 구글 폼 응답이 쌓이는 구글 시트를 **"웹에 게시(CSV)"** 링크로 읽어옵니다.
별도 API 키나 인증 없이 동작하는 대신, 시트가 링크를 아는 사람에게 공개됩니다.

1. 응답이 쌓이는 구글 시트를 엽니다. (구글 폼 상단 "응답" 탭 → 스프레드시트 아이콘)
2. **파일 → 공유 → 웹에 게시** → 시트 선택 → 형식은 **쉼표로 구분된 값(.csv)** →
   **게시** 클릭 → `https://docs.google.com/spreadsheets/d/e/.../pub?output=csv`
   형태의 링크가 생성됩니다.
3. 서버를 실행한 뒤 `/admin` 페이지에 접속해 이 URL을 붙여넣고 저장 → **"지금 동기화"**
   버튼을 누르면 응답이 즉시 반영됩니다.
4. 이후에는 `/admin`에서 필요할 때마다 "지금 동기화"를 눌러 최신 응답을 반영하면 됩니다.
   (완전 자동 실시간 반영이 필요하면 `app/services/sheet_sync.sync_now()`를 주기적으로
   호출하는 스케줄러를 추가하면 됩니다.)

## 3. 국적(한국/일본) 자동 판별

이 설문은 국적을 직접 묻지 않고 "한국인은 한국어로, 일본인은 일본어로 답변한다"는
전제로 운영되고 있습니다. 그래서 앱은 각 응답의 답변 텍스트에 포함된 **한글/가나 문자
비율**로 국적을 자동 판별합니다 (`app/services/lang_detect.py`). 100% 정확할 수는
없어서(예: 답변이 전부 영어 고유명사인 경우 등), `/admin` 페이지의 **"국적 판별이
필요한 응답"** 목록에서 신뢰도가 낮거나 미판별된 응답을 수동으로 KR/JP로 바로잡거나,
품질이 낮은 응답을 통계에서 제외 처리할 수 있습니다.

## 4. 관리자 로그인

`/admin`과 `/api/admin/*`, `/api/ai/logs`는 비밀번호 인증이 필요합니다. `.env`에
`ADMIN_PASSWORD`(로그인 비밀번호)와 `ADMIN_SESSION_SECRET`(세션 쿠키 서명 키,
임의의 긴 무작위 문자열)를 설정하세요. 인증되지 않은 사용자에게는 상단
"관리자" 탭도 보이지 않습니다.

## 5. 화면 구성

| 경로 | 설명 |
|---|---|
| `/` | AI 채팅 — 사용자는 여기서만 질문/추천을 받습니다 |
| `/admin` | 관리자 전용 (비밀번호 로그인 필요) — 시트 연동 설정, 동기화, 응답 통계, 국적 보정 |

우측 상단의 버튼(日本語 / 한국어)을 누르면 화면 전체(채팅·관리자 페이지 모두)가
한국어 ↔ 일본어로 즉시 전환됩니다. 선택한 언어는 브라우저에 저장되어 다음 방문에도
유지되며, 채팅에서는 AI 답변도 선택된 언어로 생성됩니다. 번역 문구는
`app/static/i18n.js`에서 관리합니다.

## 6. 기능별 구현 요약

**AI 채팅 (질문 + 추천 통합)** — `app/routers/ai.py`, `app/services/rag.py`
사용자가 채팅창에 무엇이든 물어보면, 국적(KR/JP)별로 정리된 설문 원문 응답 전체를
컨텍스트로 구성해 Claude API에 전달합니다. 문항이 전부 주관식(영화/음악/음식/여행지/
애니메이션 등)이라 고정 태그 체계 대신 원문 텍스트를 그대로 근거로 사용하고, Claude가
직접 빈도·패턴을 읽어 답변과 추천, 그 이유를 함께 설명합니다. 데이터 규모가 작은
동안은 별도 벡터 검색 없이 전체 컨텍스트를 주입하는 것으로 충분하며, 규모가 커지면
`build_response_context()`를 임베딩 기반 검색으로 교체하는 것을 권장합니다.

채팅 화면에는 영화/음악/취미/음식/여행/애니메이션 카테고리 버튼이 있습니다(`GET /api/ai/categories`).
카테고리를 선택하면 그 주제의 문항만 Claude에게 전달되고, 관련 없는 질문은 답변을 거부하도록
시스템 프롬프트에 강제합니다(`app/services/rag.py`의 `CATEGORIES`, `CATEGORY_SYSTEM_EXTRA`).
문항-카테고리 매칭은 시트 헤더 문구가 조금씩 달라져도(예: 한국어/일본어 병기) 깨지지 않도록
정확히 일치가 아닌 키워드 포함 여부로 판단합니다. '음악' 카테고리에서는 설문에 언급된 곡뿐 아니라
같은 아티스트의 다른 곡도 Claude가 일반 지식으로 추가 추천하며, "(AI 추가 추천)"으로 구분 표시합니다.

**데이터 동기화 및 관리** — `app/routers/admin.py`, `app/services/sheet_sync.py`
구글 시트 CSV 링크 등록/동기화, 국적 자동판별 신뢰도 관리, 응답 통계(국적별/문항별
응답 건수), 데이터 품질이 낮은 응답 제외 처리를 제공하는 운영자 대시보드입니다.

**국적 자동 판별** — `app/services/lang_detect.py`
응답 텍스트의 한글/가나/한자 문자 수를 세어 KR/JP를 추정하고, 확신도가 낮은 응답은
관리자 화면에서 수동 보정하도록 플래그합니다.

## 7. 프로젝트 구조

```
app/
  main.py                  # FastAPI 앱, 페이지 라우트 (/ = 채팅, /admin = 관리자)
  database.py              # SQLite + SQLAlchemy 세션
  models.py                # DB 모델 (SurveyResponse, AppSetting, AIQuery)
  schemas.py                # Pydantic 요청/응답 스키마
  dev_import_sample.py      # 오프라인 테스트용: sample_data/mock_responses.csv 임포트
  routers/
    admin.py                # 시트 동기화 설정 + 데이터 관리
    ai.py                    # AI 채팅 (질문/답변/추천 통합)
  services/
    lang_detect.py           # 한글/가나 비율로 국적 자동 판별
    sheet_sync.py             # 구글 시트 CSV 동기화 (fetch → parse → upsert)
    rag.py                    # 설문 원문 컨텍스트 구성 + Claude 호출
  templates/                # Jinja2 + fetch 기반 프론트엔드 (프레임워크 없이 순수 HTML/JS)
  static/                   # CSS/JS
sample_data/
  mock_responses.csv         # 오프라인 테스트/데모용 샘플 응답 10건 (한국어 6 + 일본어 4)
```

## 8. 알아두면 좋은 점 (MVP 한계)

- 국적 자동 판별은 텍스트의 한글/가나 비율에 기반한 휴리스틱입니다. 답변이 전부
  영어 고유명사(아티스트명 등)인 경우 등은 "미판별"로 남을 수 있으며, `/admin`에서
  수동으로 바로잡을 수 있습니다.
- 시트 동기화는 "웹에 게시" 방식이라 별도 인증이 필요 없는 대신, 해당 시트가
  링크를 아는 사람 누구나 볼 수 있게 공개됩니다. 응답에 민감한 개인정보가
  없는지 확인 후 사용하세요.
- 완전 자동 실시간 동기화가 필요하면 `/admin`의 수동 "지금 동기화" 버튼 대신
  APScheduler 등으로 주기 실행을 추가하는 것을 권장합니다.
- DB는 SQLite 파일(`kj_exchange.db`)이며, 실 서비스 전환 시 PostgreSQL 등으로
  교체를 권장합니다.
- 대량의 응답이 쌓이면 `app/services/rag.py`의 전체 컨텍스트 주입 방식 대신
  임베딩 기반 검색으로 교체하는 것을 권장합니다 (현재는 국적별 최대 150건까지만
  사용, 초과분은 응답에 "표본 사용" 안내가 붙습니다).
