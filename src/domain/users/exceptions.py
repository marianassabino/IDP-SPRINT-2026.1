"""
Exceções do domínio de usuários.

São lançadas pelos casos de uso quando regras de negócio são violadas.
A camada de apresentação (FastAPI) captura e converte para HTTP status code.
"""


class UserDomainError(Exception):
    """Classe base para todas as exceções do domínio de usuários."""


class EmailAlreadyExists(UserDomainError):
    """Lançada quando se tenta criar usuário com email já cadastrado."""


class UserNotFound(UserDomainError):
    """Lançada quando um usuário esperado não é encontrado."""


class WeakPassword(UserDomainError):
    """Lançada quando a senha não atende aos requisitos mínimos."""


class SamePassword(UserDomainError):
    """Lançada quando a nova senha é igual à senha atual."""