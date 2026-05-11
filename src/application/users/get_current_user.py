"""Caso de uso: obter o usuário atualmente autenticado."""
from uuid import UUID

from domain.users.exceptions import UserNotFound
from domain.users.repositories import UserRepository

from application.users.dtos import UserView


class GetCurrentUserUseCase:
    """
    Retorna os dados do usuário autenticado.

    A autenticação em si (validar o JWT) é feita pela camada de presentation,
    que extrai o user_id do token e passa pra cá. Esse caso de uso só busca
    o usuário no repositório.
    """

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def execute(self, user_id: UUID) -> UserView:
        user = await self._user_repo.find_by_id(user_id)
        if user is None:
            # Estado inconsistente: o JWT é válido mas o usuário foi deletado.
            raise UserNotFound("User not found.")

        return UserView(id=user.id, email=user.email)