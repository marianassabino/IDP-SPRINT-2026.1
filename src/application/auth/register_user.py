"""Caso de uso: registrar um novo usuário."""
from domain.auth.repositories import RefreshTokenRepository
from domain.users.entities import User
from domain.users.exceptions import EmailAlreadyExists, WeakPassword
from domain.users.repositories import UserRepository

from application.auth.dtos import AuthenticatedSession, RegisterUserCommand
from application.auth.services import PasswordHasher, TokenService

# Regra mínima de senha (poderia ficar em config, mas pra MVP fica explícito aqui)
MIN_PASSWORD_LENGTH = 8


class RegisterUserUseCase:
    """
    Registra um novo usuário e já abre sessão (define cookies de auth).

    Fluxo:
      1. Verifica se email já existe (case-insensitive porque User normaliza no domain).
      2. Verifica que a senha atende ao tamanho mínimo.
      3. Gera hash da senha.
      4. Cria a entidade User e persiste.
      5. Emite access token + refresh token.
      6. Persiste o hash do refresh token.
      7. Retorna AuthenticatedSession.
    """

    def __init__(
        self,
        user_repo: UserRepository,
        refresh_token_repo: RefreshTokenRepository,
        password_hasher: PasswordHasher,
        token_service: TokenService,
    ) -> None:
        self._user_repo = user_repo
        self._refresh_token_repo = refresh_token_repo
        self._hasher = password_hasher
        self._tokens = token_service

    async def execute(self, command: RegisterUserCommand) -> AuthenticatedSession:
        # 1. Email único
        if await self._user_repo.exists_by_email(command.email):
            raise EmailAlreadyExists(f"Email already registered.")

        # 2. Senha mínima
        if len(command.password) < MIN_PASSWORD_LENGTH:
            raise WeakPassword(
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
            )

        # 3. Hash
        password_hash = self._hasher.hash(command.password)

        # 4. Cria e salva usuário
        user = User(email=command.email, password_hash=password_hash)
        await self._user_repo.save(user)

        # 5. Emite tokens
        access = self._tokens.issue_access_token(user.id)
        refresh_pair = self._tokens.issue_refresh_token(user.id)

        # 6. Salva hash do refresh token
        from datetime import datetime, timedelta, timezone
        from domain.auth.entities import RefreshToken
        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=refresh_pair.expires_in_seconds
        )
        await self._refresh_token_repo.save(
            RefreshToken(
                user_id=user.id,
                token_hash=refresh_pair.token_hash,
                expires_at=expires_at,
            )
        )

        # 7. Retorna o resultado
        return AuthenticatedSession(
            user_id=user.id,
            user_email=user.email,
            access_token=access.value,
            access_token_expires_in=access.expires_in_seconds,
            refresh_token=refresh_pair.plain_value,
            refresh_token_expires_in=refresh_pair.expires_in_seconds,
        )