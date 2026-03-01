import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'bitrans_migration.db'}"
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:6001",
    ]
    PORT: int = 8000

    class Config:
        env_file = ".env"


settings = Settings()

# Railway sets CORS_ORIGINS as comma-separated string in env
raw_cors = os.environ.get("CORS_ORIGINS")
if raw_cors and "," in raw_cors:
    settings.CORS_ORIGINS = [o.strip() for o in raw_cors.split(",")]

settings.UPLOAD_DIR.mkdir(exist_ok=True)
