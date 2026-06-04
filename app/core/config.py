from __future__ import annotations
import json
import os
from typing import Any, Dict, List, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["dev", "prod", "test"]

CONFIG: Dict[str, Dict[str, Any]] = {
    "dev": {
        "DEBUG": True,
        "SECRET_KEY": "dev-secret-key-change-in-production",
        "DATABASE_URL": "postgresql://fastapi_user:fastapi_password@localhost:5432/fastapi_db",
        "REDIS_URL": "redis://localhost:6379/0",
        "CELERY_BROKER_URL": "amqp://guest:guest@localhost:5672//",
        "CELERY_RESULT_BACKEND_URL": "redis://localhost:6379/0",
        "CORS_ORIGINS": "http://localhost:3000,http://localhost:8000",
    },
    "prod": {
        "DEBUG": False,
        "SECRET_KEY": "",
        "DATABASE_URL": "",
        "REDIS_URL": "redis://redis:6379/0",
        "CELERY_BROKER_URL": "amqp://guest:guest@rabbitmq:5672//",
        "CELERY_RESULT_BACKEND_URL": "redis://redis:6379/0",
        "CORS_ORIGINS": "",
    },
    "test": {
        "DEBUG": True,
        "SECRET_KEY": "test-secret-key",
        "DATABASE_URL": "sqlite:///./test.db",
        "REDIS_URL": "redis://localhost:6379/1",
        "CELERY_BROKER_URL": "memory://",
        "CELERY_RESULT_BACKEND_URL": "cache+memory://",
        "CORS_ORIGINS": "*",
    },
}


def _env_block() -> Dict[str, Any]:
    env = os.getenv("ENVIRONMENT", "dev").lower()
    if env not in CONFIG:
        env = "dev"
    return CONFIG[env]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENVIRONMENT: Environment = "dev"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"

    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    DATABASE_URL: str = "postgresql://fastapi_user:fastapi_password@localhost:5432/fastapi_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "amqp://guest:guest@localhost:5672//"
    CELERY_RESULT_BACKEND_URL: str = "redis://localhost:6379/0"

    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    def __init__(self, **kwargs: Any) -> None:
        block = _env_block()
        merged: Dict[str, Any] = {}
        for key in (
            "DEBUG",
            "SECRET_KEY",
            "DATABASE_URL",
            "REDIS_URL",
            "CELERY_BROKER_URL",
            "CELERY_RESULT_BACKEND_URL",
            "CORS_ORIGINS",
        ):
            if key not in kwargs and key in block and block[key] not in ("", None):
                merged[key] = block[key]
        merged.update(kwargs)
        super().__init__(**merged)
        self._validate_production()

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> List[str]:
        if isinstance(value, list):
            return value
        if not value:
            return []
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("["):
                parsed = json.loads(stripped)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
            return [origin.strip() for origin in stripped.split(",") if origin.strip()]
        return value

    def _validate_production(self) -> None:
        if self.ENVIRONMENT != "prod":
            return
        if not self.SECRET_KEY or self.SECRET_KEY == CONFIG["dev"]["SECRET_KEY"]:
            raise ValueError("SECRET_KEY must be set to a strong value in production")
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL must be set in production")


settings = Settings(ENVIRONMENT=os.getenv("ENVIRONMENT", "dev"))  # type: ignore[arg-type]
