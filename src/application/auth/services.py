"""
Contratos (interfaces) para serviços técnicos usados pelos casos de uso de auth.

Esses serviços encapsulam detalhes técnicos como bibliotecas de hash e JWT.
As implementações concretas ficam em infrastructure/.
"""
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


class PasswordHasher(Protocol):
    """Contrato para qualquer implementação de hash de senha."""

    def hash(self, password: str) -> str:
        """Gera o hash de uma senha em texto puro."""
        ...

    def verify(self, password: str, hashed: str) -> bool:
        """Verifica se uma senha em texto puro corresponde a um hash."""
        ...


@dataclass(frozen=True)
class AccessToken:
    """Resultado da emissão de um access token."""
    value: str  # o JWT em si (string)
    expires_in_seconds: int  # quanto tempo até expirar (pra setar Max-Age do cookie)


@dataclass(frozen=True)
class RefreshTokenPair:
    """Resultado da emissão de um refresh token.

    Contém o token em texto puro (pra ir pro cookie) e o hash (pra salvar no banco).
    O texto puro só existe nesse momento e nunca mais.
    """
    plain_value: str
    token_hash: str
    expires_in_seconds: int


class TokenService(Protocol):
    """Contrato para geração e validação de tokens (JWT + refresh)."""

    def issue_access_token(self, user_id: UUID) -> AccessToken:
        """Gera um novo access token JWT para o usuário."""
        ...

    def decode_access_token(self, token: str) -> UUID:
        """
        Decodifica um access token e retorna o user_id (sub).

        Lança:
            TokenExpired: se o token está expirado.
            InvalidToken: se o token é malformado, assinatura inválida, ou tipo errado.
        """
        ...

    def issue_refresh_token(self, user_id: UUID) -> RefreshTokenPair:
        """Gera um novo refresh token. Retorna texto puro + hash + expiração."""
        ...

    def hash_refresh_token(self, plain_value: str) -> str:
        """
        Gera o hash de um refresh token em texto puro.

        Usado quando recebemos um refresh token do cookie e precisamos
        buscar pelo hash no banco.
        """
        ...