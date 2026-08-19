"""Pydantic 요청/응답 스키마"""
from typing import Optional
from pydantic import BaseModel


class ChatIn(BaseModel):
    question: str
    lang: Optional[str] = "ko"  # "ko" | "ja" - AI 답변 언어 (UI에서 선택한 언어를 따라감)
    category: Optional[str] = None  # 선택된 카테고리 키 (예: "music"). 없으면 전체 문항 대상


class SettingsIn(BaseModel):
    csv_url: str


class ResponseOverrideIn(BaseModel):
    nationality: Optional[str] = None  # "KR" | "JP" | "UNKNOWN"
    excluded: Optional[bool] = None
