"""한일문화교류서비스 MVP - FastAPI 진입점

메인 화면은 AI 채팅 하나로 통합되어 있고(질문+추천), /admin 은 별도 URL로 분리된
관리자 전용 화면입니다 (인증은 걸려있지 않음 - 필요 시 추가 가능).
"""
import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import Base, engine
from app.routers import admin, ai

Base.metadata.create_all(bind=engine)

APP_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="한일문화교류서비스 MVP")

app.mount("/static", StaticFiles(directory=os.path.join(APP_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(APP_DIR, "templates"))

app.include_router(admin.router)
app.include_router(ai.router)


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(request, "chat.html", {})


@app.get("/admin")
def admin_page(request: Request):
    return templates.TemplateResponse(request, "admin.html", {})
