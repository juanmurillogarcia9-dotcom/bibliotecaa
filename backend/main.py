import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from psycopg import Error as PsycopgError

from backend.core.auth import SESSION_COOKIE, verify_session_token
from backend.core.config import get_settings
from backend.core.database import lifespan_context
from backend.routes import auth, libros, prestamos, usuarios

logger = logging.getLogger(__name__)
settings = get_settings()
static_dir = Path(__file__).resolve().parent.parent / "frontend"

if not settings.admin_email or not settings.admin_password or not settings.session_secret:
    raise RuntimeError(
        "Configura ADMIN_EMAIL, ADMIN_PASSWORD y SESSION_SECRET en el archivo .env."
    )
if len(settings.admin_password) < 12:
    raise RuntimeError("ADMIN_PASSWORD debe tener al menos 12 caracteres.")
if len(settings.session_secret.encode("utf-8")) < 32:
    raise RuntimeError("SESSION_SECRET debe tener al menos 32 bytes.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with lifespan_context(app, settings):
        yield


app = FastAPI(
    title="biblioteca-13",
    description="API asíncrona para la gestión de libros, lectores y préstamos.",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def require_admin_session(request: Request, call_next):
    path = request.url.path
    if path.startswith("/api/") and path not in {
        "/api/auth/login",
        "/api/auth/logout",
        "/api/auth/session",
    }:
        valid_session = verify_session_token(
            request.cookies.get(SESSION_COOKIE),
            settings.session_secret,
            settings.admin_email,
        )
        if not valid_session:
            return JSONResponse(
                status_code=401,
                content={"detail": "Inicia sesión para continuar."},
            )
    return await call_next(request)


@app.exception_handler(PsycopgError)
async def handle_database_error(_, exc: PsycopgError) -> JSONResponse:
    if exc.sqlstate == "23505":
        status_code, detail = 409, "El recurso ya existe (ISBN o correo duplicado)."
    elif exc.sqlstate == "23503":
        status_code, detail = 409, "No se puede eliminar el recurso porque tiene préstamos asociados."
    elif exc.sqlstate == "23514":
        status_code, detail = 400, "La operación viola una restricción de datos."
    elif exc.sqlstate in {"23502", "22001", "22003"}:
        status_code, detail = 400, "Los datos enviados no cumplen los requisitos."
    else:
        logger.error(
            "Error de base de datos",
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        status_code, detail = 500, "Error interno de base de datos."
    return JSONResponse(status_code=status_code, content={"detail": detail})


app.include_router(auth.router, prefix="/api")
app.include_router(libros.router, prefix="/api")
app.include_router(usuarios.router, prefix="/api")
app.include_router(prestamos.router, prefix="/api")


@app.get("/", include_in_schema=False)
async def home() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/health", tags=["Sistema"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    config = uvicorn.Config(app, host="0.0.0.0", port=settings.port)
    server = uvicorn.Server(config)
    with asyncio.Runner(loop_factory=asyncio.SelectorEventLoop) as runner:
        runner.run(server.serve())
