from environs import Env
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException, status, Cookie, Request
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import User
from sqlalchemy.future import select
from jwt import PyJWTError, ExpiredSignatureError

env = Env()
env.read_env()
SECRET_KEY = env('SECRET_KEY')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
        request: Request,
        access_token: str | None = Cookie(None, alias="access_token"),
        db: AsyncSession = Depends(get_db)
):
    if not access_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            access_token = auth_header.split("Bearer ")[1]

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Необходима аутентификация",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token = access_token.replace("Bearer ", "") if access_token.startswith("Bearer") else access_token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")

        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный фортокен токена",
            )

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Срок действия токена истек",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен аутентификации",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await db.execute(select(User).filter(User.username == username))
    user = user.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    return user
