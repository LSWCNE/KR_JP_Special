"""한일문화교류서비스 MVP - FastAPI 진입점

메인 화면은 AI 채팅 하나로 통합되어 있고(질문+추천), /admin 은 비밀번호 로그인이
필요한 관리자 전용 화면입니다. 인증되지 않은 사용자에게는 네비게이션의 "관리자"
탭도 노출되지 않습니다.
"""
import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.routers import admin, ai
from app.services import admin_auth, sheet_sync

Base.metadata.create_all(bind=engine)

APP_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="한일문화교류서비스 MVP")

app.mount("/static", StaticFiles(directory=os.path.join(APP_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(APP_DIR, "templates"))

app.include_router(admin.router)
app.include_router(ai.router)


@app.get("/")
def home(request: Request, db: Session = Depends(get_db)):
    is_admin = admin_auth.is_admin_request(request)
    return templates.TemplateResponse(request, "chat.html", {
        "is_admin": is_admin,
        "chat_published": sheet_sync.is_chat_published(db),
    })


@app.get("/admin")
def admin_page(request: Request):
    if not admin_auth.is_admin_request(request):
        return RedirectResponse("/admin/login")
    return templates.TemplateResponse(request, "admin.html", {"is_admin": True})


@app.get("/admin/login")
def admin_login_page(request: Request):
    if admin_auth.is_admin_request(request):
        return RedirectResponse("/admin")
    return templates.TemplateResponse(request, "admin_login.html", {"is_admin": False})


@app.post("/admin/login")
def admin_login_submit(request: Request, password: str = Form(...)):
    if not admin_auth.check_password(password):
        return templates.TemplateResponse(
            request, "admin_login.html", {"is_admin": False, "error": "비밀번호가 올바르지 않습니다."}, status_code=401
        )
    response = RedirectResponse("/admin", status_code=303)
    response.set_cookie(
        admin_auth.COOKIE_NAME,
        admin_auth.create_session_token(),
        max_age=admin_auth.SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
    )
    return response


@app.post("/admin/logout")
def admin_logout():
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie(admin_auth.COOKIE_NAME)
    return response
