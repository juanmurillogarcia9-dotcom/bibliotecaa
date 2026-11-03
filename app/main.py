from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from .core.config import get_settings
from .core.exceptions import ErrorAplicacion
from .routes import autores, categorias, libros, prestamos, reportes, socios, auth

settings = get_settings()

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Usamos Alembic para las migraciones, dejamos el lifespan limpio
    yield


app = FastAPI(
    title="API de Biblioteca",
    description="Gestión integral de biblioteca con PostgreSQL y FastAPI",
    version="3.0",
    lifespan=lifespan,
)


@app.get("/api/v1/health", tags=["Salud"])
def health_check() -> dict[str, str]:
    """Endpoint de salud para verificar que la API y la configuración funcionan."""
    return {"status": "ok", "environment": settings.environment}


@app.get("/", tags=["Inicio"])
def raiz() -> dict[str, str]:
    """Página de entrada con enlaces a la documentación y al resumen."""
    return {
        "mensaje": "API de Biblioteca en funcionamiento",
        "documentacion": "/docs",
        "openapi": "/openapi.json",
        "resumen": "/api/v1/reportes/resumen",
    }


@app.exception_handler(ErrorAplicacion)
async def manejar_error_aplicacion(
    _: Request, error: ErrorAplicacion
) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={"detail": error.mensaje},
    )


@app.exception_handler(IntegrityError)
async def manejar_error_integridad(
    _: Request, error: IntegrityError
) -> JSONResponse:
    """Traduce violaciones de restricciones a 409 en lugar de un 500."""
    return JSONResponse(
        status_code=409,
        content={
            "detail": (
                "La operación entra en conflicto con datos existentes "
                "(valor duplicado o referencia inválida)"
            )
        },
    )


# Incluimos los routers de la aplicación
app.include_router(autores.router, prefix="/api/v1")
app.include_router(categorias.router, prefix="/api/v1")
app.include_router(libros.router, prefix="/api/v1")
app.include_router(socios.router, prefix="/api/v1")
app.include_router(prestamos.router, prefix="/api/v1")
app.include_router(reportes.router, prefix="/api/v1")
app.include_router(auth.router)  # auth.py ya incluye el prefijo /api/v1/auth