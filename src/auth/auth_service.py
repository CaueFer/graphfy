from fastapi import HTTPException, status
from passlib.context import CryptContext

from lib.helpers.jwt_helper import create_token
from db.models.user_model import User, User_Pydantic

# Configs do passlib
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def login_service(email: str, password: str) -> str:
    user = await User.get(email=email)

    if not pwd_context.verify(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidas",
        )

    access_token = create_token(data={"sub": user.email})

    return access_token


async def signup_service(username: str, email: str, password: str):
    existing_user = await User.filter(email=email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Este email já está em uso!"
        )

    hashPassword = pwd_context.hash(password)

    queryTortoise = await User.create(
        username=username, email=email, password=hashPassword
    )

    newUser = await User_Pydantic.from_tortoise_orm(queryTortoise)

    return newUser
