"""Caso de uso: renovar sessão usando refresh token (com rotação)."""
from datetime import datetime, timedelta, timezone

from domain.auth.entities import RefreshToken
from domain.auth.exceptions import (
    RefreshTokenExpired,
    RefreshTokenNotFound,
    RefreshTokenRevoked,
)
from domain.auth.repositories import RefreshTokenRepository
from domain.users.exceptions import UserNotFound
from domain.users.repositories import UserRepository

from application.auth.dtos import AuthenticatedSession, RefreshSessionCommand
from application.auth.services import TokenService


class RefreshSessionUseCase:
    """
    Renova a sessão usando o refresh token.

    Fluxo (com ROTAÇÃO):
      1. Hasheia o refresh token recebido (pra buscar no banco).
      2. Busca pelo hash. Se não existe -> RefreshTokenNotFound.
      3. Se revogado -> RefreshTokenRevoked.
      4. Se expirado -> RefreshTokenExpired.
      5. Busca o usuário (defensivo).
      6. Revoga o refresh token atual.
      7. Emite NOVO access + NOVO refresh token (rotação).
      8. Salva hash do novo refresh.
      9. Retorna AuthenticatedSession.

    Por que ROTAÇÃO? Cada uso do refresh gera um novo e invalida o velho.
    Se um refresh token vazar, ele só pode ser usado uma vez antes do legítimo
    ser invalidado. Quando o legítimo tentar usar, recebe erro e sabemos que
    houve comprometimento (em sistemas mais sofisticados, isso dispara alerta).
    """

    def __init__(
        self,
        user_repo: UserRepository,
        refresh_token_repo: RefreshTokenRepository,
        token_service: TokenService,
    ) -> None:
        self._user_repo = user_repo
        self._refresh_token_repo = refresh_token_repo
        self._tokens = token_service

    async def execute(self, command: RefreshSessionCommand) -> AuthenticatedSession:
        # 1. Hash do token recebido
        token_hash = self._tokens.hash_refresh_token(command.refresh_token)

        # 2. Busca pelo hash
        stored = await self._refresh_token_repo.find_by_hash(token_hash)
        if stored is None:
            raise RefreshTokenNotFound("Refresh token not found.")

        # 3. Revogado?
        if stored.is_revoked():
            raise RefreshTokenRevoked("Refresh token was revoked.")

        # 4. Expirado?
        if stored.is_expired():
            raise RefreshTokenExpired("Refresh token expired.")

        # 5. Usuário existe? (defesa contra estado inconsistente do banco)
        user = await self._user_repo.find_by_id(stored.user_id)
        if user is None:
            raise UserNotFound("User of refresh token not found.")

        # 6. Revoga o token atual
        stored.revoke()
        await self._refresh_token_repo.save(stored)

        # 7. Emite novos tokens
        access = self._tokens.issue_access_token(user.id)
        new_refresh = self._tokens.issue_refresh_token(user.id)

        # 8. Salva o novo refresh
        new_expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=new_refresh.expires_in_seconds
        )
        await self._refresh_token_repo.save(
            RefreshToken(
                user_id=user.id,
                token_hash=new_refresh.token_hash,
                expires_at=new_expires_at,
            )
        )

        # 9. Retorna
        return AuthenticatedSession(
            user_id=user.id,
            user_email=user.email,
            access_token=access.value,
            access_token_expires_in=access.expires_in_seconds,
            refresh_token=new_refresh.plain_value,
            refresh_token_expires_in=new_refresh.expires_in_seconds,
        )