"""Rotas HTTP de usuário."""
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from application.users import (
    ChangePasswordCommand,
    ChangePasswordUseCase,
    GetCurrentUserUseCase,
)
from presentation.http.cookies import clear_auth_cookies
from presentation.http.dependencies.auth import get_current_user_id
from presentation.http.dependencies.container import (
    provide_change_password,
    provide_get_current_user,
)
from presentation.http.error_handlers import domain_error_to_http
from presentation.http.schemas import (
    ChangePasswordRequest,
    ChangePasswordResponse,
    UserResponse,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user",
)
async def get_me(
    current_user_id: UUID = Depends(get_current_user_id),
    use_case: GetCurrentUserUseCase = Depends(provide_get_current_user),
) -> UserResponse:
    """Retorna dados do usuário autenticado (via cookie access_token)."""
    try:
        user = await use_case.execute(current_user_id)
    except Exception as exc:
        raise domain_error_to_http(exc)

    return UserResponse(id=str(user.id), email=user.email)


@router.patch(
    "/me/password",
    response_model=ChangePasswordResponse,
    status_code=status.HTTP_200_OK,
    summary="Change current user password",
)
async def change_password(
    payload: ChangePasswordRequest,
    response: Response,
    current_user_id: UUID = Depends(get_current_user_id),
    use_case: ChangePasswordUseCase = Depends(provide_change_password),
) -> ChangePasswordResponse:
    """Altera a senha do usuário autenticado, revoga os refresh tokens e limpa os cookies forçando re-login."""
    try:
        await use_case.execute(
            ChangePasswordCommand(
                user_id=current_user_id,
                current_password=payload.current_password,
                new_password=payload.new_password,
            )
        )
    except Exception as exc:
        raise domain_error_to_http(exc)

    clear_auth_cookies(response)

    return ChangePasswordResponse(password_updated=True)
