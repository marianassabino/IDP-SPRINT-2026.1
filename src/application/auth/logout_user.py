"""Caso de uso: logout."""
from domain.auth.repositories import RefreshTokenRepository

from application.auth.dtos import LogoutUserCommand
from application.auth.services import TokenService


class LogoutUserUseCase:
    """
    Encerra a sessão do usuário.

    Fluxo:
      1. Se há refresh token no cookie, tenta revogá-lo.
      2. Se não há ou não é encontrado, ignora (logout deve ser idempotente).

    Não levanta erro se o token já estiver revogado/expirado/inexistente.
    Logout sempre "funciona" do ponto de vista do cliente — a limpeza dos
    cookies acontece na camada HTTP independentemente.
    """

    def __init__(
        self,
        refresh_token_repo: RefreshTokenRepository,
        token_service: TokenService,
    ) -> None:
        self._refresh_token_repo = refresh_token_repo
        self._tokens = token_service

    async def execute(self, command: LogoutUserCommand) -> None:
        if not command.refresh_token:
            return

        token_hash = self._tokens.hash_refresh_token(command.refresh_token)
        stored = await self._refresh_token_repo.find_by_hash(token_hash)

        if stored is None or stored.is_revoked():
            # Já não havia sessão válida. Não há nada pra fazer.
            return

        stored.revoke()
        await self._refresh_token_repo.save(stored)