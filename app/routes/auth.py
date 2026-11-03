from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verificar_password
from app.core.jwt import crear_access_token, crear_refresh_token, decodificar_token
from app.models.entities import Socio
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticación"])

class LoginSchema(BaseModel):
    email: str
    password: str

class RefreshSchema(BaseModel):
    refresh_token: str

@router.post("/login")
def login(credentials: LoginSchema, db: Session = Depends(get_db)):
    """Autentica a un socio y retorna los tokens de acceso y refresco."""
    socio = db.query(Socio).filter(Socio.email == credentials.email).first()

    if not socio or not verificar_password(credentials.password, socio.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas (email o contraseña inválidos)"
        )

    access_token = crear_access_token({"sub": str(socio.id), "rol": getattr(socio, "rol", "socio")})
    refresh_token = crear_refresh_token({"sub": str(socio.id)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh")
def refresh_access_token(body: RefreshSchema):
    """Genera un nuevo access token usando un refresh token válido."""
    payload = decodificar_token(body.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tipo de token inválido (se esperaba refresh token)"
        )

    user_id = payload.get("sub")
    new_access_token = crear_access_token({"sub": user_id})

    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }