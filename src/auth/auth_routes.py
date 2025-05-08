from fastapi import APIRouter, HTTPException, status
from tortoise.exceptions import DoesNotExist, IntegrityError

from auth.auth_service import login_service, signup_service
from db.schemas import LoginRequest, SignupRequest

authRouter = APIRouter()

@authRouter.post("/login")
async def login_user(request: LoginRequest):
    try:
        token = await login_service(email=request.email, password=request.password)

        return {"message": "Login bem-sucedido", "token": token}

    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nenhum usuário encontrado.",
        )


@authRouter.post("/signup")
async def signup_user(request: SignupRequest):
    try:   
        newUser = await signup_service(username=request.username, email=request.email, password=request.password)

        return {"message": "Usuário Criado com Sucesso", "user": { "id":newUser.id, "email":newUser.email }}
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já registrado"
        )
 