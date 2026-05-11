"""Implementação de RefreshTokenRepository em memória."""
import asyncio
from datetime import datetime, timezone
from uuid import UUID

from domain.auth.entities import RefreshToken
from domain.auth.repositories import RefreshTokenRepository


class InMemoryRefreshTokenRepository(RefreshTokenRepository):
    """Refresh tokens em memória, para testes."""

    def __init__(self) -> None:
        # chave = token_hash (string), valor = RefreshToken
        self._by_hash: dict[str, RefreshToken] = {}
        self._lock = asyncio.Lock()

    async def save(self, refresh_token: RefreshToken) -> None:
        async with self._lock:
            self._by_hash[refresh_token.token_hash] = refresh_token

    async def find_by_hash(self, token_hash: str) -> RefreshToken | None:
        async with self._lock:
            return self._by_hash.get(token_hash)

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        now = datetime.now(timezone.utc)
        async with self._lock:
            for token in self._by_hash.values():
                if token.user_id == user_id and not token.is_revoked():
                    token.revoked_at = now