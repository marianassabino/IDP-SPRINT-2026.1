"""
Entidade user de domínio
Representa um usuário do sistema no nível regra de negócio.
Não conhece bancho, FastAPI, JWT, hash ou detalhes técnicos
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

@dataclass
class User:
    """
    Atributos:
    id: identificador único (UUID)
    email: email normalizado em lowercase
    password_hash: hash da senha
    created_at: quando foi criado (UTC)
    updated_at: última atualização (UTC)

    """
    email: str
    password_hash: str
    name: str
    last_name: str
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        self.email = self.email.strip().lower()

    def change_password(self, new_password_hash: str) -> None:
        self.password_hash = new_password_hash
        self.updated_at = datetime.now(timezone.utc)
        