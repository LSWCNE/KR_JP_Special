"""관리자 로그인: 비밀번호 확인 + 서명된 세션 쿠키 (별도 세션 저장소 없이 stdlib만 사용)"""
import hashlib
import hmac
import os
import time

from fastapi import HTTPException, Request

COOKIE_NAME = "admin_session"
SESSION_TTL_SECONDS = 60 * 60 * 8  # 8시간


def _secret() -> str | None:
    return os.getenv("ADMIN_SESSION_SECRET")


def check_password(password: str) -> bool:
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_password:
        return False
    return hmac.compare_digest(password, admin_password)


def create_session_token() -> str:
    secret = _secret()
    if not secret:
        raise RuntimeError(
            "ADMIN_SESSION_SECRET 환경변수가 설정되어 있지 않습니다. .env에 추가해주세요."
        )
    expires_at = int(time.time()) + SESSION_TTL_SECONDS
    payload = str(expires_at)
    sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


def verify_session_token(token: str | None) -> bool:
    secret = _secret()
    if not secret or not token or "." not in token:
        return False
    payload, sig = token.rsplit(".", 1)
    try:
        expires_at = int(payload)
    except ValueError:
        return False
    expected_sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected_sig):
        return False
    return time.time() < expires_at


def is_admin_request(request: Request) -> bool:
    return verify_session_token(request.cookies.get(COOKIE_NAME))


def require_admin_api(request: Request) -> None:
    if not is_admin_request(request):
        raise HTTPException(status_code=401, detail="관리자 인증이 필요합니다.")
