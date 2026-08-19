"""구글 시트 '웹에 게시(CSV)' 동기화 서비스

구글 폼 응답이 쌓이는 구글 시트를 파일 > 공유 > 웹에 게시 > CSV 로 발행하면
`https://docs.google.com/spreadsheets/d/e/.../pub?output=csv` 형태의 URL이 생기고,
이 URL은 인증 없이 누구나 최신 CSV를 받아볼 수 있다. 이 모듈은 그 URL을 주기적으로
읽어와 SurveyResponse 테이블에 반영(upsert)한다.
"""
import csv
import hashlib
import io
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.models import AppSetting, SurveyResponse
from app.services.lang_detect import classify_response_row

CSV_URL_KEY = "csv_url"
LAST_SYNCED_AT_KEY = "last_synced_at"
LAST_SYNC_SUMMARY_KEY = "last_sync_summary"
SURVEY_FORM_URL_KEY = "survey_form_url"

TIMESTAMP_HEADER_CANDIDATES = {"타임스탬프", "timestamp", "タイムスタンプ"}


def get_setting(db: Session, key: str, default: str | None = None) -> str | None:
    row = db.query(AppSetting).get(key)
    return row.value if row else default


def set_setting(db: Session, key: str, value: str):
    row = db.query(AppSetting).get(key)
    if row:
        row.value = value
    else:
        row = AppSetting(key=key, value=value)
        db.add(row)
    db.commit()


def _row_hash(row: dict) -> str:
    payload = "|".join(f"{k}={v}" for k, v in sorted(row.items()))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def _parse_timestamp(value: str):
    if not value:
        return None
    value = value.strip()
    # 한국어/일본어 로케일의 오전·오후(午前·午後) 표기는 %p로 인식되지 않으므로 치환
    value = (
        value.replace("오전", "AM").replace("오후", "PM")
        .replace("午前", "AM").replace("午後", "PM")
    )
    # 구글 폼 기본 타임스탬프 형식: "2026. 8. 19 오후 3:20:11" 또는 "8/19/2026 15:20:11"
    formats = [
        "%Y. %m. %d %p %I:%M:%S",
        "%Y/%m/%d %I:%M:%S %p",
        "%m/%d/%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def looks_like_published_csv_url(url: str) -> bool:
    """일반 '/edit' 공유 링크가 아니라 '웹에 게시'로 만든 CSV 링크인지 대략 확인."""
    if not url:
        return False
    if "docs.google.com/spreadsheets" not in url:
        return True  # 구글시트가 아니면(다른 CSV 호스팅 등) 굳이 막지 않음
    if "/edit" in url:
        return False
    return "output=csv" in url


PUBLISH_HELP_MESSAGE = (
    "이 링크는 일반 '공유' 링크(브라우저로 열 때 로그인 필요)로 보입니다. "
    "구글 시트에서 파일 → 공유 → 웹에 게시(Publish to web) → 형식을 "
    "쉼표로 구분된 값(.csv)으로 선택 → 게시를 눌러 나오는, "
    "'.../pub?output=csv' 형태의 링크를 붙여넣어야 합니다. "
    "(README 2절 참고)"
)


def fetch_csv_text(url: str, timeout: float = 15.0) -> str:
    with httpx.Client(follow_redirects=True, timeout=timeout) as client:
        resp = client.get(url)
        resp.raise_for_status()
        # 구글이 BOM을 붙여 내려주는 경우 대비
        return resp.content.decode("utf-8-sig")


def parse_csv_rows(csv_text: str) -> list[dict]:
    reader = csv.DictReader(io.StringIO(csv_text))
    return [dict(row) for row in reader]


def sync_rows(db: Session, rows: list[dict]) -> dict:
    """파싱된 CSV 행들을 SurveyResponse로 upsert. 반환: 동기화 요약 통계."""
    new_count = 0
    skipped_count = 0
    updated_count = 0

    for row in rows:
        # 타임스탬프 컬럼과 그 외 문항 컬럼 분리
        timestamp_value = None
        answers = {}
        for header, value in row.items():
            if header is None:
                continue
            if header.strip() in TIMESTAMP_HEADER_CANDIDATES:
                timestamp_value = value
            else:
                answers[header.strip()] = (value or "").strip()

        if not any(answers.values()):
            continue  # 완전히 빈 행은 스킵

        row_key = timestamp_value.strip() if timestamp_value else _row_hash(answers)
        existing = db.query(SurveyResponse).filter(
            SurveyResponse.external_row_key == row_key
        ).first()
        if existing:
            skipped_count += 1
            continue

        nationality, confidence = classify_response_row(answers)
        submitted_at = _parse_timestamp(timestamp_value) if timestamp_value else None

        db.add(SurveyResponse(
            external_row_key=row_key,
            submitted_at=submitted_at,
            nationality=nationality,
            nationality_confidence=confidence,
            raw_answers=answers,
        ))
        new_count += 1

    db.commit()
    return {
        "total_rows_in_csv": len(rows),
        "new": new_count,
        "skipped_existing": skipped_count,
        "updated": updated_count,
    }


def sync_now(db: Session) -> dict:
    csv_url = get_setting(db, CSV_URL_KEY)
    if not csv_url:
        return {"ok": False, "error": "CSV URL이 설정되지 않았습니다. 관리자 페이지에서 먼저 설정해주세요."}

    if not looks_like_published_csv_url(csv_url):
        return {"ok": False, "error": PUBLISH_HELP_MESSAGE}

    try:
        csv_text = fetch_csv_text(csv_url)
        rows = parse_csv_rows(csv_text)
        summary = sync_rows(db, rows)
    except httpx.HTTPStatusError as e:
        if e.response is not None and e.response.status_code in (401, 403):
            return {"ok": False, "error": PUBLISH_HELP_MESSAGE}
        return {"ok": False, "error": f"CSV를 가져오는 중 오류가 발생했습니다: {e}"}
    except httpx.HTTPError as e:
        return {"ok": False, "error": f"CSV를 가져오는 중 오류가 발생했습니다: {e}"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"동기화 중 오류가 발생했습니다: {e}"}

    now = datetime.now(timezone.utc).isoformat()
    set_setting(db, LAST_SYNCED_AT_KEY, now)
    result = {"ok": True, "synced_at": now, **summary}
    set_setting(db, LAST_SYNC_SUMMARY_KEY, str(result))
    return result
