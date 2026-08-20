"""기능③④ 통합: AI 채팅 (자연어 질문 -> 답변 + 추천)"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AIQuery
from app.schemas import ChatIn
from app.services.admin_auth import is_admin_request, require_admin_api
from app.services.rag import build_response_context, call_claude, load_categories_list
from app.services import sheet_sync

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.get("/categories")
def categories(db: Session = Depends(get_db)):
    return [
        {
            "key": c["key"], "ko": c["ko"], "ja": c["ja"],
            "examples_ko": c.get("examples_ko", []), "examples_ja": c.get("examples_ja", []),
        }
        for c in load_categories_list(db)
    ]


@router.get("/survey-url")
def survey_url(db: Session = Depends(get_db)):
    """설문 참여 링크 (구글 폼 URL). 관리자가 설정한 경우에만 값이 채워짐 - 공개 정보."""
    return {"survey_form_url": sheet_sync.get_setting(db, sheet_sync.SURVEY_FORM_URL_KEY)}


@router.post("/chat")
def chat(payload: ChatIn, request: Request, db: Session = Depends(get_db)):
    if not sheet_sync.is_chat_published(db) and not is_admin_request(request):
        raise HTTPException(403, "아직 채팅이 게시되지 않았습니다. 관리자가 게시할 때까지 기다려주세요.")

    context = build_response_context(db, category=payload.category)
    answer = call_claude(payload.question, context, lang=payload.lang or "ko")

    log = AIQuery(
        question=payload.question,
        answer=answer,
        used_context={"counts": context["counts"], "category": context["category"]},
    )
    db.add(log)
    db.commit()

    return {"answer": answer, "query_id": log.id}


@router.get("/logs", dependencies=[Depends(require_admin_api)])
def recent_logs(limit: int = 20, db: Session = Depends(get_db)):
    logs = db.query(AIQuery).order_by(AIQuery.id.desc()).limit(limit).all()
    return [
        {
            "id": l.id, "question": l.question, "answer": l.answer,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        }
        for l in logs
    ]
