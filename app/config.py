import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'bitrans_migration.db'}"
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001,http://localhost:6001,https://gotrafficusa.com,https://www.gotrafficusa.com"
    PORT: int = 8000

    class Config:
        env_file = ".env"

    def get_cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()

settings.UPLOAD_DIR.mkdir(exist_ok=True)
