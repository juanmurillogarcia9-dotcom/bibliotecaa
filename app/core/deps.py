from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.jwt import decodificar_token
from app.models.entities import Socio  # O el nombre de la clase de socio que tengas en entities.py

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def obtener_usuario_actual(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Socio:
    """Valida el token JWT y extrae el usuario autenticado de la base de datos."""
    payload = decodificar_token(token)

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tipo de token inválido (se esperaba access token)"
        )

    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de autenticación inválidas"
        )

    usuario = db.query(Socio).filter(Socio.id == int(user_id)).first()
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    return usuario

def verificar_rol(rol_requerido: str):
    """Fábrica de dependencias para validar roles específicos."""
    def dependencia_rol(usuario_actual: Socio = Depends(obtener_usuario_actual)):
        if getattr(usuario_actual, "rol", None) != rol_requerido:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos suficientes para realizar esta acción"
            )
        return usuario_actual
    return dependencia_rol