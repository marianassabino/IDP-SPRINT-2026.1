"""
Contrato (interface) para persistência de usuários.

Usa typing.Protocol para definir o que qualquer implementação precisa ter.
Quem implementa de fato fica em infrastructure (in-memory, SQLAlchemy, etc).
"""
from typing import Protocol
from uuid import UUID

from domain.users.entities import User


class UserRepository(Protocol):
    """
    Contrato para qualquer repositório de usuários.

    Qualquer classe que tenha esses métodos com essas assinaturas
    é automaticamente um UserRepository, sem precisar herdar nada.
    """

    async def save(self, user: User) -> None:
        """Cria ou atualiza um usuário."""
        ...

    async def find_by_id(self, user_id: UUID) -> User | None:
        """Busca um usuário pelo ID. Retorna None se não existir."""
        ...

    async def find_by_email(self, email: str) -> User | None:
        """Busca um usuário pelo email (case-insensitive). Retorna None se não existir."""
        ...

    async def exists_by_email(self, email: str) -> bool:
        """Verifica se já existe usuário com esse email."""
        ...