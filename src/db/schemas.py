from pydantic import BaseModel, EmailStr, Field

class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Endereço de email do usuário")
    password: str = Field(..., min_length=1, description="Senha do usuário")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "sua_senha"
            }
        }

class SignupRequest(BaseModel):
    username: str = Field(..., description="Nome do usuário")
    email: EmailStr = Field(..., description="Endereço de email do usuário")
    password: str = Field(..., min_length=6, description="Senha do usuário (mínimo 6 caracteres)")

    class Config:
        json_schema_extra = {
            "example": {
                "username": "seu nome",
                "email": "user@example.com",
                "password": "sua_senha_segura"
            }
        }