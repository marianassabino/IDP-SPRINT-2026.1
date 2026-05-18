"""
Schemas Pydantic para os endpoints de autenticação.

Esses schemas definem o formato JSON de entrada e saída das rotas HTTP.
São diferentes dos DTOs da application: estes conhecem HTTP, JSON, email, etc.
"""
from pydantic import BaseModel, EmailStr, Field


# ---------------- REQUEST SCHEMAS ----------------

class RegisterRequest(BaseModel):
    """Corpo da requisição POST /auth/register."""
    name: str = Field(min_length=1, max_length=120)
    last_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    """Corpo da requisição POST /auth/login."""
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


# ---------------- RESPONSE SCHEMAS ----------------

class UserResponse(BaseModel):
    """
    Resposta com dados públicos do usuário.

    Usada por /auth/register, /auth/login e /users/me.
    NUNCA inclui password_hash.
    """
    id: str
    email: EmailStr
    name: str
    last_name: str


class AuthenticatedResponse(BaseModel):
    """Resposta de /auth/refresh."""
    authenticated: bool


class LogoutResponse(BaseModel):
    """Resposta de /auth/logout."""
    authenticated: bool