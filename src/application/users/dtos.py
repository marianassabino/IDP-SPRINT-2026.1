"""DTOs para os casos de uso de usuário."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class UserView:
    """Representação 'pública' de um usuário (sem hash de senha)."""
    id: UUID
    email: str


@dataclass(frozen=True)
class ChangePasswordCommand:
    """Dados de entrada para troca de senha."""
    user_id: UUID
    current_password: str
    new_password: str