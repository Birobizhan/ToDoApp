from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from shemas import UserCreate, UserResponse, ToDoCreate
from models import User, ToDo
from passlib.context import CryptContext
from security import get_current_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter(prefix="/auth", tags=["tasks"])


@router.post('/register/', response_model=UserResponse)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    existing_user = await db.execute(select(User).filter((User.username == user.username) | (User.email == user.email)))
    if existing_user.scalars().first():
        raise HTTPException(400, 'Пользователь с таким именем или почтой уже существует!')
    hashed_password = pwd_context.hash(user.password)

    new_user = User(username=user.username,
                    email=user.email,
                    hash_password=hashed_password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.post("/login/", response_model=dict)
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.username == form_data.username))
    user = result.scalars().first()

    if not user or not pwd_context.verify(form_data.password, user.hash_password):
        raise HTTPException(
            status_code=401,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }