from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Normalizador JusBrasil"
    app_env: str = "development"
    app_version: str = "0.1.0"

    # JWT
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    cookie_secure: bool = False
    cookie_samesite: str = "lax"

    #CORS -> origens permitidas
    cors_allowed_origins: list[str] = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    ]
    # Postgres
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/normalizador"

    # AWS S3
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_s3_bucket_name: str = ""
    aws_s3_region: str = "us-east-1"
    aws_s3_endpoint_url: str = ""  # deixar vazio para usar AWS real

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
