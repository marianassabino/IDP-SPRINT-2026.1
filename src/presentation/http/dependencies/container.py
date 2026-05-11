"""Container de dependências (Composition Root) que instancia e injeta implementações concretas nos casos de uso."""
from functools import lru_cache

from application.auth import (
    LoginUserUseCase,
    LogoutUserUseCase,
    RefreshSessionUseCase,
    RegisterUserUseCase,
)
from application.auth.services import PasswordHasher, TokenService
from application.users import ChangePasswordUseCase, GetCurrentUserUseCase
from domain.auth.repositories import RefreshTokenRepository
from domain.users.repositories import UserRepository
from infrastructure.auth import Argon2PasswordHasher, JwtTokenService
from infrastructure.persistence import (
    InMemoryRefreshTokenRepository,
    InMemoryUserRepository,
)
from infrastructure.settings import Settings, get_settings as _get_settings_cached


def get_settings() -> Settings:
    """Configurações lidas do .env (reusa o singleton do infrastructure)."""
    return _get_settings_cached()


@lru_cache
def get_password_hasher() -> PasswordHasher:
    """Hasher singleton (instanciar Argon2 a cada request é caro)."""
    return Argon2PasswordHasher()


@lru_cache
def get_token_service() -> TokenService:
    """Token service singleton, configurado a partir das settings."""
    settings = get_settings()
    return JwtTokenService(
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        access_token_expire_minutes=settings.access_token_expire_minutes,
        refresh_token_expire_days=settings.refresh_token_expire_days,
    )


@lru_cache
def get_user_repository() -> UserRepository:
    """Repositório de usuários em memória; trocar pela implementação com banco quando disponível."""
    return InMemoryUserRepository()


@lru_cache
def get_refresh_token_repository() -> RefreshTokenRepository:
    """Repositório de refresh tokens em memória; trocar pela implementação com banco quando disponível."""
    return InMemoryRefreshTokenRepository()


def provide_register_user() -> RegisterUserUseCase:
    return RegisterUserUseCase(
        user_repo=get_user_repository(),
        refresh_token_repo=get_refresh_token_repository(),
        password_hasher=get_password_hasher(),
        token_service=get_token_service(),
    )


def provide_login_user() -> LoginUserUseCase:
    return LoginUserUseCase(
        user_repo=get_user_repository(),
        refresh_token_repo=get_refresh_token_repository(),
        password_hasher=get_password_hasher(),
        token_service=get_token_service(),
    )


def provide_refresh_session() -> RefreshSessionUseCase:
    return RefreshSessionUseCase(
        user_repo=get_user_repository(),
        refresh_token_repo=get_refresh_token_repository(),
        token_service=get_token_service(),
    )


def provide_logout_user() -> LogoutUserUseCase:
    return LogoutUserUseCase(
        refresh_token_repo=get_refresh_token_repository(),
        token_service=get_token_service(),
    )


def provide_get_current_user() -> GetCurrentUserUseCase:
    return GetCurrentUserUseCase(
        user_repo=get_user_repository(),
    )


def provide_change_password() -> ChangePasswordUseCase:
    return ChangePasswordUseCase(
        user_repo=get_user_repository(),
        refresh_token_repo=get_refresh_token_repository(),
        password_hasher=get_password_hasher(),
    )
