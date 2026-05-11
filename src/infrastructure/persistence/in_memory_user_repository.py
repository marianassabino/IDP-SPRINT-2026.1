"""Implementação de UserRepository em memória, para testes."""
import asyncio
from uuid import UUID

from domain.users.entities import User
from domain.users.repositories import UserRepository


class InMemoryUserRepository(UserRepository):
    """
    Guarda usuários num dicionário em memória.

    Útil para testes e para desenvolvimento enquanto a implementação
    de banco (SQLAlchemy) não está pronta. NÃO usar em produção.
    """

    def __init__(self) -> None:
        self._by_id: dict[UUID, User] = {}
        self._lock = asyncio.Lock()

    async def save(self, user: User) -> None:
        async with self._lock:
            self._by_id[user.id] = user

    async def find_by_id(self, user_id: UUID) -> User | None:
        async with self._lock:
            return self._by_id.get(user_id)

    async def find_by_email(self, email: str) -> User | None:
        # Normaliza igual ao domain
        normalized = email.strip().lower()
        async with self._lock:
            for user in self._by_id.values():
                if user.email == normalized:
                    return user
        return None

    async def exists_by_email(self, email: str) -> bool:
        return await self.find_by_email(email) is not None