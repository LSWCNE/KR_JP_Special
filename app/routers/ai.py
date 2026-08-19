"""기능③④ 통합: AI 채팅 (자연어 질문 -> 답변 + 추천)"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AIQuery
from app.schemas import ChatIn
from app.services.rag import CATEGORIES, build_response_context, call_claude

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.get("/categories")
def categories():
    return [
        {"key": key, "ko": info["ko"], "ja": info["ja"]}
        for key, info in CATEGORIES.items()
    ]


@router.post("/chat")
def chat(payload: ChatIn, db: Session = Depends(get_db)):
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


@router.get("/logs")
def recent_logs(limit: int = 20, db: Session = Depends(get_db)):
    logs = db.query(AIQuery).order_by(AIQuery.id.desc()).limit(limit).all()
    return [
        {
            "id": l.id, "question": l.question, "answer": l.answer,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        }
        for l in logs
    ]
