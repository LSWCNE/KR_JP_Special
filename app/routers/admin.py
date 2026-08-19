"""기능②: 데이터 관리 (구글 시트 동기화 설정 + 응답 품질/국적 보정 대시보드)"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SurveyResponse
from app.schemas import SettingsIn, ResponseOverrideIn
from app.services import sheet_sync
from app.services.admin_auth import require_admin_api

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin_api)])


@router.get("/settings")
def get_settings(db: Session = Depends(get_db)):
    return {
        "csv_url": sheet_sync.get_setting(db, sheet_sync.CSV_URL_KEY),
        "last_synced_at": sheet_sync.get_setting(db, sheet_sync.LAST_SYNCED_AT_KEY),
    }


@router.post("/settings")
def update_settings(payload: SettingsIn, db: Session = Depends(get_db)):
    url = payload.csv_url.strip()
    sheet_sync.set_setting(db, sheet_sync.CSV_URL_KEY, url)
    result = {"ok": True}
    if not sheet_sync.looks_like_published_csv_url(url):
        result["warning"] = sheet_sync.PUBLISH_HELP_MESSAGE
    return result


@router.post("/sync")
def trigger_sync(db: Session = Depends(get_db)):
    result = sheet_sync.sync_now(db)
    if not result.get("ok"):
        raise HTTPException(400, result.get("error", "동기화 실패"))
    return result


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total = db.query(SurveyResponse).count()
    excluded = db.query(SurveyResponse).filter(SurveyResponse.excluded == True).count()  # noqa: E712
    kr = db.query(SurveyResponse).filter(SurveyResponse.nationality == "KR").count()
    jp = db.query(SurveyResponse).filter(SurveyResponse.nationality == "JP").count()
    unknown = db.query(SurveyResponse).filter(SurveyResponse.nationality == "UNKNOWN").count()
    low_confidence = db.query(SurveyResponse).filter(
        SurveyResponse.nationality_confidence < 0.4,
        SurveyResponse.nationality_manual == False,  # noqa: E712
    ).count()

    # 문항별 응답 건수 (비어있지 않은 답변 개수)
    question_counts: dict[str, int] = {}
    for r in db.query(SurveyResponse).filter(SurveyResponse.excluded == False).all():  # noqa: E712
        for q, a in (r.raw_answers or {}).items():
            if a:
                question_counts[q] = question_counts.get(q, 0) + 1

    return {
        "total_responses": total,
        "excluded": excluded,
        "kr": kr,
        "jp": jp,
        "unknown": unknown,
        "low_confidence_needs_review": low_confidence,
        "question_counts": question_counts,
    }


@router.get("/responses")
def list_responses(db: Session = Depends(get_db), limit: int = 200, needs_review_only: bool = False):
    q = db.query(SurveyResponse)
    if needs_review_only:
        q = q.filter(
            (SurveyResponse.nationality == "UNKNOWN") |
            (SurveyResponse.nationality_confidence < 0.4)
        ).filter(SurveyResponse.nationality_manual == False)  # noqa: E712
    rows = q.order_by(SurveyResponse.id.desc()).limit(limit).all()

    result = []
    for r in rows:
        preview_items = list((r.raw_answers or {}).items())[:2]
        preview = " / ".join(f"{k}: {v}" for k, v in preview_items if v)
        result.append({
            "id": r.id,
            "nationality": r.nationality,
            "nationality_confidence": r.nationality_confidence,
            "nationality_manual": r.nationality_manual,
            "excluded": r.excluded,
            "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None,
            "preview": preview[:200],
        })
    return result


@router.get("/responses/{response_id}")
def get_response(response_id: int, db: Session = Depends(get_db)):
    r = db.query(SurveyResponse).get(response_id)
    if not r:
        raise HTTPException(404, "response not found")
    return {
        "id": r.id,
        "nationality": r.nationality,
        "nationality_confidence": r.nationality_confidence,
        "nationality_manual": r.nationality_manual,
        "excluded": r.excluded,
        "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None,
        "raw_answers": r.raw_answers,
    }


@router.patch("/responses/{response_id}")
def update_response(response_id: int, payload: ResponseOverrideIn, db: Session = Depends(get_db)):
    r = db.query(SurveyResponse).get(response_id)
    if not r:
        raise HTTPException(404, "response not found")
    if payload.nationality is not None:
        if payload.nationality not in ("KR", "JP", "UNKNOWN"):
            raise HTTPException(400, "nationality must be KR, JP, or UNKNOWN")
        r.nationality = payload.nationality
        r.nationality_manual = True
    if payload.excluded is not None:
        r.excluded = payload.excluded
    db.commit()
    return {"ok": True}
