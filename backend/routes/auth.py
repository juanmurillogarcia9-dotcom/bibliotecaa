import hmac
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from backend.core.auth import (
    SESSION_COOKIE,
    SESSION_MAX_AGE,
    create_session_token,
    verify_session_token,
)
from backend.core.config import Settings, get_settings
from backend.schemas.auth import LoginRequest

router = APIRouter(prefix="/auth", tags=["Autenticación"])
SettingsDependency = Annotated[Settings, Depends(get_settings)]


@router.post("/login")
async def login(
    payload: LoginRequest, response: Response, settings: SettingsDependency
) -> dict[str, str]:
    email_matches = hmac.compare_digest(
        payload.email.strip().casefold().encode("utf-8"),
        settings.admin_email.casefold().encode("utf-8"),
    )
    password_matches = hmac.compare_digest(
        payload.password.encode("utf-8"),
        settings.admin_password.encode("utf-8"),
    )
    if not (email_matches and password_matches):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos.",
        )

    response.set_cookie(
        key=SESSION_COOKIE,
        value=create_session_token(settings.admin_email, settings.session_secret),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=settings.secure_cookie,
        samesite="lax",
        path="/",
    )
    return {"email": settings.admin_email}


@router.get("/session")
async def get_session(request: Request) -> dict[str, str]:
    settings = get_settings()
    if not verify_session_token(
        request.cookies.get(SESSION_COOKIE),
        settings.session_secret,
        settings.admin_email,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inicia sesión para continuar.",
        )
    return {"email": settings.admin_email}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE,
        httponly=True,
        samesite="lax",
        secure=get_settings().secure_cookie,
        path="/",
    )
