"""SQLAlchemy 모델 정의 (v2 - 구글 폼/시트 자유응답 기반)

- AppSetting: CSV 발행 URL 등 설정 값 (key-value)
- SurveyResponse: 구글 폼 응답 1건 = 1행. 13개 주관식 문항의 원문 답변을 raw_answers(JSON)에 저장
- AIQuery: AI 채팅 질의응답 로그
"""
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, DateTime, JSON
)

from app.database import Base


def now_utc():
    return datetime.now(timezone.utc)


class AppSetting(Base):
    __tablename__ = "app_settings"

    key = Column(String(50), primary_key=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=now_utc, onupdate=now_utc)


class SurveyResponse(Base):
    __tablename__ = "survey_responses"

    id = Column(Integer, primary_key=True, index=True)
    # 구글시트 원본 행을 식별하기 위한 키 (Timestamp 컬럼 값, 없으면 전체 내용 해시)
    external_row_key = Column(String(64), unique=True, index=True, nullable=False)
    submitted_at = Column(DateTime, nullable=True)  # 시트의 Timestamp 컬럼 (파싱 가능한 경우)

    # 자동 판별된 국적: "KR" | "JP" | "UNKNOWN"
    nationality = Column(String(10), nullable=False, default="UNKNOWN")
    nationality_confidence = Column(Float, default=0.0)
    nationality_manual = Column(Boolean, default=False)  # 관리자가 수동으로 보정했는지 여부
    excluded = Column(Boolean, default=False)  # 관리자가 데이터 품질상 제외 처리했는지 여부

    # {"질문 헤더 원문": "답변 원문", ...} 형태로 13개 문항 전체 저장
    raw_answers = Column(JSON, nullable=False)

    imported_at = Column(DateTime, default=now_utc)


class AIQuery(Base):
    __tablename__ = "ai_queries"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    used_context = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=now_utc)
