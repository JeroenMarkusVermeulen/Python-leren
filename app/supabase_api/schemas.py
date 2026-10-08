"""Auth-invoer en antwoorden; passwords worden nooit naar de client teruggestuurd."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, field_validator


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: SecretStr = Field(min_length=12, max_length=128)

    @field_validator("password")
    @classmethod
    def reject_blank_password(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().strip():
            raise ValueError("Kies een wachtwoord dat niet alleen uit spaties bestaat.")
        return value


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: SecretStr = Field(min_length=1, max_length=4096)


class RegistrationResult(BaseModel):
    message: str
    confirmation_required: bool
    session: Token | None = None


class AuthUser(BaseModel):
    id: UUID
    email: str | None = None
