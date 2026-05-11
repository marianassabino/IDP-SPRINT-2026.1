"""
Dependência FastAPI para extrair o usuário autenticado do cookie.

Uso nas rotas:

    @router.get("/users/me")
    async def get_me(current_user_id: UUID = Depends(get_current_user_id)):
        ...

Se o token estiver ausente, inválido ou expirado, FastAPI responde 401
automaticamente e a rota nem é chamada.
"""
from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, status

from application.auth.services import TokenService
from domain.auth.exceptions import InvalidToken, TokenExpired
from presentation.http.cookies import ACCESS_TOKEN_COOKIE
from presentation.http.dependencies.container import get_token_service


async def get_current_user_id(
    access_token: str | None = Cookie(default=None, alias=ACCESS_TOKEN_COOKIE),
    token_service: TokenService = Depends(get_token_service),
) -> UUID:
    """
    Extrai e valida o user_id a partir do cookie access_token.

    Lança 401 Unauthorized se:
      - O cookie não existe
      - O token é inválido (assinatura, formato, tipo errado)
      - O token está expirado
    """
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
        )

    try:
        return token_service.decode_access_token(access_token)
    except (InvalidToken, TokenExpired):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
        )