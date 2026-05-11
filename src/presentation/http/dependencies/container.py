from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from application.auth import (
    LoginUserUseCase,
    LogoutUserUseCase,
    RefreshSessionUseCase,
    RegisterUserUseCase,
)
from application.auth.services import PasswordHasher, TokenService
from application.users import ChangePasswordUseCase, GetCurrentUserUseCase
from infrastructure.auth import Argon2PasswordHasher, JwtTokenService
from infrastructure.persistence.database import get_db
from infrastructure.persistence.repositories.auth_repository import SqlAlchemyRefreshTokenRepository
from infrastructure.persistence.repositories.user_repository import SqlAlchemyUserRepository
from infrastructure.settings import Settings, get_settings as _get_settings_cached
from functools import lru_cache


def get_settings() -> Settings:
    return _get_settings_cached()


@lru_cache
def get_password_hasher() -> PasswordHasher:
    return Argon2PasswordHasher()


@lru_cache
def get_token_service() -> TokenService:
    settings = get_settings()
    return JwtTokenService(
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        access_token_expire_minutes=settings.access_token_expire_minutes,
        refresh_token_expire_days=settings.refresh_token_expire_days,
    )


def provide_register_user(db: AsyncSession = Depends(get_db)) -> RegisterUserUseCase:
    return RegisterUserUseCase(
        user_repo=SqlAlchemyUserRepository(db),
        refresh_token_repo=SqlAlchemyRefreshTokenRepository(db),
        password_hasher=get_password_hasher(),
        token_service=get_token_service(),
    )


def provide_login_user(db: AsyncSession = Depends(get_db)) -> LoginUserUseCase:
    return LoginUserUseCase(
        user_repo=SqlAlchemyUserRepository(db),
        refresh_token_repo=SqlAlchemyRefreshTokenRepository(db),
        password_hasher=get_password_hasher(),
        token_service=get_token_service(),
    )


def provide_refresh_session(db: AsyncSession = Depends(get_db)) -> RefreshSessionUseCase:
    return RefreshSessionUseCase(
        user_repo=SqlAlchemyUserRepository(db),
        refresh_token_repo=SqlAlchemyRefreshTokenRepository(db),
        token_service=get_token_service(),
    )


def provide_logout_user(db: AsyncSession = Depends(get_db)) -> LogoutUserUseCase:
    return LogoutUserUseCase(
        refresh_token_repo=SqlAlchemyRefreshTokenRepository(db),
        token_service=get_token_service(),
    )


def provide_get_current_user(db: AsyncSession = Depends(get_db)) -> GetCurrentUserUseCase:
    return GetCurrentUserUseCase(
        user_repo=SqlAlchemyUserRepository(db),
    )


def provide_change_password(db: AsyncSession = Depends(get_db)) -> ChangePasswordUseCase:
    return ChangePasswordUseCase(
        user_repo=SqlAlchemyUserRepository(db),
        refresh_token_repo=SqlAlchemyRefreshTokenRepository(db),
        password_hasher=get_password_hasher(),
    )
