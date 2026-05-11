"""Caso de uso: trocar a senha do usuário autenticado."""
from domain.auth.repositories import RefreshTokenRepository
from domain.users.exceptions import (
    SamePassword,
    UserNotFound,
    WeakPassword,
)
from domain.users.repositories import UserRepository
from domain.auth.exceptions import InvalidCredentials

from application.auth.services import PasswordHasher
from application.users.dtos import ChangePasswordCommand

MIN_PASSWORD_LENGTH = 8


class ChangePasswordUseCase:
    """
    Troca a senha do usuário autenticado.

    Fluxo:
      1. Busca o usuário (deve existir, JWT já foi validado antes).
      2. Verifica a senha atual.
      3. Verifica que a nova senha respeita regra mínima.
      4. Verifica que nova senha != atual.
      5. Gera hash da nova senha.
      6. Atualiza a entidade User.
      7. REVOGA todos os refresh tokens ativos do usuário (segurança).
      8. Salva.

    Observação: revogar todos os refresh tokens força re-login em todos
    os dispositivos. Isso protege contra cenário em que algum refresh token
    antigo tenha vazado.
    """

    def __init__(
        self,
        user_repo: UserRepository,
        refresh_token_repo: RefreshTokenRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        self._user_repo = user_repo
        self._refresh_token_repo = refresh_token_repo
        self._hasher = password_hasher

    async def execute(self, command: ChangePasswordCommand) -> None:
        # 1. Busca usuário
        user = await self._user_repo.find_by_id(command.user_id)
        if user is None:
            raise UserNotFound("User not found.")

        # 2. Senha atual
        if not self._hasher.verify(command.current_password, user.password_hash):
            raise InvalidCredentials("Current password is incorrect.")

        # 3. Nova senha forte
        if len(command.new_password) < MIN_PASSWORD_LENGTH:
            raise WeakPassword(
                f"New password must be at least {MIN_PASSWORD_LENGTH} characters."
            )

        # 4. Não pode ser igual à atual
        if self._hasher.verify(command.new_password, user.password_hash):
            raise SamePassword("New password must be different from the current one.")

        # 5 + 6. Aplica nova senha
        new_hash = self._hasher.hash(command.new_password)
        user.change_password(new_hash)
        await self._user_repo.save(user)

        # 7. Revoga refresh tokens (força re-login)
        await self._refresh_token_repo.revoke_all_for_user(user.id)