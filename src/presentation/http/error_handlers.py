"""
Conversão centralizada de exceções de domínio/aplicação para HTTPException.

Mantém as rotas limpas e garante consistência:
qualquer rota que lance EmailAlreadyExists vira sempre o mesmo 409.
"""
from fastapi import HTTPException, status

from domain.auth.exceptions import (
    AuthDomainError,
    InvalidCredentials,
    InvalidToken,
    RefreshTokenExpired,
    RefreshTokenNotFound,
    RefreshTokenRevoked,
    TokenExpired,
)
from domain.users.exceptions import (
    EmailAlreadyExists,
    SamePassword,
    UserDomainError,
    UserNotFound,
    WeakPassword,
)


def domain_error_to_http(exc: Exception) -> HTTPException:
    """
    Converte qualquer exceção de domínio/aplicação para HTTPException.

    Mantém mensagem genérica em casos sensíveis (credenciais inválidas,
    refresh token inválido) por motivos de segurança.
    """
    # --- Erros de credenciais e tokens (sempre 401 com mensagem genérica) ---
    if isinstance(exc, InvalidCredentials):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
        )

    if isinstance(exc, (InvalidToken, TokenExpired,
                        RefreshTokenNotFound, RefreshTokenRevoked,
                        RefreshTokenExpired)):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
        )

    # --- Erros de usuário ---
    if isinstance(exc, EmailAlreadyExists):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered.",
        )

    if isinstance(exc, UserNotFound):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if isinstance(exc, (WeakPassword, SamePassword)):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    # --- Catch-all para outras exceções de domínio ---
    if isinstance(exc, (AuthDomainError, UserDomainError)):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    # Re-raise se não souber tratar (vira 500)
    raise exc