"""Configurações da aplicação, lidas de variáveis de ambiente."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configurações lidas do .env e/ou de variáveis de ambiente.

    Como usar:
        settings = Settings()
        print(settings.jwt_secret_key)
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # ignora variáveis no .env que não estão definidas aqui
    )

    # App
    app_name: str = "Normalizador JusBrasil"
    app_env: str = "development"
    app_version: str = "0.1.0"

    # JWT
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # Cookies
    cookie_secure: bool = False  # True em produção (HTTPS)
    cookie_samesite: str = "lax"