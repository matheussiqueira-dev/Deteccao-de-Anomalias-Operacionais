from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_password_hash,
    decode_access_token,
    verify_password,
)
from app.schemas import TokenRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

settings = get_settings()
_admin_password_hash = create_password_hash(settings.admin_password)


@router.post("/login", response_model=TokenResponse)
def login(payload: TokenRequest) -> TokenResponse:
    if payload.username != settings.admin_username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not verify_password(payload.password, _admin_password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(subject=payload.username)
    return TokenResponse(access_token=token)


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = decode_access_token(token)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc
    subject = payload.get("sub")
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return str(subject)
