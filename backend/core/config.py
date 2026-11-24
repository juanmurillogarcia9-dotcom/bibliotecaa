import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    database_url: str | None
    db_user: str
    db_password: str
    db_host: str
    db_port: int
    db_name: str
    port: int
    cors_origins: list[str]
    db_pool_min_size: int
    db_pool_max_size: int
    admin_email: str
    admin_password: str
    session_secret: str
    secure_cookie: bool


def get_settings() -> Settings:
    database_url = os.getenv("DATABASE_URL") or None
    cors_origins = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
        if origin.strip()
    ]
    return Settings(
        database_url=database_url,
        db_user=os.getenv("DB_USER", "postgres"),
        db_password=os.getenv("DB_PASSWORD", ""),
        db_host=os.getenv("DB_HOST", "localhost"),
        db_port=int(os.getenv("DB_PORT", "5432")),
        db_name=os.getenv("DB_NAME", "biblioteca13"),
        port=int(os.getenv("PORT", "8000")),
        cors_origins=cors_origins,
        db_pool_min_size=int(os.getenv("DB_POOL_MIN_SIZE", "1")),
        db_pool_max_size=int(os.getenv("DB_POOL_MAX_SIZE", "10")),
        admin_email=os.getenv("ADMIN_EMAIL", "").strip(),
        admin_password=os.getenv("ADMIN_PASSWORD", ""),
        session_secret=os.getenv("SESSION_SECRET", ""),
        secure_cookie=os.getenv("COOKIE_SECURE", "false").strip().lower()
        in {"1", "true", "yes", "on"},
    )
