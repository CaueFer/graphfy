from fastapi import APIRouter, HTTPException, status
from tortoise.exceptions import DoesNotExist, IntegrityError
from passlib.context import CryptContext

from lib.helpers.jwt_helper import create_token
from db.schemas import LoginRequest, SignupRequest
from db.models.user_model import User, User_Pydantic

authRouter = APIRouter()

# Configs do passlib
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@authRouter.post("/login")
async def login_user(request: LoginRequest):
    try:
        user = await User.get(email=request.email)

        if not pwd_context.verify(request.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou senha inválidas",
            )

        access_token = create_token(data={"sub": user.email})

        return {"message": "Login bem-sucedido", "token": access_token}

    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nenhum usuário encontrado.",
        )


@authRouter.post("/signup")
async def signup_user(request: SignupRequest):
    try:   
        existing_user = await User.filter(email=request.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já registrado"
            )

        username = request.username
        email = request.email
        password = request.password

        hashPassword = pwd_context.hash(password)

        queryTortoise = await User.create(username=username, email=email, password=hashPassword)

        newUser = await User_Pydantic.from_tortoise_orm(queryTortoise)

        return {"message": "Usuário Criado com Sucesso", "user": { "id":newUser.id, "email":newUser.email }}
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já registrado"
        )
 