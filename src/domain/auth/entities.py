"""
Entidade RefreshToken do domínio.

Representa um refresh token persistido. NÃO contém o token em texto puro,
apenas seu hash (o token puro só existe no momento da criação, é enviado
ao cliente via cookie e nunca mais é armazenado).
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass
class RefreshToken:
    """
    Um refresh token persistido no sistema.

    Atributos:
        id: identificador único do registro.
        user_id: a quem pertence.
        token_hash: hash do token (nunca o token puro).
        expires_at: quando vence (UTC).
        revoked_at: se foi revogado (None = ativo).
        created_at: quando foi criado.
    """
    user_id: UUID
    token_hash: str
    expires_at: datetime
    id: UUID = field(default_factory=uuid4)
    revoked_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_revoked(self) -> bool:
        """Token foi revogado manualmente?"""
        return self.revoked_at is not None

    def is_expired(self) -> bool:
        """Token passou da data de expiração?"""
        return datetime.now(timezone.utc) >= self.expires_at

    def is_active(self) -> bool:
        """Token pode ser usado para renovar sessão?"""
        return not self.is_revoked() and not self.is_expired()

    def revoke(self) -> None:
        """Marca o token como revogado agora."""
        if self.revoked_at is None:
            self.revoked_at = datetime.now(timezone.utc)